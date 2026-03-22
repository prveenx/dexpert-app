# FILE: engine/core/context/episodic.py
"""
Episodic Context Manager.

The ultimate cure for 'Lazy LLM' hallucination.
Manages the prompt assembly and executes the Clean Slate Protocol (History Flushing)
at the end of every queue item processing cycle.
"""

import logging
from typing import List, Dict, Any, Optional
from core.memory.workflow_tracker import WorkflowTracker
from core.context.strategy import StrategyCache
from core.context.hud import HUDGenerator

log = logging.getLogger(__name__)

class EpisodicContext:
    def __init__(self, max_tokens: int = 100_000, recent_window: int = 10):
        self.max_tokens = max_tokens
        self.recent_window = recent_window
        
        self.strategy_cache = StrategyCache()
        
        # The volatile action history (Wiped every episode)
        self._action_history: List[Dict[str, Any]] =[]

    def add_message(self, role: str, content: str) -> None:
        """Adds a turn to the current episode."""
        self._action_history.append({"role": role, "content": content})
        
        # Micro-compression: If the episode itself is getting too long, 
        # pop the oldest actions to keep scaling perfectly flat.
        if len(self._action_history) > self.recent_window * 2:
            self._action_history = self._action_history[-self.recent_window:]

    def end_episode(self) -> None:
        """
        THE CLEAN SLATE PROTOCOL.
        Called when an item is Committed or Skipped.
        """
        log.info("Ending Episode: Distilling strategy and flushing Action History...")
        
        # 1. Distill procedural memory from this episode
        self.strategy_cache.extract_from_episode(self._action_history)
        
        # 2. Nuke the action history. Clicks, DOM trees, and thoughts are erased.
        self._action_history =[]
        
        log.info("Action History flushed. Ready for next episode.")

    def get_context_window(
        self,
        system_prompt: str,
        tool_schemas: str,
        tracker: WorkflowTracker,
        current_observation: str
    ) -> List[Dict[str, Any]]:
        """
        Assembles the perfectly scaled, cache-friendly LLM prompt.
        """
        messages = []

        # 1. SYSTEM IDENTITY + TOOL SCHEMAS
        sys_content = system_prompt
        if tool_schemas:
            sys_content += f"\n\nAVAILABLE_TOOLS:\n{tool_schemas}"
        messages.append({"role": "system", "content": sys_content})

        # 2. ARCHIVE
        if self._archive_summary:
            messages.append({
                "role": "user",
                "content": f"PREVIOUS_ACTIONS_SUMMARY:\n{self._archive_summary}",
            })

        # 3. RECENT HISTORY with budget trimming
        recent = list(self._raw_history)
        fixed_tokens = estimate_tokens(sys_content) + estimate_tokens(self._archive_summary)
        recent_tokens = sum(m.get("_tokens", 0) for m in recent)
        dynamic_tokens = estimate_tokens(current_observation) + estimate_tokens(scratchpad_status)

        budget = int(self.max_tokens * 0.88)
        total = fixed_tokens + recent_tokens + dynamic_tokens

        while recent and total > budget:
            removed = recent.pop(0)
            total -= removed.get("_tokens", 0)

        for msg in recent:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # 4. CURRENT OBSERVATION
        if current_observation:
            messages.append({"role": "user", "content": str(current_observation)})

        # 5. SCRATCHPAD STATUS
        if scratchpad_status:
            messages.append({
                "role": "user",
                "content": f"SCRATCHPAD:\n{scratchpad_status}\n\nDetermine your NEXT action.",
            })

        return messages

    def get_raw_history(self) -> List[Dict[str, str]]:
        """Get raw history for checkpoint saving."""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in self._raw_history
        ]

    def clear(self) -> None:
        """Clear all history (between tasks)."""
        self._raw_history = []
        self._archive_summary = ""
        self._archive_message_count = 0
        self._total_raw_tokens = 0

    def wipe_for_item_completion(self) -> None:
        """
        Wipe ReAct action history after completing a queue item.
        Preserves archive but clears recent history to prevent
        context pollution in multi-item workflows.
        """
        # Compress everything into archive first
        for msg in self._raw_history:
            compressed = compress_message(msg)
            if compressed:
                if self._archive_summary:
                    self._archive_summary += "\n" + compressed
                else:
                    self._archive_summary = compressed

        self._raw_history = []
        self._total_raw_tokens = 0
        log.info("EpisodicContext: Wiped recent history for item completion")

    @property
    def message_count(self) -> int:
        return len(self._raw_history)

    def _maybe_compress(self) -> None:
        """Batch compression when history exceeds threshold."""
        threshold = self.recent_window * 2
        if len(self._raw_history) <= threshold:
            return

        batch_size = self.recent_window
        to_archive = self._raw_history[:batch_size]
        self._raw_history = self._raw_history[batch_size:]

        compressed_parts = []
        for msg in to_archive:
            compressed = compress_message(msg)
            if compressed:
                compressed_parts.append(compressed)
            self._total_raw_tokens -= msg.get("_tokens", 0)

        if compressed_parts:
            new_archive = "\n".join(compressed_parts)
            if self._archive_summary:
                self._archive_summary += "\n" + new_archive
            else:
                self._archive_summary = new_archive

        # Trim archive if too large
        archive_budget = int(self.max_tokens * ARCHIVE_ZONE_MAX_PCT)
        if estimate_tokens(self._archive_summary) > archive_budget:
            lines = self._archive_summary.split("\n")
            while lines and estimate_tokens("\n".join(lines)) > archive_budget:
                lines.pop(0)
            self._archive_summary = "\n".join(lines)
