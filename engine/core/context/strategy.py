# FILE: engine/core/context/strategy.py
"""
Strategy Cache (Procedural Memory Distillation)

Extracts 1-shot learning rules from the LLM's thought process before the 
Action History is wiped at the end of an episode.
"""

import re
import logging
from typing import List, Dict, Any

log = logging.getLogger(__name__)


class StrategyCache:
    """Maintains a rolling cache of procedural rules discovered during an episode."""

    def __init__(self, max_rules: int = 5):
        self.max_rules = max_rules
        self._rules: List[str] =[]

    def extract_from_episode(self, history: List[Dict[str, Any]]) -> None:
        """
        Scans the episode's history (specifically <thinking> blocks) for explicit
        learning markers right before the history is flushed.
        """
        patterns =[
            r"LEARNED:\s*(.+)",
            r"STRATEGY:\s*(.+)",
            r"RULE:\s*(.+)",
            r"NOTE TO SELF:\s*(.+)",
        ]

        for msg in history:
            if msg.get("role") != "assistant":
                continue
            
            content = str(msg.get("content", ""))
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    rule = match.strip()
                    if len(rule) > 10 and rule not in self._rules:
                        self._rules.append(rule)
                        log.info(f"Strategy Distilled: '{rule[:60]}...'")

        # Keep only the freshest, most relevant rules
        if len(self._rules) > self.max_rules:
            self._rules = self._rules[-self.max_rules:]

    def get_formatted_rules(self) -> str:
        if not self._rules:
            return "No specific procedural rules identified yet."
        
        return "\n".join([f"- {rule}" for rule in self._rules])

    def clear(self) -> None:
        self._rules =[]