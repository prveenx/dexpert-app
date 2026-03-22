# FILE: /browser/tools/registry.py
import asyncio
import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Callable, Awaitable, Optional

from .browser.state import BrowserState
from core.scratchpad import WorkflowPhase

log = logging.getLogger(__name__)

# System downloads directory (human-like behavior)
_SYSTEM_DOWNLOADS = Path(os.path.expanduser('~/Downloads')).resolve()

# URL patterns considered invalid for navigation
_INVALID_URL_RE = re.compile(
    r'^$|^#|^javascript:|^mailto:|^tel:|^data:|0x0:0x0|^void\(',
    re.IGNORECASE
)

# Type alias for tool handler functions
ToolHandler = Callable[[Dict[str, Any], BrowserState, Any], Awaitable[str]]


class BrowserToolRegistry:
    """
    Central registry that routes tool_name -> handler.

    Initialised once per task with live controller references.
    The ``execute_batch`` method processes a list of actions
    sequentially and collects feedback - this is the core
    mechanism that allows the agent to do multiple actions per turn
    (e.g., fill a form: type username + type password + click submit).
    """

    def __init__(
        self,
        navigator: Any,
        interactor: Any,
        perception: Any,
        scratchpad: Any,
        manager: Any,
        emit_func: Callable[[str, str], Awaitable[None]],
        llm: Any,
        vision_llm: Any,
        prompts: Any,
    ):
        self.nav = navigator
        self.interact = interactor
        self.perception = perception
        self.scratchpad = scratchpad
        self.manager = manager
        self.emit = emit_func
        self.llm = llm
        self.vision_llm = vision_llm
        self.prompts = prompts

        # Build the dispatch table
        self._handlers: Dict[str, ToolHandler] = {
            # --- Navigation ---
            "go_to_url":    self._handle_navigate,
            "navigate":      self._handle_navigate, # Alias
            "google_search": self._handle_google_search,
            "go_back":      self._handle_go_back,
            "refresh":      self._handle_refresh,
            "switch_tab":   self._handle_switch_tab,
            "close_tab":    self._handle_close_tab,

            # --- Interaction ---
            "click_element": self._handle_click,
            "click":         self._handle_click,
            "input_text":    self._handle_input_text,
            "type":          self._handle_input_text,
            "select_option": self._handle_select_option,
            "hover":         self._handle_hover,
            "scroll":        self._handle_scroll,
            "scroll_down":   lambda p, s, c: self._handle_scroll({"direction": "down"}, s, c),
            "scroll_up":     lambda p, s, c: self._handle_scroll({"direction": "up"}, s, c),
            "scroll_to":     self._handle_scroll_to_element,
            "key_press":     self._handle_key_press,
            "press_key":     self._handle_key_press,
            "press_enter":   lambda p, s, c: self._handle_key_press({"key": "Enter"}, s, c),
            "wait":          self._handle_wait,
            "wait_for_download": self._handle_wait_for_download,
            "cancel_download":   self._handle_cancel_download,
            "upload_file":   self._handle_upload_file,
            "upload":        self._handle_upload_file,

            # --- Vision ---
            "analyze_visual": self._handle_analyze_visual,
            "vision":         self._handle_analyze_visual,

            # --- Scratchpad: Data ---
            "scratchpad_save":      self._handle_scratchpad_save,
            "scratchpad_read":      self._handle_scratchpad_read,

            # --- Scratchpad: Queue Management ---
            "scratchpad_enqueue":   self._handle_scratchpad_enqueue,
            "scratchpad_next":      self._handle_scratchpad_next,
            "scratchpad_complete":  self._handle_scratchpad_complete,
            "scratchpad_fail":      self._handle_scratchpad_fail,
            "scratchpad_skip":      self._handle_scratchpad_skip,

            # --- Scratchpad: Workflow Control ---
            "scratchpad_transition": self._handle_scratchpad_transition,
        }

        # Tracks an in-flight download to prevent duplicate clicks
        self._active_download_element: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        state: BrowserState,
    ) -> str:
        """Execute a single tool and return feedback."""
        handler = self._handlers.get(tool_name)
        if not handler:
            return f"Error: Unknown tool '{tool_name}'. Available: {list(self._handlers.keys())}"

        try:
            result = await handler(params, state, None)
            log.info(f"Tool '{tool_name}': {result[:120]}")
            return result
        except Exception as e:
            log.error(f"Tool '{tool_name}' crashed: {e}", exc_info=True)
            return f"Error: Tool '{tool_name}' failed with: {str(e)}"

    async def execute_batch(
        self,
        actions: List[Dict[str, Any]],
        state: BrowserState,
    ) -> List[str]:
        """
        Execute a list of actions sequentially.
        Each action dict must have ``tool_name`` and optionally ``parameters``.
        Returns a list of feedback strings (one per action).
        """
        feedback: List[str] =[]

        for i, action in enumerate(actions):
            tool_name = action.get("tool_name", "")
            params = action.get("parameters", action)  # fallback: flat dict

            # Remove tool_name from params to avoid passing it to handler
            if "tool_name" in params:
                params = {k: v for k, v in params.items() if k != "tool_name"}

            result = await self.execute(tool_name, params, state)
            feedback.append(f"[{i+1}] {tool_name}: {result}")

        return feedback

    # ------------------------------------------------------------------
    # Navigation Handlers
    # ------------------------------------------------------------------

    async def _handle_navigate(self, params: dict, state: BrowserState, ctx: Any) -> str:
        url = params.get("url", "")
        if not url:
            return "Error: 'url' parameter is required."
        # Clear loop history on navigation
        self.scratchpad.clear_loop_history()
        return await self.nav.navigate_to(url)

    async def _handle_google_search(self, params: dict, state: BrowserState, ctx: Any) -> str:
        query = params.get("query", "")
        if not query:
            return "Error: 'query' parameter is required."
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        self.scratchpad.clear_loop_history()
        return await self.nav.navigate_to(url)

    async def _handle_go_back(self, params: dict, state: BrowserState, ctx: Any) -> str:
        self.scratchpad.clear_loop_history()
        return await self.nav.go_back()

    async def _handle_refresh(self, params: dict, state: BrowserState, ctx: Any) -> str:
        return await self.nav.refresh()

    async def _handle_switch_tab(self, params: dict, state: BrowserState, ctx: Any) -> str:
        idx = params.get("tab_index", 0)
        return await self.nav.switch_tab(idx)

    async def _handle_close_tab(self, params: dict, state: BrowserState, ctx: Any) -> str:
        idx = params.get("tab_index", None)
        return await self.nav.close_tab(idx)

    # ------------------------------------------------------------------
    # Interaction Handlers
    # ------------------------------------------------------------------

    async def _handle_click(self, params: dict, state: BrowserState, ctx: Any) -> str:
        raw_id = params.get("target_id") or params.get("ax_id") or params.get("id", "")
        ax_id = self._parse_ax_id(str(raw_id))
        if ax_id is None:
            return "Error: Invalid target_id."

        node = state.get_node(ax_id)
        expect_download = params.get("expect_download", False)
        
        # Auto-detect download links (broader detection)
        if node:
            if "[DOWNLOAD]" in node.states or "download" in node.name.lower():
                expect_download = True
            # Also check href for common download patterns
            href = node.attributes.get("href", "").lower()
            if any(href.endswith(ext) for ext in ('.exe', '.msi', '.zip', '.dmg', '.deb', '.rpm', '.appx', '.msix')):
                expect_download = True
            # Check for download-related URL patterns
            if any(kw in href for kw in ('download', '/dl/', '/release')):
                expect_download = True

        # --- Unified Click Path ---
        # We always clear the download event before clicking so we can detect
        # if the click triggered a download (even unexpectedly).
        self.manager._download_event.clear()
        self.manager._last_captured_download = None

        target = await self.interact._resolve_locator(state, ax_id)
        if not target:
            # Fallback: try standard click via interactor
            return await self.interact.click_element(state, ax_id)

        try:
            try:
                await target.click(timeout=5_000)
            except Exception:
                await target.click(force=True, timeout=5_000)
        except Exception as e:
            return f"Error: Click on [ax-{ax_id}] failed: {str(e)[:150]}"

        # Check if the click triggered a download
        # Wait longer for expected downloads (15s), briefly for unexpected ones (3s)
        wait_timeout = 15.0 if expect_download else 3.0
        
        try:
            await asyncio.wait_for(self.manager._download_event.wait(), timeout=wait_timeout)
            task_state = self.manager._last_captured_download
        except asyncio.TimeoutError:
            task_state = None

        if task_state:
            task_id = task_state["id"]
            filename = task_state["filename"]
            return (
                f"DOWNLOAD_STARTED: '{filename}' is downloading to ~/Downloads. "
                f"Task ID: '{task_id}'. Control returned to you instantly. "
                f"To wait for completion, use: wait_for_download(task_id='{task_id}'). "
                f"If this is an application installer (.exe/.msi), after download completes, "
                f"report back to the Planner so it can delegate installation to the OS Agent."
            )
        
        # No download detected — handle navigation/popup that might have occurred
        if expect_download:
            return f"Success: Clicked[ax-{ax_id}]. (No download was detected — the click may have triggered a navigation. Check if a new tab opened or if the download starts with a delay.)"
        
        # Standard click result
        await self.interact._wait_for_potential_navigation()
        return f"Success: Clicked[ax-{ax_id}]."

    async def _handle_input_text(self, params: dict, state: BrowserState, ctx: Any) -> str:
        raw_id = params.get("target_id") or params.get("ax_id") or params.get("id", "")
        ax_id = self._parse_ax_id(str(raw_id))
        text = params.get("text", "") or params.get("value", "")
        if ax_id is None:
            return "Error: Invalid target_id."
        if not text:
            return "Error: 'text' parameter is required."

        result = await self.interact.input_text(
            state, ax_id, text,
            submit=params.get("submit", False)
        )

        return result

    async def _handle_select_option(self, params: dict, state: BrowserState, ctx: Any) -> str:
        ax_id = self._parse_ax_id(params.get("target_id", ""))
        value = params.get("value", "")
        if ax_id is None:
            return "Error: Invalid target_id."

        target = await self.interact._resolve_locator(state, ax_id)
        if not target:
            return f"Error: Element [ax-{ax_id}] not found."

        try:
            await target.select_option(label=value, timeout=3000)
            return f"Success: Selected '{value}' in dropdown [ax-{ax_id}]."
        except Exception as e:
            return f"Error: select_option failed: {e}"

    async def _handle_hover(self, params: dict, state: BrowserState, ctx: Any) -> str:
        ax_id = self._parse_ax_id(params.get("target_id", ""))
        if ax_id is None:
            return "Error: Invalid target_id."
        return await self.interact.hover(state, ax_id)

    async def _handle_scroll(self, params: dict, state: BrowserState, ctx: Any) -> str:
        direction = params.get("direction", "down")
        amount = params.get("amount", 800)

        # Check if we are scrolling a specific container
        raw_id = params.get("target_id") or params.get("ax_id") or params.get("id")
        target_id = self._parse_ax_id(str(raw_id)) if raw_id else None

        return await self.interact.scroll(direction, amount, target_id=target_id)

    async def _handle_scroll_to_element(self, params: dict, state: BrowserState, ctx: Any) -> str:
        raw_id = params.get("target_id") or params.get("ax_id") or params.get("id", "")
        ax_id = self._parse_ax_id(str(raw_id))
        if ax_id is None:
            return "Error: Invalid target_id for scroll_to."
        return await self.interact.scroll_to_element(state, ax_id)

    async def _handle_key_press(self, params: dict, state: BrowserState, ctx: Any) -> str:
        key = params.get("key", "")
        if not key:
            return "Error: 'key' parameter is required."
        try:
            page = self.nav.page
            await page.keyboard.press(key)
            return f"Success: Pressed key '{key}'."
        except Exception as e:
            return f"Error: key_press failed: {e}"

    async def _handle_wait(self, params: dict, state: BrowserState, ctx: Any) -> str:
        seconds = params.get("seconds", 2.0)
        await asyncio.sleep(min(seconds, 30.0))  # Cap at 30s (downloads can take time)
        return f"Success: Waited {seconds}s."

    # 🚀 TRUE POLLER: Suspends agent execution until download is 100% complete
    async def _handle_wait_for_download(self, params: dict, state: BrowserState, ctx: Any) -> str:
        """
        Unlike the `wait` tool which just sleeps for a fixed duration,
        this tool POLLS the download tracking system continuously
        and ONLY returns once the download is fully complete or failed.
        
        Accepts either the UUID task_id OR the filename.
        """
        raw_id = params.get("task_id", "")
        timeout = float(params.get("timeout", 600.0))
        
        if not raw_id:
            return "Error: task_id parameter is required (accepts task UUID or filename)."

        # Resolve: accepts both UUID task_id and filename
        task_id = self.manager._resolve_task_id(raw_id)
        
        if not task_id:
            # Give context handler a moment to register
            for _ in range(5):
                await asyncio.sleep(1.0)
                task_id = self.manager._resolve_task_id(raw_id)
                if task_id:
                    break
        
        if not task_id:
            return (
                f"Error: No download found matching '{raw_id}'. "
                f"Active downloads: {[d['filename'] for d in self.manager.active_downloads.values()]}. "
                f"Completed: {[d['filename'] for d in self.manager.completed_downloads]}."
            )

        start_wait = time.time()

        # ── TRUE POLLING LOOP ──
        while True:
            elapsed = time.time() - start_wait
            if elapsed > timeout:
                return f"Error: wait_for_download timed out after {timeout}s. Download may still be running in the background."

            # Check completed list
            for d in self.manager.completed_downloads:
                if d["id"] == task_id:
                    await self.emit("STATUS", "READY")
                    if d["status"] == "completed":
                        final = d['final_path']
                        is_installer = any(final.lower().endswith(ext) for ext in (
                            '.exe', '.msi', '.msix', '.appx', '.appxbundle'
                        ))
                        msg = f"DOWNLOAD_COMPLETED: {d['filename']} successfully downloaded to absolute_path={final}."
                        if is_installer:
                            msg += (
                                " This is an application installer. "
                                "Report back to the Planner so it can delegate the installation to the OS Agent."
                            )
                        else:
                            msg += " You may now use or reference this file."
                        return msg
                    else:
                        return f"DOWNLOAD_FAILED: {d.get('filename','?')}. Error: {d.get('error','unknown')}"

            # 🚀 Check if still actively downloading → emit live progress with ETA
            if task_id in self.manager.active_downloads:
                dl_state = self.manager.active_downloads[task_id]
                mb = dl_state.get('downloaded_mb', 0.0)
                tot = dl_state.get('total_mb', 0.0)
                spd = dl_state.get('speed_mb_s', 0.0)
                eta = dl_state.get('eta_seconds', -1)
                fn = dl_state['filename'][:20]
                
                pct_str = f"{int(dl_state.get('percent', 0))}% " if tot > 0 else ""
                eta_str = f" | ETA: {eta}s" if eta >= 0 else ""

                await self.emit("STATUS", f"\u2b07 DL: {fn}... | {pct_str}({mb:.1f}MB) @ {spd:.1f}MB/s{eta_str}")
            else:
                # Not active AND not completed — check filesystem as safety net
                for d in list(self.manager.completed_downloads) + list(self.manager.active_downloads.values()):
                    if d.get("id") == task_id and d.get("final_path"):
                        p = Path(d["final_path"])
                        if p.exists() and p.stat().st_size > 0:
                            await self.emit("STATUS", "READY")
                            return f"DOWNLOAD_COMPLETED: {p.name} found at absolute_path={p}."
                
                if elapsed > 10:
                    return (
                        f"Error: Download '{raw_id}' tracking lost. "
                        f"Check ~/Downloads folder manually for the file."
                    )

            await asyncio.sleep(1.5)  # Poll interval
        
    async def _handle_cancel_download(self, params: dict, state: BrowserState, ctx: Any) -> str:
        raw_id = params.get("task_id")
        if not raw_id:
            return "Error: task_id parameter is required for cancel_download."
        
        success = await self.manager.cancel_download(raw_id)
        if success:
            return f"OK: Download '{raw_id}' was cancelled."
        else:
            return f"Error: Failed to cancel download '{raw_id}'. It may have already finished or the ID is invalid."

    async def _handle_upload_file(self, params: dict, state: BrowserState, ctx: Any) -> str:
        raw_id = params.get("target_id") or params.get("ax_id") or params.get("id", "")
        file_path = params.get("file_path", "")
        ax_id = self._parse_ax_id(str(raw_id))
        if ax_id is None:
            return "Error: Invalid target_id. Use format 'ax-42' or just '42'."
        if not file_path:
            return "Error: 'file_path' parameter is required. Ask Planner for the path if you don't know it."

        return await self.interact.upload_file(state, ax_id, file_path)

    # ... (Rest of tools omitted for brevity, they remain identical to original) ...
    # Following the prompt instructions, I will include the full file anyway to prevent fragmentation.

    # ------------------------------------------------------------------
    # Vision Handler
    # ------------------------------------------------------------------

    async def _handle_analyze_visual(self, params: dict, state: BrowserState, ctx: Any) -> str:
        """
        On-demand Vision LLM analysis.
        1. Take/crop screenshot based on target_id or focus_box.
        2. Send to Vision LLM with the user's query.
        3. Return the LLM's response as feedback.
        """
        query = params.get("query", "Describe what you see.")
        target_id = params.get("target_id")
        focus_box = params.get("focus_box")

        page = self.nav.page
        screenshot_b64 = None

        if target_id:
            ax_id = self._parse_ax_id(target_id)
            if ax_id is not None:
                screenshot_b64 = await self.perception.capture_element_screenshot(
                    page, state, ax_id
                )

        if not screenshot_b64 and focus_box and len(focus_box) == 4:
            from .browser.state import BoundingBox
            bbox = BoundingBox(
                x=focus_box[0], y=focus_box[1],
                width=focus_box[2], height=focus_box[3],
            )
            full_ss = await self.perception.capture_screenshot(page)
            if full_ss:
                screenshot_b64 = self.perception.crop_to_bbox(
                    full_ss, bbox, state.viewport_size
                )

        if not screenshot_b64:
            screenshot_b64 = await self.perception.capture_screenshot(page)

        if not screenshot_b64:
            return "Error: Could not capture screenshot for visual analysis."

        # Send to Vision LLM
        try:
            response = await self.vision_llm.generate_with_image(
                system=self.prompts.vision_system_prompt,
                prompt=query,
                image_base64=screenshot_b64,
            )
            return f"Visual Analysis: {response.strip()}"
        except Exception as e:
            return f"Error: Vision LLM failed: {e}"

    # ------------------------------------------------------------------
    # Scratchpad: Data Handlers
    # ------------------------------------------------------------------

    async def _handle_scratchpad_save(self, params: dict, state: BrowserState, ctx: Any) -> str:
        data = params.get("data", {})
        note = params.get("note")
        target_id_raw = params.get("target_id")

        if target_id_raw:
            ax_id = self._parse_ax_id(target_id_raw)
            if ax_id:
                node = state.get_node(ax_id)
                if node and node.attributes.get("_implicit_image_url"):
                    if "image_url" not in data:
                        data["image_url"] = node.attributes["_implicit_image_url"]
                        log.info(f"Auto-injected image for[ax-{ax_id}]")

        if data:
            self.scratchpad.save_data(data)
        if note:
            self.scratchpad.log(note)

        target_info = ""
        if self.scratchpad.target_count:
            target_info = f" (target: {self.scratchpad.target_count})"
        return f"OK: Saved to scratchpad. Total items: {len(self.scratchpad.collected_data)}{target_info}"

    async def _handle_scratchpad_read(self, params: dict, state: BrowserState, ctx: Any) -> str:
        summary = self.scratchpad.progress_summary()
        if params.get("include_data", False):
            summary += "\n\n--- COLLECTED DATA ---\n"
            summary += self.scratchpad.get_collected_summary()
        return summary

    # ------------------------------------------------------------------
    # Scratchpad: Queue Management Handlers
    # ------------------------------------------------------------------

    async def _handle_scratchpad_enqueue(self, params: dict, state: BrowserState, ctx: Any) -> str:
        items = params.get("items", [])
        urls = params.get("urls",[])

        if urls and not items:
            items = [{"url": u, "title": ""} for u in urls]

        if not items:
            return "Error: 'items' list is required."

        if not self.scratchpad.source_url:
            current_url = state.url if state else None
            if current_url and current_url != "about:blank":
                self.scratchpad.source_url = current_url

        for item in items:
            source_id = item.get("source_id") or item.get("ax_id")
            if source_id:
                ax_id = self._parse_ax_id(str(source_id))
                if ax_id is not None:
                    node = state.get_node(ax_id)
                    if node:
                        real_href = node.attributes.get("href", "")
                        if not real_href or _INVALID_URL_RE.search(real_href):
                            real_href = self._find_nearby_href(state, ax_id)

                        if real_href and not _INVALID_URL_RE.search(real_href):
                            if not item.get("url") or _INVALID_URL_RE.search(item.get("url", "")):
                                item["url"] = real_href
                                log.info(f"href resolved for [ax-{ax_id}]: {real_href[:60]}")

                        if node.attributes.get("_implicit_image_url"):
                            item["thumbnail_url"] = node.attributes["_implicit_image_url"]
                        if not item.get("title") and node.name:
                            item["title"] = node.name.strip()[:80]

            url = item.get("url", "")
            if url and _INVALID_URL_RE.search(url):
                log.warning(f"Wiped invalid URL: {url[:80]}")
                item["url"] = ""

        added = self.scratchpad.enqueue_items(items)

        queue_info = self.scratchpad.get_queue_status()
        target_info = ""
        if self.scratchpad.target_count:
            remaining = self.scratchpad.target_count - queue_info["total"]
            if remaining > 0:
                target_info = f" SYSTEM WARNING: You still need {remaining} more items to reach your target of {self.scratchpad.target_count}. DO NOT use scratchpad_next yet. Scroll the page and enqueue more items!"
            else:
                target_info = f" Target reached! You may now use scratchpad_transition(phase='process')."

        return f"OK: Enqueued {added} items. Queue: {queue_info['total']} total.{target_info}"

    async def _handle_scratchpad_next(self, params: dict, state: BrowserState, ctx: Any) -> str:
        if self.scratchpad.phase == WorkflowPhase.GATHER:
            log.info("Agent called next() during GATHER. Auto-transitioning to PROCESS.")
            self.scratchpad.transition_to(WorkflowPhase.PROCESS)

        item = self.scratchpad.next()
        if not item:
            done = self.scratchpad.done_count
            total = len(self.scratchpad.queue)
            return f"QUEUE_EXHAUSTED: All {total} items processed ({done} done). Transition to REPORT phase."

        response = f"NEXT_ITEM: #{item.id}"
        if item.title:
            response += f" | Title: {item.title}"

        if item.url and "0x0:0x0" not in item.url:
            response += f" | URL: {item.url}"
            response += " | ACTION: Use go_to_url to navigate to this URL."
        else:
            source_url = self.scratchpad.source_url
            response += " | NO_URL: No direct URL available."
            if source_url:
                response += f" | ACTION: Navigate back to the search results ({source_url}), find '{item.title}' in the list, and CLICK on it to open its detail page."
            else:
                response += f" | ACTION: Go back to the search results page and CLICK on '{item.title}' to open its detail page."

        if item.data:
            preview = str(item.data)[:100]
            response += f" | Metadata: {preview}"

        remaining = self.scratchpad.pending_count
        total = len(self.scratchpad.queue)
        response += f" | Progress: {self.scratchpad.done_count}/{total} done, {remaining} remaining"

        return response

    async def _handle_scratchpad_complete(self, params: dict, state: BrowserState, ctx: Any) -> str:
        data = params.get("data", {})
        self.scratchpad.complete_current(data)

        done = self.scratchpad.done_count
        total = len(self.scratchpad.queue)
        pending = self.scratchpad.pending_count

        result = f"OK: Item marked DONE. Progress: {done}/{total}"

        if pending > 0:
            result += f" | {pending} remaining. Use scratchpad_next to continue."
        else:
            result += " | All items processed! Transition to REPORT phase."

        if self.scratchpad.has_met_target:
            result += f" | Target of {self.scratchpad.target_count} items collected."

        return result

    async def _handle_scratchpad_fail(self, params: dict, state: BrowserState, ctx: Any) -> str:
        error = params.get("error", "Unknown error")
        self.scratchpad.fail_current(error)
        return f"OK: Item marked FAILED ({error}). Use scratchpad_next to continue with remaining items."

    async def _handle_scratchpad_skip(self, params: dict, state: BrowserState, ctx: Any) -> str:
        self.scratchpad.skip_current()
        return "OK: Item skipped. Use scratchpad_next to continue."

    # ------------------------------------------------------------------
    # Scratchpad: Workflow Control
    # ------------------------------------------------------------------

    async def _handle_scratchpad_transition(self, params: dict, state: BrowserState, ctx: Any) -> str:
        target_phase = params.get("phase", "").lower().strip()

        phase_map = {
            "gather": WorkflowPhase.GATHER,
            "process": WorkflowPhase.PROCESS,
            "report": WorkflowPhase.REPORT,
            "idle": WorkflowPhase.IDLE,
        }

        if target_phase not in phase_map:
            return f"Error: Invalid phase '{target_phase}'. Must be one of: {list(phase_map.keys())}"

        result = self.scratchpad.transition_to(phase_map[target_phase])

        if target_phase == "process":
            result += " | Now use scratchpad_next to get the first item, navigate to it, extract data, then scratchpad_complete."
        elif target_phase == "report":
            result += f" | {len(self.scratchpad.collected_data)} items collected. Compile results and deliver to user."

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_ax_id(raw: str) -> Optional[int]:
        if not raw:
            return None
        cleaned = str(raw).replace("ax-", "").replace("ax", "").strip()
        try:
            return int(cleaned)
        except ValueError:
            return None

    def _find_nearby_href(self, state: BrowserState, ax_id: int, radius: int = 8) -> str:
        for node in state.interactive_nodes:
            if abs(node.ax_id - ax_id) > radius:
                continue
            href = node.attributes.get("href", "")
            if href and not _INVALID_URL_RE.search(href):
                log.debug(f"Deep-href: [ax-{node.ax_id}] near [ax-{ax_id}] → {href[:60]}")
                return href
        return ""