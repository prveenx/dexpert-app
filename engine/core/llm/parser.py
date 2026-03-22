# FILE: core/llm/parser.py
"""
Unified LLM Response Parser.

Adapted from PCAgent MAF prototype. Supports both XML tags and
legacy bracket tags for backward compatibility.

Expected LLM Output Format:

    <thinking>
    My reasoning here...
    </thinking>

    <action>
    [{"tool_name": "...", "parameters": {...}}]
    </action>

OR (for task completion):

    <thinking>
    Task is done because...
    </thinking>

    <done>Summary of what was accomplished.</done>
"""

import re
import json
import logging
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class ParsedResponse:
    """Structured result from parsing an LLM response."""

    thinking: Optional[str] = None
    actions: List[Dict[str, Any]] = field(default_factory=list)
    done: Optional[str] = None  # If present, the agent wants to finalize

    @property
    def has_actions(self) -> bool:
        return len(self.actions) > 0

    @property
    def is_done(self) -> bool:
        return self.done is not None


class ActionParser:
    """
    Unified XML-Based Response Parser.

    Supports both XML tags and legacy [BRACKET] tags for backward compatibility.
    """

    # --- XML Tag Patterns (Primary) ---
    _RE_THINKING_XML = re.compile(
        r"<thinking>(.*?)</thinking>", re.DOTALL | re.IGNORECASE
    )
    _RE_ACTION_XML = re.compile(
        r"<action>(.*?)</action>", re.DOTALL | re.IGNORECASE
    )
    _RE_DONE_XML = re.compile(
        r"<done>(.*?)</done>", re.DOTALL | re.IGNORECASE
    )

    # --- Legacy [BRACKET] Patterns (Fallback) ---
    _RE_THINKING_LEGACY = re.compile(
        r"\[THINKING\](.*?)\[/THINKING\]", re.DOTALL | re.IGNORECASE
    )
    _RE_ACTION_LEGACY = re.compile(
        r"\[ACTION\](.*?)\[/ACTION\]", re.DOTALL | re.IGNORECASE
    )
    _RE_ACTION_OPEN_LEGACY = re.compile(
        r"\[ACTION\](.*)", re.DOTALL | re.IGNORECASE
    )

    def parse(self, text: str) -> ParsedResponse:
        """
        Main parse method. Extracts thinking, actions, and done signal.
        Returns a ParsedResponse with structured data.
        """
        result = ParsedResponse()

        # --- PHASE 1: Extract Thinking ---
        result.thinking = self._extract_thinking(text)

        # --- PHASE 2: Check for <done> (Task Complete Signal) ---
        done_match = self._RE_DONE_XML.search(text)
        if done_match:
            content = done_match.group(1).strip()
            # Clean up redundant XML bleed
            content = re.sub(r"<[a-zA-Z0-9_-]+>", "", content)
            content = re.sub(r"</[a-zA-Z0-9_-]+>", "\n", content)
            result.done = content.strip()
            return result

        # --- PHASE 3: Extract Actions ---
        result.actions = self._extract_actions(text)

        return result

    def _extract_thinking(self, text: str) -> Optional[str]:
        """Extract thinking from XML or legacy tags."""
        match = self._RE_THINKING_XML.search(text)
        if match:
            return match.group(1).strip()

        match = self._RE_THINKING_LEGACY.search(text)
        if match:
            return match.group(1).strip()

        # Fallback: Text before any action/done tag
        for marker in ["<action>", "<done>", "[ACTION]"]:
            if marker.lower() in text.lower():
                idx = text.lower().index(marker.lower())
                pre = text[:idx].strip()
                if pre and len(pre) > 10 and not pre.strip().startswith("{"):
                    return pre

        return None

    def _extract_actions(self, text: str) -> List[Dict[str, Any]]:
        """Extract action JSON from XML or legacy tags."""
        json_str = None

        # Strategy A: XML <action> tags
        match = self._RE_ACTION_XML.search(text)
        if match:
            json_str = match.group(1).strip()

        # Strategy B: Legacy [ACTION]...[/ACTION] tags
        if not json_str:
            match = self._RE_ACTION_LEGACY.search(text)
            if match:
                json_str = match.group(1).strip()

        # Strategy C: Open legacy [ACTION] tag
        if not json_str:
            match = self._RE_ACTION_OPEN_LEGACY.search(text)
            if match:
                json_str = match.group(1).strip()

        # Strategy D: Raw JSON array with tool_name
        if not json_str:
            json_array_match = re.search(r"(\[.*\])", text, re.DOTALL)
            if json_array_match:
                candidate = json_array_match.group(1).strip()
                if '"tool_name"' in candidate:
                    json_str = candidate

        if json_str:
            return self._decode_json(json_str)

        return []

    def _decode_json(self, json_str: str) -> List[Dict[str, Any]]:
        """Clean and parse JSON string into action list."""
        # Remove Markdown code fences
        json_str = re.sub(r"^```json\s*", "", json_str)
        json_str = re.sub(r"^```\s*", "", json_str)
        json_str = re.sub(r"\s*```$", "", json_str)
        json_str = json_str.strip()

        try:
            parsed = json.loads(json_str)

            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                log.warning(f"Parsed JSON was not list or dict: {type(parsed)}")
                return []

        except json.JSONDecodeError as e:
            log.error(f"JSON Parse Error: {e}")
            log.debug(f"Failed JSON Content: {json_str[:200]}")
            return []
