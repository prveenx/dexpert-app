import logging
import asyncio
from typing import Optional, Union, Literal

from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
from ..state import BrowserState, DOMNode
from ..config.config import BrowserAgentSettings

log = logging.getLogger(__name__)

class InteractionController:
    """
    The 'Hands' of the Browser Agent.
    
    Responsibilities:
    1. Translation: Converts abstract 'ax_id' (from LLM) into concrete Playwright Locators.
    2. Visual Debugging: Highlights elements before interacting so humans can follow.
    3. Resilience: Handles scrolling, waiting, and detached elements automatically.
    """

    def __init__(self, navigator, config: Optional[BrowserAgentSettings] = None):
        self.navigator = navigator
        self.config = config

    @property
    def page(self) -> Page:
        return self.navigator.page

    async def _wait_for_potential_navigation(self, timeout: float = 5.0):
        """
        Smart wait after an action. If navigation starts, it waits for load.
        If no navigation starts within a short window, it proceeds.
        """
        try:
            # We wait for the 'load' state with a short timeout.
            # If navigation was triggered, this will catch it.
            # If it's a dynamic SPA update, 'load' will resolve quickly.
            await self.page.wait_for_load_state("load", timeout=timeout * 1000)
            
            # Optional: short sleep to allow JS to settle if it was just an AJAX update
            await asyncio.sleep(0.5)
            
            # If it's something heavy like Gmail, try networkidle briefly
            try:
                await self.page.wait_for_load_state("networkidle", timeout=2000)
            except:
                pass
        except Exception:
            # Timeout or error during wait... just proceed
            pass

    async def _resolve_locator(self, state: BrowserState, ax_id: int) -> Optional[Locator]:
        """
        Resolves a semantic ID to a physical DOM handle.
        Uses the unique data-pcagent-id attribute injected by our processor.
        """
        node = state.get_node(ax_id)
        if not node:
            log.warning(f"Interaction: Node [ax-{ax_id}] not found in current Perception State.")
            return None

        # Strategy 1: Unique Attribute (Most Robust - 100% match)
        # The processor adds [data-pcagent-id="ax-42"] to the element.
        selector = f'[data-pcagent-id="ax-{ax_id}"]'
        try:
            # We check if it exists in the live page
            locator = self.page.locator(selector)
            if await locator.count() > 0:
                return locator.first
        except Exception:
            pass

        # Strategy 2: Fallback to Cached Selector (Fast)
        if node.selector:
            try:
                locator = self.page.locator(node.selector)
                if await locator.count() > 0:
                    return locator.first
            except Exception:
                pass

        # Strategy 3: XPath (Fallback for complex text/hierarchy)
        if node.xpath:
            try:
                locator = self.page.locator(f"xpath={node.xpath}")
                if await locator.count() > 0:
                    return locator.first
            except Exception:
                pass

        log.error(f"Interaction: Could not resolve ANY locator for [ax-{ax_id}].")
        return None

    async def highlight(self, locator: Locator, color: str = "red"):
        """
        Visual Debugging: Flashes a border around the target.
        Critical for verifying that the AI is clicking what it *thinks* it is clicking.
        """
        # Skip if disabled in config
        if self.config and not self.config.controller.highlight_elements:
            return

        try:
            # Execute JS in browser context for a premium "glow" highlight
            await locator.evaluate(f"""(el, color) => {{
                if (!el.dataset.originalStyle) el.dataset.originalStyle = el.getAttribute('style') || '';
                
                el.style.boxShadow = `0 0 15px ${{color}}, inset 0 0 10px ${{color}}`;
                el.style.border = `2px solid ${{color}}`;
                el.style.transition = 'all 0.3s ease';
                
                setTimeout(() => {{
                    el.setAttribute('style', el.dataset.originalStyle);
                }}, 1000);
            }}""", color)
            
            # Artificial delay for human observation (if configured)
            if self.config:
                await asyncio.sleep(self.config.controller.action_delay)
                
        except Exception as e:
            # Highlighting failure should NEVER fail the task
            log.debug(f"Highlighting failed (likely element invisible/detached): {e}")

    async def click_element(self, state: BrowserState, ax_id: int) -> str:
        """
        Robust Click Procedure:
        1. Resolve Locator.
        2. Scroll into View.
        3. Highlight.
        4. Wait for Stability (Attached & Visible).
        5. Click.
        """
        target = await self._resolve_locator(state, ax_id)
        if not target:
            return f"Error: Element [ax-{ax_id}] could not be located on the page."

        try:
            # 1. Scroll & Wait
            await target.scroll_into_view_if_needed(timeout=2000)
            
            # Wait specifically for the element to be ready for interaction
            await target.wait_for(state="visible", timeout=self.config.controller.element_timeout * 1000)
            
            # 2. Visual Confirmation
            asyncio.create_task(self.highlight(target, "red")) 
            
            # 3. Execution
            # We use force=False by default to ensure it's actually clickable (not covered).
            # If that fails, we catch and try force=True.
            try:
                await target.click(timeout=3000)
            except Exception as e:
                # If element is covered or shifted, try forcing it
                log.warning(f"Click failed for [ax-{ax_id}]: {e}. Retrying with force=True...")
                await asyncio.sleep(0.5)
                await target.click(force=True, timeout=3000)

            # --- SMART WAIT ---
            # Clicking often triggers navigation. We must wait before returning to the Agent.
            await self._wait_for_potential_navigation()

            return f"Success: Clicked element [ax-{ax_id}]."

        except PlaywrightTimeoutError:
            return f"Error: Timeout waiting for [ax-{ax_id}] to become clickable."
        except Exception as e:
            return f"Error: Click failed unexpectedly: {str(e)}"

    async def input_text(self, state: BrowserState, ax_id: int, text: str, clear: bool = True, submit: bool = False) -> str:
        target = await self._resolve_locator(state, ax_id)
        if not target:
            return f"Error: Input field [ax-{ax_id}] not found."

        try:
            await target.scroll_into_view_if_needed()
            asyncio.create_task(self.highlight(target, "blue"))
            
            if clear:
                await target.fill("")
            
            # 'type' sends individual keypress events, triggering JS listeners better than 'fill'
            await target.type(text, delay=10) # 10ms delay for natural but fast input
            
            # Optional: Blur the element to trigger 'onchange' events
            await target.blur()
            
            if submit:
                # Trigger internal Enter press on the element
                await target.press("Enter")
                await self._wait_for_potential_navigation()
                return f"Success: Typed '{text}' into [ax-{ax_id}] and submitted (Enter)."
                
            return f"Success: Typed '{text}' into [ax-{ax_id}]."

        except Exception as e:
            return f"Error: Input failed: {str(e)}"

    async def press_key(self, key: str) -> str:
        """
        Presses a specific key on the page.
        Useful for Enter, Escape, ArrowKeys, etc.
        """
        try:
            await self.page.keyboard.press(key)
            await self._wait_for_potential_navigation()
            return f"Success: Pressed key '{key}'."
        except Exception as e:
            return f"Error: Key press failed: {str(e)}"

    async def upload_file(self, state: BrowserState, ax_id: int, file_path: str) -> str:
        """
        Uploads a file to a specific input element.
        The element should be an <input type="file"> or a drop zone.
        """
        import os
        if not os.path.exists(file_path):
            return f"Error: File at path '{file_path}' does not exist."

        target = await self._resolve_locator(state, ax_id)
        if not target:
            return f"Error: Input field [ax-{ax_id}] not found."

        try:
            # Check visibility. Hidden file inputs cannot be scrolled to or highlighted.
            # (Sites like WhatsApp and Instagram hide the actual <input type="file">)
            is_visible = await target.is_visible()
            if is_visible:
                try:
                    await target.scroll_into_view_if_needed(timeout=2000)
                    asyncio.create_task(self.highlight(target, "green"))
                except Exception:
                    pass # Ignore visual errors, focus on the upload

            # Try to upload directly (works on <input type="file"> even if hidden)
            await target.set_input_files(file_path, timeout=5000)
            await asyncio.sleep(1.0)
            
            return f"Success: Uploaded file '{file_path}' to [ax-{ax_id}]."
        except Exception as e:
            if "not an HTMLInputElement" in str(e) or "type is not file" in str(e):
                return (
                    f"Error: Element [ax-{ax_id}] is NOT a File Input (it is likely a button). "
                    f"You MUST use ask_clarification to tell the Planner: 'An OS file dialog will open. "
                    f"Please ask the OS Agent to focus the file dialog, type the path {file_path}, and press Enter.'"
                )
            return f"Error: File upload failed: {str(e)}"

    async def scroll(self, direction: Literal["up", "down", "top", "bottom"] = "down", amount: int = 800, target_id: Optional[int] = None) -> str:
        """
        Scrolls the viewport OR a specific scrollable element (Partitioned UI).
        """
        try:
            target_css = "window"
            if target_id:
                # Resolve the specific scrollable element
                selector = f'[data-pcagent-id="ax-{target_id}"]'
                target_css = f'document.querySelector(\'{selector}\')'
            
            if direction == "top":
                js = f"{target_css}.scrollTo({{ top: 0, behavior: 'smooth' }});"
            elif direction == "bottom":
                # For elements, scrollHeight is on the element itself. For window, it's document.body.scrollHeight.
                scroll_h = "document.body.scrollHeight" if not target_id else "scrollHeight"
                js = f"{target_css}.scrollTo({{ top: {target_css}.{scroll_h} || 99999, behavior: 'smooth' }});"
            else:
                delta_y = amount if direction == "down" else -amount
                method = "scrollBy" if not target_id else "scrollBy" # Both support scrollBy
                js = f"{target_css}.{method}({{ top: {delta_y}, behavior: 'smooth' }});"
            
            await self.page.evaluate(js)
            await asyncio.sleep(0.8) 
            target_name = f"[ax-{target_id}]" if target_id else "viewport"
            return f"Success: Scrolled {direction} in {target_name} ({amount}px)."
        except Exception as e:
            return f"Error: Scroll failed: {str(e)}"

    async def scroll_to_element(self, state: BrowserState, ax_id: int) -> str:
        """
        Jump- scrolls a specific element into view.
        """
        target = await self._resolve_locator(state, ax_id)
        if not target:
            return f"Error: Element [ax-{ax_id}] not found."
        
        try:
            await target.scroll_into_view_if_needed()
            asyncio.create_task(self.highlight(target, "purple"))
            return f"Success: Scrolled [ax-{ax_id}] into view."
        except Exception as e:
            return f"Error: scroll_to_element failed: {str(e)}"

    async def hover(self, state: BrowserState, ax_id: int) -> str:
        target = await self._resolve_locator(state, ax_id)
        if not target: return f"Error: Element [ax-{ax_id}] not found."
        
        try:
            await target.scroll_into_view_if_needed()
            asyncio.create_task(self.highlight(target, "orange"))
            await target.hover()
            return f"Success: Hovered over [ax-{ax_id}]."
        except Exception as e:
            return f"Error: Hover failed: {str(e)}"