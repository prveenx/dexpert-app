# FILE: /browser/perception/perception.py
"""
Unified Perception Pipeline for the Browser Agent.

This module is the single entry point for all 'sensing' operations:
  1. DOM capture     — via PerceptionEngine (JS injection → Pydantic state)
  2. Screenshot      — on-demand or when captcha/vision is triggered
  3. Captcha detect  — heuristic scan of DOM nodes for known captcha patterns

Design: Vision is OFF by default for cost efficiency. Screenshots are only
taken when explicitly requested (analyze_visual tool) or when a captcha is
detected and auto_solve is enabled.
"""
import base64
import io
import logging
from typing import Optional, Dict, List

from playwright.async_api import Page

from .browser.config.config import BrowserAgentSettings
from .browser.perception.service import PerceptionEngine
from .browser.state import BrowserState, DOMNode

log = logging.getLogger(__name__)

# Keywords that indicate a CAPTCHA element in the DOM
_CAPTCHA_SIGNALS = frozenset({
    "captcha", "recaptcha", "hcaptcha", "turnstile", "challenge",
    "security-check", "verify", "are you a robot", "not a robot",
    "i'm not a robot", "verification",
})


class PerceptionPipeline:
    """
    High-level façade that orchestrates DOM capture, screenshots,
    and captcha detection in one coherent API.

    Usage::

        pipeline = PerceptionPipeline(settings)
        state = await pipeline.capture(page)
        captcha_node = pipeline.detect_captcha(state)
    """

    def __init__(self, settings: BrowserAgentSettings):
        self.settings = settings
        self._engine = PerceptionEngine(settings)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def capture(
        self,
        page: Page,
        force_screenshot: bool = False,
    ) -> BrowserState:
        """
        Full perception pass:
          1. DOM scan via JS processor
          2. Screenshot (if visual_mode enabled, or force_screenshot=True)
          3. Viewport metadata

        Returns a fully populated BrowserState.
        """
        # 1. DOM capture (always)
        state = await self._engine.capture(page)

        # 2. Screenshot (conditional)
        take_ss = force_screenshot or self.settings.perception.visual_mode
        if take_ss and not page.is_closed():
            screenshot_b64 = await self.capture_screenshot(page)
            state.screenshot_base64 = screenshot_b64

        # 3. Viewport
        if not page.is_closed():
            try:
                vp = page.viewport_size
                if vp:
                    state.viewport_size = {"width": vp["width"], "height": vp["height"]}
            except Exception:
                pass

        return state

    async def capture_screenshot(self, page: Page) -> Optional[str]:
        """
        Takes a PNG screenshot of the visible viewport and returns it as
        a base64-encoded string.  Returns None on failure.
        """
        if page.is_closed():
            return None

        try:
            raw_bytes = await page.screenshot(
                type="png",
                full_page=False,
            )
            return base64.b64encode(raw_bytes).decode("utf-8")
        except Exception as e:
            log.warning(f"PerceptionPipeline: screenshot failed: {e}")
            return None

    async def capture_element_screenshot(
        self,
        page: Page,
        state: BrowserState,
        ax_id: int,
    ) -> Optional[str]:
        """
        Crops a screenshot to the bounding box of a specific element.
        Used by the captcha handler and analyze_visual tool.

        Returns base64-encoded PNG, or None on failure.
        """
        from PIL import Image  # local import — only needed when vision is active

        node = state.get_node(ax_id)
        if not node:
            log.warning(f"Element [ax-{ax_id}] not found for cropping.")
            return None

        # Take full viewport screenshot first
        full_ss = await self.capture_screenshot(page)
        if not full_ss:
            return None

        return self.crop_to_bbox(full_ss, node.bbox, state.viewport_size)

    def crop_to_bbox(
        self,
        screenshot_b64: str,
        bbox: "BoundingBox",
        viewport: Dict[str, int],
    ) -> Optional[str]:
        """
        Crops a base64 screenshot to the given bounding box + configured padding.
        Respects crop_width/crop_height limits from captcha config.
        """
        try:
            try:
                from PIL import Image
            except ImportError:
                log.warning("Pillow (PIL) not installed. Cannot crop image. Using full screenshot.")
                return screenshot_b64

            image_data = base64.b64decode(screenshot_b64)
            image = Image.open(io.BytesIO(image_data))
            img_w, img_h = image.size

            pad_w = self.settings.captcha.crop_padding.get("width", 20)
            pad_h = self.settings.captcha.crop_padding.get("height", 20)

            left = max(0, int(bbox.x) - pad_w)
            top = max(0, int(bbox.y) - pad_h)
            right = min(img_w, int(bbox.x + bbox.width) + pad_w)
            bottom = min(img_h, int(bbox.y + bbox.height) + pad_h)

            # Enforce max crop dimensions
            max_w = self.settings.captcha.crop_width
            max_h = self.settings.captcha.crop_height
            if (right - left) > max_w:
                right = left + max_w
            if (bottom - top) > max_h:
                bottom = top + max_h

            cropped = image.crop((left, top, right, bottom))

            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode("utf-8")

        except Exception as e:
            log.error(f"PerceptionPipeline: crop failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Captcha Detection
    # ------------------------------------------------------------------

    def detect_captcha(self, state: BrowserState) -> Optional[DOMNode]:
        """
        Scans the current DOM state for elements that look like CAPTCHAs.

        Strategy — check each node's name, attributes, and role against
        known CAPTCHA signal keywords.  Returns the first match, or None.
        """
        if not self.settings.captcha.enabled:
            return None

        for node in state.dom_nodes.values():
            if self._is_captcha_node(node):
                # Use plain text, no emojis to avoid encoding issues on Windows
                log.info(f"CAPTCHA-DISCOVERY: [ax-{node.ax_id}] role={node.role} name=\"{node.name}\"")
                return node

        return None

    def find_captcha_input(
        self,
        state: BrowserState,
        captcha_node: DOMNode,
    ) -> Optional[DOMNode]:
        """
        Given a captcha image/frame node, tries to find the adjacent
        input field where the OCR result should be typed.

        Heuristic: find the nearest INPUT node (by Y coordinate proximity)
        that has not been filled yet.
        """
        captcha_y = captcha_node.bbox.y
        candidates: List[DOMNode] = []

        for node in state.dom_nodes.values():
            if node.role.upper() in ("INPUT", "TEXTBOX", "TEXT"):
                # Only consider empty inputs within ±200px vertically
                if abs(node.bbox.y - captcha_y) < 200:
                    if not node.value:
                        candidates.append(node)

        if not candidates:
            return None

        # Return the closest one vertically
        candidates.sort(key=lambda n: abs(n.bbox.y - captcha_y))
        return candidates[0]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _is_captcha_node(node: DOMNode) -> bool:
        """
        Check if a node's text or attributes match captcha patterns.
        Strict heuristic to avoid expensive vision LLM false positives.
        """
        # 1. Role Filter: Captchas are almost always images, frames, or generic containers
        # Exclude typical interactive elements that are NOT captchas (buttons, links)
        if node.role.upper() in ("BUTTON", "LINK", "MENUITEM", "TAB", "CHECKBOX", "RADIO"):
            return False

        # 2. Content Scan
        searchable = (node.name or "").lower()
        for attr_val in node.attributes.values():
            if isinstance(attr_val, str):
                searchable += " " + attr_val.lower()

        # 3. Keyword Match with Role weighting
        # Words like 'verify' are only suspicious on images/iframes/regions
        is_suspicious_role = node.role.upper() in ("IMG", "IFRAME", "CANVAS", "GRAPHIC", "REGION", "GENERIC", "")
        
        matches_keyword = any(signal in searchable for signal in _CAPTCHA_SIGNALS)
        
        if matches_keyword:
            # If it's an image or iframe, it's a high-confidence captcha
            if node.role.upper() in ("IMG", "IFRAME", "CANVAS"):
                return True
            
            # If it's a generic container, only match if it contains specific 'strict' signals
            # things like 'not a robot' or 'recaptcha'
            strict_signals = {"recaptcha", "hcaptcha", "turnstile", "not a robot", "challenge"}
            if any(s in searchable for s in strict_signals):
                return True
            
            # Casual signals like 'verify' or 'security' require a suspicious role (like a region)
            if is_suspicious_role and ("captcha" in searchable or "security-check" in searchable):
                return True

        return False
