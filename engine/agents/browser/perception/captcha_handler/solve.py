# FILE: /browser/perception/captcha_handler/solve.py
"""
CAPTCHA detection, bbox validation, cropping, OCR, and input filling.

Flow:
  1. PerceptionPipeline detects a captcha node via heuristic scan.
  2. CaptchaHandler validates the bbox (non-zero, within viewport).
  3. Takes a screenshot, crops to the captcha region (respecting crop_width/height).
  4. Sends to Vision LLM for OCR.
  5. Returns CaptchaSolution(text, input_ax_id) so the agent can type it.
"""
import logging
import base64
import io
from dataclasses import dataclass
from typing import Optional, Tuple, Any

from .browser.state import BrowserState, DOMNode, BoundingBox
from .browser.config.config import BrowserAgentSettings
from .browser.perception.perception import PerceptionPipeline
from llm.client import LLMClient

log = logging.getLogger(__name__)


@dataclass
class CaptchaSolution:
    """Result of a successful captcha solve attempt."""
    text: str
    input_ax_id: Optional[int]  # The ax-ID of the input field to fill


class CaptchaHandler:
    """
    Handles the full captcha lifecycle:
      detect → validate bbox → crop → OCR → find input → return solution.

    Designed to be called from the agent's ReAct loop when a captcha
    is detected during perception.
    """

    def __init__(
        self,
        settings: BrowserAgentSettings,
        perception: PerceptionPipeline,
        llm: LLMClient,
        prompts: Any,
    ):
        self.settings = settings
        self.perception = perception
        self.llm = llm
        self.prompts = prompts

    async def detect_and_solve(
        self,
        state: BrowserState,
        page: Any, 
    ) -> Optional[CaptchaSolution]:
        """
        End-to-end captcha handling.
        """
        if not self.settings.captcha.enabled or not self.settings.captcha.auto_solve:
            return None

        # 1. Detect
        captcha_node = self.perception.detect_captcha(state)
        if not captcha_node:
            return None

        log.info(f"CaptchaHandler: Attempting to solve [ax-{captcha_node.ax_id}]")

        # 2. Validate bbox
        validated_bbox = self._validate_bbox(captcha_node.bbox, state.viewport_size)
        if not validated_bbox:
            log.warning("CaptchaHandler: Invalid bbox — skipping.")
            return None

        # 3. Get screenshot (force it, vision is needed)
        screenshot_b64 = state.screenshot_base64
        if not screenshot_b64:
            screenshot_b64 = await self.perception.capture_screenshot(page)
        if not screenshot_b64:
            log.error("CaptchaHandler: Cannot take screenshot.")
            return None

        # 4. Crop
        cropped_b64 = self.perception.crop_to_bbox(
            screenshot_b64, validated_bbox, state.viewport_size
        )
        if not cropped_b64:
            log.error("CaptchaHandler: Crop failed.")
            return None

        # 5. OCR via Vision LLM
        ocr_text = await self._ocr_via_vision(cropped_b64)
        if not ocr_text:
            log.warning("CaptchaHandler: OCR returned empty.")
            return None

        # 6. Find input field
        input_node = self.perception.find_captcha_input(state, captcha_node)
        input_id = input_node.ax_id if input_node else None

        if input_id:
            log.info(f"CaptchaHandler: OCR='{ocr_text}', target input=[ax-{input_id}]")
        else:
            log.warning(f"CaptchaHandler: OCR='{ocr_text}', but no input field found nearby.")

        return CaptchaSolution(text=ocr_text, input_ax_id=input_id)

    # ------------------------------------------------------------------
    # Bbox Validation
    # ------------------------------------------------------------------

    def _validate_bbox(
        self,
        bbox: BoundingBox,
        viewport: dict,
    ) -> Optional[BoundingBox]:
        """
        Validates that the captcha bbox:
          - Has non-zero width and height
          - Falls within (or overlaps) the viewport
          - Gets clamped to viewport bounds

        Returns a corrected BoundingBox, or None if invalid.
        """
        # Non-zero check
        if bbox.width <= 0 or bbox.height <= 0:
            log.debug(f"CaptchaHandler: bbox has zero/negative dimensions: {bbox}")
            return None

        vw = viewport.get("width", 1366)
        vh = viewport.get("height", 968)

        # Completely off-screen?
        if bbox.x >= vw or bbox.y >= vh:
            log.debug(f"CaptchaHandler: bbox completely off-screen: {bbox}")
            return None
        if (bbox.x + bbox.width) <= 0 or (bbox.y + bbox.height) <= 0:
            log.debug(f"CaptchaHandler: bbox completely off-screen (negative): {bbox}")
            return None

        # Clamp to viewport
        clamped_x = max(0.0, bbox.x)
        clamped_y = max(0.0, bbox.y)
        clamped_w = min(bbox.width, vw - clamped_x)
        clamped_h = min(bbox.height, vh - clamped_y)

        return BoundingBox(x=clamped_x, y=clamped_y, width=clamped_w, height=clamped_h)

    # ------------------------------------------------------------------
    # Vision LLM OCR
    # ------------------------------------------------------------------

    async def _ocr_via_vision(self, cropped_b64: str) -> Optional[str]:
        """
        Sends the cropped captcha image to the Vision LLM and extracts text.
        Retries up to max_attempts on failure.
        """
        
        # We use the General Vision System Prompt, but force a strict query.
        ocr_query = (
            "This image contains a CAPTCHA security code. "
            "Your task is pure OCR to read the text. "
            "Output ONLY the exact characters visible in the image. "
            "Do not add any explanation, punctuation, or formatting."
        )

        for attempt in range(1, self.settings.captcha.max_attempts + 1):
            try:
                # Assuming prompts.vision_system_prompt is available
                solution = await self.llm.generate_with_image(
                    system=self.prompts.vision_system_prompt,
                    prompt=ocr_query,
                    image_base64=cropped_b64,
                )
                solution = solution.strip()
                if solution:
                    log.info(f"CaptchaHandler: OCR attempt {attempt} succeeded: '{solution}'")
                    return solution

            except Exception as e:
                log.warning(f"CaptchaHandler: OCR attempt {attempt} failed: {e}")

        return None
