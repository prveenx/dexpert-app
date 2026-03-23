import logging
import asyncio
from typing import List, Optional, Dict, Union

from playwright.async_api import Page, BrowserContext, Frame
from ..state import BrowserState

log = logging.getLogger(__name__)

# JS injected into the browser to show a visual tab/context indicator
_TAB_INDICATOR_JS = """
(() => {
    // Remove previous indicator if present
    const old = document.getElementById('__pcagent_tab_indicator');
    if (old) old.remove();

    const bar = document.createElement('div');
    bar.id = '__pcagent_tab_indicator';
    bar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #00e5ff, #7c4dff, #ff4081);
        z-index: 2147483647;
        pointer-events: none;
        box-shadow: 0 0 12px rgba(0,229,255,0.6);
        animation: __pcagent_pulse 2s ease-in-out infinite;
    `;

    // Add pulse animation
    if (!document.getElementById('__pcagent_tab_style')) {
        const style = document.createElement('style');
        style.id = '__pcagent_tab_style';
        style.textContent = `
            @keyframes __pcagent_pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(bar);
})();
"""

# JS to remove the tab indicator from non-active tabs
_TAB_INDICATOR_REMOVE_JS = """
(() => {
    const el = document.getElementById('__pcagent_tab_indicator');
    if (el) el.remove();
    const st = document.getElementById('__pcagent_tab_style');
    if (st) st.remove();
})();
"""

class NavigationController:
    """
    Handles state changes: URL navigation, History, Tabs, and Frames.
    Ensures the 'Execution Context' is correct before Interaction tools are used.

    Tab Reliability Guarantees:
    - `_active_page` is the SINGLE source of truth for which tab the agent is on.
    - When a new tab opens (e.g., target=_blank), the controller automatically switches
      to it AND waits for it to load before returning control.
    - A `_new_tab_event` dict is set whenever a new tab opens so the react loop can
      inject context about the tab switch into the LLM's next observation.
    - Visual indicator bars are injected into the active tab so a human observer can
      see exactly which tab the agent is operating on.
    """

    def __init__(self, context: BrowserContext):
        self.context = context
        self._active_page: Optional[Page] = None

        # Event flag: set by _on_page_created, consumed by the react loop
        self._new_tab_event: Optional[Dict[str, str]] = None
        # Track tab count before actions to detect new tabs
        self._tab_count_before_action: int = len(context.pages)

        # Automatically focus newly opened tabs (e.g., from target="_blank" links)
        self.context.on("page", self._on_page_created)

    async def _on_page_created(self, page: Page):
        """
        Fires when a new tab opens naturally (e.g., target=_blank click, window.open).
        Mimics human behavior: switch to the new tab AND wait for it to be ready.
        """
        old_page = self._active_page
        old_title = ""
        try:
            if old_page and not old_page.is_closed():
                old_title = await old_page.title()
        except Exception:
            pass

        self._active_page = page

        try:
            await page.bring_to_front()
        except Exception as e:
            log.debug(f"Failed to bring new page to front: {e}")

        # Wait for the new tab to reach a usable state
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            log.debug("New tab: domcontentloaded timeout, proceeding.")

        # Brief extra wait for JS hydration
        await asyncio.sleep(0.5)

        new_title = ""
        new_url = page.url
        try:
            new_title = await page.title()
        except Exception:
            pass

        # Record the event so the react loop can inform the LLM
        self._new_tab_event = {
            "from_tab_title": old_title,
            "new_tab_title": new_title,
            "new_tab_url": new_url,
            "new_tab_index": len(self.context.pages) - 1,
            "total_tabs": len(self.context.pages),
        }

        log.info(
            f"NEW TAB DETECTED: Switched to Tab {self._new_tab_event['new_tab_index']} "
            f"'{new_title}' ({new_url}). Total tabs: {self._new_tab_event['total_tabs']}"
        )

        # Inject visual indicator on the new active tab
        await self._inject_tab_indicator()

    def consume_new_tab_event(self) -> Optional[Dict[str, str]]:
        """
        Returns and clears the new-tab event.
        Called by the react loop after each action to detect tab changes.
        """
        event = self._new_tab_event
        self._new_tab_event = None
        return event

    def snapshot_tab_count(self):
        """Snapshot tab count before an action batch. Used to detect new tabs."""
        self._tab_count_before_action = len(self.context.pages)

    @property
    def page(self) -> Page:
        """Always returns the currently active page/tab."""
        if not self._active_page or self._active_page.is_closed():
            if self.context.pages:
                # Default to the most recently opened tab if active is closed
                self._active_page = self.context.pages[-1]
            else:
                raise RuntimeError("No pages open in browser context.")
        return self._active_page

    async def _inject_tab_indicator(self):
        """
        Injects a visual indicator bar on the active tab and removes it from all others.
        This makes it visually obvious which tab the agent is operating on.
        """
        for p in self.context.pages:
            if p.is_closed():
                continue
            try:
                if p == self._active_page:
                    await p.evaluate(_TAB_INDICATOR_JS)
                else:
                    await p.evaluate(_TAB_INDICATOR_REMOVE_JS)
            except Exception:
                pass  # Page might not be ready yet

    async def navigate_to(self, url: str) -> str:
        """Goes to a URL and waits for stability."""
        try:
            # Handle user laziness (google.com -> https://google.com)
            if not url.startswith("http"):
                url = "https://" + url

            log.info(f"Navigating to: {url}")
            # wait_until="load" is more reliable for SPAs like Gmail than "domcontentloaded"
            await self.page.goto(url, wait_until="load", timeout=45000)

            # Additional stability check for async content
            try:
                # Wait for at least 1s of network inactivity to catch hydration
                await self.page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                log.debug("Networkidle timeout reached during navigate_to, proceeding anyway.")

            title = await self.page.title()
            # Re-inject visual indicator after navigation
            await self._inject_tab_indicator()
            return f"Success: Loaded '{title}' at {url}"
        except Exception as e:
            return f"Error: Navigation failed: {str(e)}"

    async def refresh(self) -> str:
        try:
            await self.page.reload(wait_until="load")
            try:
                await self.page.wait_for_load_state("networkidle", timeout=3000)
            except: pass
            await self._inject_tab_indicator()
            return "Success: Page refreshed."
        except Exception as e:
            return f"Error: Refresh failed: {e}"

    async def go_back(self) -> str:
        try:
            await self.page.go_back(wait_until="load")
            try:
                await self.page.wait_for_load_state("networkidle", timeout=3000)
            except: pass
            await self._inject_tab_indicator()
            return "Success: Navigated back."
        except Exception as e:
            return f"Error: Could not go back: {e}"

    # --- TAB MANAGEMENT ---

    async def create_tab(self, url: Optional[str] = None) -> str:
        try:
            new_page = await self.context.new_page()
            self._active_page = new_page
            if url:
                await self.navigate_to(url)
            await self._inject_tab_indicator()
            return "Success: Opened and focused new tab."
        except Exception as e:
            return f"Error: Failed to open tab: {e}"

    async def switch_tab(self, tab_index: int) -> str:
        """
        Switches focus to a specific tab index.
        Also waits for the tab to be loaded and re-injects the visual indicator.
        """
        pages = self.context.pages
        if 0 <= tab_index < len(pages):
            target_page = pages[tab_index]

            if target_page.is_closed():
                return f"Error: Tab {tab_index} is closed."

            self._active_page = target_page
            await self._active_page.bring_to_front()

            # Wait briefly for the tab to be in a usable state
            try:
                await self._active_page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass

            title = await self._active_page.title()
            url = self._active_page.url
            total = len(pages)

            # Re-inject visual indicator
            await self._inject_tab_indicator()

            return (
                f"Success: Switched to Tab {tab_index} ('{title}' | {url}). "
                f"Total tabs: {total}. DOM data is now from this tab."
            )
        return f"Error: Tab index {tab_index} out of range (0-{len(pages)-1})."

    async def close_tab(self, tab_index: Optional[int] = None) -> str:
        """
        Closes a tab and provides detailed feedback about the new active state.
        """
        pages = self.context.pages
        target = self.page
        closed_title = ""

        if tab_index is not None:
            if 0 <= tab_index < len(pages):
                target = pages[tab_index]
            else:
                return f"Error: Tab index {tab_index} invalid (0-{len(pages)-1})."

        try:
            closed_title = await target.title()
        except Exception:
            pass

        await target.close()

        # Reset active page logic
        if not self.context.pages:
            self._active_page = await self.context.new_page()
            return f"Success: Closed tab '{closed_title}'. Opened empty tab to keep browser alive."

        # If we closed the active tab, switch to the last one
        if target == self._active_page or self._active_page.is_closed():
            self._active_page = self.context.pages[-1]
            await self._active_page.bring_to_front()
            try:
                await self._active_page.wait_for_load_state("domcontentloaded", timeout=3000)
            except Exception:
                pass

        new_title = ""
        try:
            new_title = await self._active_page.title()
        except Exception:
            pass

        new_url = self._active_page.url
        remaining = len(self.context.pages)

        # Re-inject visual indicator
        await self._inject_tab_indicator()

        return (
            f"Success: Closed tab '{closed_title}'. "
            f"Now on Tab '{new_title}' ({new_url}). "
            f"Remaining tabs: {remaining}. DOM data is now from this tab."
        )

    # --- FRAME MANAGEMENT ---

    async def switch_frame(self, frame_reference: str) -> Union[Frame, str]:
        """
        Attempts to locate a frame by name, url, or index.
        Note: This changes the 'active context' for InteractionController.
        """
        # Reset to main frame
        if frame_reference.lower() in ["main", "top", "parent"]:
            return self.page.main_frame

        # Try by name or URL
        frame = self.page.frame(name=frame_reference) or self.page.frame(url=frame_reference)

        if frame:
            return frame

        return f"Error: Frame '{frame_reference}' not found."

    async def get_tabs_info(self) -> List[Dict[str, str]]:
        """Returns metadata for all tabs to help the Agent decide navigation."""
        info = []
        active_page = self.page  # resolve once to avoid side effects
        for i, p in enumerate(self.context.pages):
            try:
                title = await p.title()
                info.append({
                    "index": i,
                    "title": title,
                    "url": p.url,
                    "active": (p == active_page)
                })
            except Exception:
                info.append({
                    "index": i,
                    "title": "(loading...)",
                    "url": "(unknown)",
                    "active": (p == active_page)
                })
        return info

    async def get_tab_context_string(self) -> str:
        """
        Builds a formatted string for the LLM prompt showing all open tabs
        with a clear visual marker for the active tab.
        """
        tabs = await self.get_tabs_info()
        if not tabs:
            return "OPEN TABS: None"

        lines = []
        for t in tabs:
            marker = " >>> ACTIVE (you are here)" if t["active"] else ""
            title_display = t['title'][:60] or '(no title)'
            url_display = t['url'][:80]
            lines.append(f"  Tab {t['index']}: \"{title_display}\" | {url_display}{marker}")

        return f"OPEN TABS ({len(tabs)} total):\n" + "\n".join(lines)