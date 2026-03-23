# FILE: /os/controller/interaction.py
import logging
import asyncio
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import pyautogui

log = logging.getLogger(__name__)

# Import the advanced processor we added previously
from ..perception.processor import SemanticProcessor, Printer

class OSInteractionController:
    """
    The 'Hands and Eyes' of the OS Agent.
    Cross-platform interaction using PyAutoGUI driven by Rust's semantic data.
    """
    def __init__(self, bridge_client):
        self.bridge = bridge_client
        self.active_elements = {} # Cache: ax_id -> {role, name, bbox}

    # ------------------------------------------------------------------
    # 1. MACRO PERCEPTION
    # ------------------------------------------------------------------

    async def list_windows(self) -> str:
        res = await self.bridge.request({"action": "list_windows"})
        if "error" in res: return f"Error: {res}"
        windows = res.get("windows", [])
        if not windows: return "No active windows found."
        
        import psutil
        output = []
        for w in windows:
            pid = w.get('process_id', 0)
            exe_name = "Unknown App"
            try:
                if pid:
                    exe_name = psutil.Process(pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            title = w.get('title', 'Unknown')
            
            # Contextualize for the LLM
            context_tag = exe_name
            if exe_name.lower() == "explorer.exe":
                context_tag = "File Explorer"
            elif exe_name.lower() == "applicationframehost.exe":
                context_tag = "Windows UWP App"
                
            output.append(f"[ID: {w.get('handle', 'Unknown')}] {title} ({context_tag} | {exe_name} - PID: {pid})")
            
        return "\n".join(output)

    async def focus_window(self, window_id: str) -> str:
        res = await self.bridge.request({"action": "focus_window", "window_id": str(window_id)})
        if "error" in res: return f"Error focusing window: {res}"
        return f"Success: Focused window '{res.get('title', window_id)}'."

    async def launch_app(self, query: str) -> str:
        """
        SOTA App Launcher.
        Replicates human "Start Menu Search" behavior to reliably launch 
        Core, Electron, and UWP/Store apps without needing exact paths.
        """
        try:
            if platform.system() == "Windows":
                return await self._launch_windows_app(query)
            elif platform.system() == "Darwin":
                # macOS native app launcher
                subprocess.Popen(['open', '-a', query])
                return f"Success: Instructed macOS to launch '{query}'."
            else:
                # Linux fallback
                subprocess.Popen(f'{query} &', shell=True)
                return f"Success: Instructed Linux to launch '{query}'."
        except Exception as e:
            return f"Error launching app '{query}': {e}. If it failed, try searching for the exact executable path using 'search_files'."

    async def _launch_windows_app(self, query: str) -> str:
        """Internal helper to intelligently hunt down and launch Windows apps."""
        query_clean = query.lower().strip()

        # PHASE 1: Try Direct Execution (PATH variables, cmd aliases, etc.)
        try:
            os.startfile(query_clean)
            return f"Success: Launched '{query}' directly via system path."
        except Exception:
            pass
        
        if not query_clean.endswith('.exe'):
            try:
                os.startfile(query_clean + ".exe")
                return f"Success: Launched '{query}.exe' directly via system path."
            except Exception:
                pass

        # PHASE 2: Start Menu Shortcut Search (Catches Electron apps: Discord, Slack, VSCode)
        appdata = os.environ.get('APPDATA', '')
        programdata = os.environ.get('PROGRAMDATA', '')
        
        search_dirs = [
            Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path(programdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        ]
        
        best_match = None
        for sdir in search_dirs:
            if not sdir.exists(): continue
            for root, _, files in os.walk(sdir):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        name = file[:-4].lower()
                        if query_clean == name: # Exact match
                            best_match = os.path.join(root, file)
                            break
                        elif query_clean in name: # Partial match
                            if not best_match:
                                best_match = os.path.join(root, file)
                # Break outer loops if exact match found
                if best_match and os.path.basename(best_match)[:-4].lower() == query_clean:
                    break

        if best_match:
            try:
                os.startfile(best_match)
                return f"Success: Launched '{os.path.basename(best_match)[:-4]}' via Start Menu shortcut."
            except Exception as e:
                log.error(f"Start Menu launch failed for {best_match}: {e}")

        # PHASE 3: Windows UWP / Store Apps (Catches WhatsApp, Netflix, modern Settings)
        try:
            # We use PowerShell to query the modern Appx/UWP database
            ps_cmd = f'Get-StartApps | Where-Object {{ $_.Name -match "{query}" }} | Select-Object -First 1 -ExpandProperty AppID'
            
            # Use CREATE_NO_WINDOW to prevent a black console box from flashing on screen
            CREATE_NO_WINDOW = 0x08000000 
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd], 
                capture_output=True, 
                text=True, 
                creationflags=CREATE_NO_WINDOW
            )
            
            app_id = result.stdout.strip()
            
            if app_id:
                # Launch UWP apps via Explorer's hidden AppsFolder shell protocol
                subprocess.Popen(f'explorer.exe shell:AppsFolder\\{app_id}', shell=True)
                return f"Success: Launched Microsoft Store App '{query}'."
        except Exception as e:
            log.error(f"UWP launch failed: {e}")

        return (
            f"Error: Could not find or launch app '{query}'. "
            f"Tried direct path, Start Menu shortcuts, and Microsoft Store apps. "
            f"Tip: Try using 'search_files' to locate its exact .exe path."
        )

    # ------------------------------------------------------------------
    # 2. MICRO PERCEPTION & INTERACTION
    # ------------------------------------------------------------------

    async def scan_focused_window(self, window_id: str = "") -> str:
        """
        Rust crawls the raw OS tree -> Python prunes and assigns IDs.
        Works across Windows, Mac, and Linux.
        """
        res = await self.bridge.request({"action": "scan_active", "window_id": str(window_id)})
        if "error" in res: return f"Error scanning screen: {res}"
        
        tree_json = res.get("semantic_tree")
        if not tree_json: return "Error: OS bridge returned empty tree."
        
        try:
            # 1. Clean & Prune (Cross-Platform)
            SemanticProcessor.process(tree_json)
            # 2. Sort Spatially & Assign LLM IDs
            printer = Printer()
            printer.process_tree(tree_json)
            
            # 3. Cache the ID -> BBox map for instant PyAutoGUI interactions
            self.active_elements = printer.elements_map
            
            return printer.get_output()
        except Exception as e:
            log.error(f"Semantic processing failed: {e}")
            return f"Error parsing tree: {e}"

    def _get_center_coords(self, ax_id: str) -> tuple[int, int]:
        """Helper to get center (x,y) from the Python cache."""
        ax_id_clean = int(str(ax_id).replace("ax-", ""))
        if ax_id_clean not in self.active_elements:
            raise ValueError(f"Element [ax-{ax_id_clean}] not found in last scan.")
            
        bbox = self.active_elements[ax_id_clean]["bbox"]
        x = bbox[0] + (bbox[2] // 2)
        y = bbox[1] + (bbox[3] // 2)
        return x, y

    async def click_element(self, ax_id: str, click_type: str = "left") -> str:
        try:
            x, y = self._get_center_coords(ax_id)
        except ValueError as e:
            return f"Error: {e}"

        pyautogui.moveTo(x, y, duration=0.1)
        if click_type == "double": pyautogui.doubleClick(x, y)
        elif click_type == "right": pyautogui.rightClick(x, y)
        else: pyautogui.leftClick(x, y)
            
        return f"Success: Clicked element [ax-{ax_id}]."

    async def input_text(self, ax_id: str, text: str, submit: bool = False) -> str:
        click_res = await self.click_element(ax_id)
        if "Error" in click_res: return click_res

        pyautogui.write(text, interval=0.01)
        if submit: pyautogui.press("enter")
        
        msg = f"Success: Typed text into [ax-{ax_id}]."
        if submit: msg += " (Submitted)"
        return msg

    async def press_key(self, key_combo: str) -> str:
        keys = key_combo.lower().split('+')
        if len(keys) > 1: pyautogui.hotkey(*keys)
        else: pyautogui.press(key_combo)
        return f"Success: Executed keystroke '{key_combo}'."

    async def scroll(self, direction: str, amount: int = 5, target_id: Optional[str] = None) -> str:
        if target_id:
            try:
                x, y = self._get_center_coords(target_id)
                pyautogui.moveTo(x, y, duration=0.1)
            except ValueError:
                pass # Fallback to current mouse position if ID fails
        
        sign = 1 if direction == "up" else -1
        pyautogui.scroll(sign * amount * 100)
        target = f"[ax-{target_id}]" if target_id else "active window"
        return f"Success: Scrolled {direction} on {target}."

    async def drag_and_drop(self, source_id: str, dest_id: str) -> str:
        try:
            sx, sy = self._get_center_coords(source_id)
            dx, dy = self._get_center_coords(dest_id)
        except ValueError as e:
            return f"Error resolving drag coordinates: {e}"
            
        pyautogui.moveTo(sx, sy, duration=0.1)
        pyautogui.dragTo(dx, dy, duration=0.5)
        return f"Success: Dragged [ax-{source_id}] to [ax-{dest_id}]."