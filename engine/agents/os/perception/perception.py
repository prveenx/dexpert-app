# FILE: /os/perception/perception.py
import base64
import io
import logging
from typing import Optional, List
from PIL import ImageGrab, Image

log = logging.getLogger(__name__)

class OSPerceptionPipeline:
    """
    Handles Visual Perception (Screenshots) for the OS Agent.
    The Semantic DOM tree is handled by the Rust Bridge, but pixels 
    are handled here using Python's native Pillow library.
    """
    def __init__(self, bridge_client, vision_llm, prompts):
        self.bridge = bridge_client
        self.vision_llm = vision_llm
        self.prompts = prompts

    async def capture_screenshot(self, bbox: Optional[List] = None) -> Optional:
        """
        Takes a cross-platform native screenshot.
        If bbox is provided, it crops the image.
        """
        try:
            # Capture across all monitors
            img = ImageGrab.grab(all_screens=True)
            
            if bbox and len(bbox) == 4:
                x, y, w, h = bbox
                # PIL crop expects (left, upper, right, lower)
                img = img.crop((x, y, x + w, y + h))
            
            # Convert to base64 for LiteLLM
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode('utf-8')
            
        except Exception as e:
            log.error(f"OS Screenshot failed: {e}")
            return None

    async def analyze_visual(self, query: str, target_id: Optional = None, focus_box: Optional = None) -> str:
        """
        Tool Handler: Takes a screenshot and asks the Vision LLM to analyze it.
        """
        # If the LLM provides an ax_id, we ask Rust for its exact physical coordinates to crop
        if target_id and not focus_box:
            # Optional: If we want to crop to a specific element, we ask the cache.
            # For now, if no focus_box is provided, we analyze the full screen.
            pass

        # 1. Capture Pixels
        screenshot_b64 = await self.capture_screenshot(bbox=focus_box)
        if not screenshot_b64:
            return "Error: Failed to capture screen. Ensure the OS allows screen recording."

        # 2. Query Vision LLM
        try:
            # We use the main system prompt to give the Vision model context of what it's looking at
            response = await self.vision_llm.generate_with_image(
                system="You are PCAgent's Visual Cortex. Analyze the provided OS screenshot.",
                prompt=query,
                image_base64=screenshot_b64
            )
            return f"Visual Analysis: {response.strip()}"
            
        except Exception as e:
            log.error(f"Vision LLM Error: {e}", exc_info=True)
            return f"Error during vision analysis: {e}"