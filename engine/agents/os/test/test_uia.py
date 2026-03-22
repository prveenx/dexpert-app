import os
import sys
import asyncio
import re
import subprocess

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
sys.path.append(project_root)

from .os.perception.bridge import OSBridgeClient
from .os.controller.interaction import OSInteractionController

BRIDGE_PATH = os.path.join(project_root, "", "os", "perception", "rust_layer", "target", "release", "pcagent_bridge.exe")
DUMP_FILE = os.path.join(current_dir, "last_ui_tree.txt")

def draw_rainbow_overlay(elements_dict):
    """Creates a transparent fullscreen window to draw bounding boxes."""
    import tkinter as tk
    
    if not elements_dict:
        print("[!] No visual elements returned to draw.")
        return

    root = tk.Tk()
    root.attributes('-alpha', 1.0)
    root.attributes('-transparentcolor', 'SystemButtonFace')
    root.attributes('-topmost', True)
    root.overrideredirect(True)
    
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{sw}x{sh}+0+0")
    
    canvas = tk.Canvas(root, width=sw, height=sh, bg='SystemButtonFace', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Matching the PCAGENT_PROCESSOR (processor.js) color palette
    colors = ['#FF0000', '#00FF00', '#0000FF', '#FF00FF', '#00FFFF', '#FFA500', '#800080', '#FFFF00']
    
    drawn_count = 0
    for el in elements_dict.values():
        id_ = el['id']
        role = el['role']
        name = el.get('name', '')
        x, y, w, h = el['bbox']
        if w <= 0 or h <= 0: continue
        
        color = colors[id_ % len(colors)]
        
        # 🚀 THICK RAINBOW BORDERS (as requested, matching similar processor.js vibes)
        canvas.create_rectangle(x, y, x + w, y + h, outline=color, width=4)
        
        # Draw ID Tag (matching the look of the browser overlays)
        tag_text = f" {id_} "
        # Dynamic width for label based on ID length
        label_w = 20 if id_ < 10 else (30 if id_ < 100 else 40)
        
        canvas.create_rectangle(x, max(0, y - 16), x + label_w, y, fill=color, outline=color)
        canvas.create_text(x + 2, max(8, y - 8), text=tag_text, fill="white", font=("Segoe UI", 8, "bold"), anchor="w")
        
        drawn_count += 1

    print(f"[*] Visualizer active! Drew {drawn_count} elements on screen.")
    print("[*] Overlay will disappear automatically in 4 seconds...")
    root.after(4000, root.destroy)
    root.mainloop()

async def interactive_uia_tester():
    print("="*70)
    print(" 🖥️   PCAgent Windows UIA Tester (Enhanced Dexpert Engine) ")
    print("="*70)

    if not os.path.exists(BRIDGE_PATH):
        print(f"[!] FATAL: Rust bridge not found at {BRIDGE_PATH}")
        print("[!] Did you forget to run 'cargo build --release'?")
        return

    bridge = OSBridgeClient(BRIDGE_PATH)
    interact = OSInteractionController(bridge)

    try:
        while True:
            print("\n🔄 Fetching active windows...")
            raw_windows = await interact.list_windows()
            
            windows_list = []
            for line in raw_windows.strip().split('\n'):
                if not line.strip() or "No active windows" in line: continue
                match = re.search(r'\[ID:\s*(\d+)\]', line)
                if match:
                    windows_list.append({"handle": match.group(1), "display": line})

            print("\n--- ACTIVE WINDOWS ---")
            if not windows_list:
                print("  [No windows detected. Ensure bridge is compiled correctly.]")
            else:
                for idx, win in enumerate(windows_list):
                    print(f"[{idx}] {win['display']}")
            
            print("\n" + "-"*70)
            print("COMMANDS:")
            print("  [0-9] : Enter a number to focus, scan, and highlight that window.")
            print("  r     : Refresh the window list.")
            print("  l app : Test launch_app (e.g., 'l notepad' or 'l ms-settings:')")
            print("  q     : Quit")
            print("-"*70)
            
            user_input = input("\nAction: ").strip()
            cmd = user_input.lower()

            if cmd in ['q', 'quit', 'exit']: 
                break
            
            elif cmd == 'r':
                continue # Loops back and refreshes
                
            elif cmd.startswith('l '):
                query = user_input[2:].strip()
                print(f"[*] Testing launch_app with query: '{query}'")
                # Using the Python subprocess fallback we discussed
                try:
                    subprocess.Popen(f'start {query}', shell=True)
                    print(f"[+] Launched '{query}'. Type 'r' to refresh window list.")
                except Exception as e:
                    print(f"[!] Launch failed: {e}")
                await asyncio.sleep(2)
                continue

            elif user_input.isdigit():
                idx = int(user_input)
                if idx < 0 or idx >= len(windows_list):
                    print("[!] Invalid window number.")
                    continue

                selected_window = windows_list[idx]
                window_handle = selected_window["handle"]

                # 1. Bring to front
                print(f"[*] Focusing window HWND: {window_handle}...")
                await interact.focus_window(window_handle)
                await asyncio.sleep(1.0) 

                # 2. Python Semantic Scan
                print(f"[*] Scanning UI Tree...")
                tree_text = await interact.scan_focused_window(window_handle)

                # 3. Save full tree to file for manual LLM prompt design
                with open(DUMP_FILE, "w", encoding="utf-8") as f:
                    f.write(tree_text)
                
                print("\n" + "="*50)
                print(tree_text[:1000]) 
                if len(tree_text) > 1000: 
                    print(f"\n... [Tree truncated. Full tree saved to: {DUMP_FILE}] ...")
                print("="*50)
                print(f"[*] Interactive nodes assigned ID: {len(interact.active_elements)}")

                # 4. Draw Rainbow UI using Python cache
                draw_rainbow_overlay(interact.active_elements)
            else:
                print("[!] Unknown command.")

    finally:
        await bridge.stop()
        print("\n👋 Exited UIA Tester.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(interactive_uia_tester())