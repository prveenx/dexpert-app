# FILE: /browser/perception/service.py
import logging
import time
import os
from typing import Optional, Dict, Any, List
from playwright.async_api import Page
from ..state import BrowserState, DOMNode, BoundingBox
from ..config.config import BrowserAgentSettings

log = logging.getLogger(__name__)

class PerceptionEngine:
    """
    The 'Eyes' of the Browser Agent. 
    Manages Javascript injection and State consolidation.
    """

    def __init__(self, settings: BrowserAgentSettings):
        self.settings = settings
        self._js_code: Optional[str] = None
        self._load_processor()

    def _load_processor(self):
        """Loads the V5 high-performance DOM processor script."""
        try:
            # Assumes processor.js is in the same directory
            path = os.path.join(os.path.dirname(__file__), "processor.js")
            if not os.path.exists(path):
                raise FileNotFoundError(f"processor.js not found at {path}")
                
            with open(path, "r", encoding="utf-8") as f:
                self._js_code = f.read()
            log.info("Perception: JS Processor loaded.")
        except Exception as e:
            log.critical(f"Perception: Failed to load processor.js: {e}")
            raise

    async def capture(self, page: Page) -> BrowserState:
        """
        Takes a snapshot of the current browser page.
        1. Ensures JS is injected.
        2. Runs the scan (silently, without highlights).
        3. Parses raw dictionary into Pydantic models.
        """
        if page.is_closed():
            return BrowserState(url="closed", title="closed", errors=["Page is closed"])

        start_time = time.perf_counter()

        try:
            # Step 1: Injection
            is_alive = await page.evaluate("() => typeof window.PCAgentProcessor !== 'undefined'")
            if not is_alive:
                if not self._js_code:
                     self._load_processor()
                await page.evaluate(self._js_code)

            # Step 2: Execution
            # Respects the highlight_elements setting from YAML
            show_h = "true" if self.settings.controller.highlight_elements else "false"
            raw_data = await page.evaluate(f"""() => {{
                window.PCAGENT_CONFIG = {{ show_highlights: {show_h} }};
                return window.PCAgentProcessor.run();
            }}""")

            if not raw_data or "registry" not in raw_data:
                raise ValueError("JS Processor returned empty or malformed data.")

            # Step 3: Transformation
            registry = raw_data["registry"]
            nodes = {}
            for ax_id_str, val in registry.items():
                ax_id = int(ax_id_str)
                
                box = val.get("box", {})
                bbox = BoundingBox(
                    x=box.get("x", 0), y=box.get("y", 0),
                    width=box.get("width", 0), height=box.get("height", 0)
                )

                nodes[ax_id] = DOMNode(
                    ax_id=ax_id,
                    role=val.get("type", "generic"),
                    name=val.get("text", ""),
                    value=val.get("attributes", {}).get("value"),
                    states=self._parse_tags(val.get("tags", "")),
                    bbox=bbox,
                    selector=val.get("selector"),
                    xpath=val.get("xpath"),
                    attributes=val.get("attributes", {})
                )

            # Step 4: Metadata
            duration = (time.perf_counter() - start_time) * 1000
            
            # Safe Viewport extraction
            vp_dict = {}
            if page.viewport_size:
                vp_dict = page.viewport_size

            state = BrowserState(
                url=page.url,
                title=await page.title(),
                dom_nodes=nodes,
                viewport_size=vp_dict,
                scan_duration_ms=duration
            )
            
            # Only log if slow
            if duration > 500:
                log.warning(f"Perception: Slow capture ({duration:.1f}ms) for {len(nodes)} nodes")
                
            return state

        except Exception as e:
            log.error(f"Perception: Capture failed: {e}")
            return BrowserState(
                url=page.url,
                title="Error",
                errors=[str(e)]
            )

    def _parse_tags(self, tags_str: str) -> List[str]:
        """Cleans '[DISABLED] [CHECKED]' -> ['DISABLED', 'CHECKED']"""
        import re
        if not tags_str: return []
        return re.findall(r'\[(.*?)\]', tags_str)