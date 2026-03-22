# FILE: engine/core/context/hud.py
"""
The North Star HUD (Heads-Up Display).

Replaces the LLM's reliance on historical message context by projecting
the absolute truth of the state machine directly into the prompt prefix.
"""

from core.memory.workflow_tracker import WorkflowTracker
from core.context.strategy import StrategyCache

class HUDGenerator:
    """Generates the Mission Control panel."""

    @staticmethod
    def generate_mission_control(tracker: WorkflowTracker, strategy_cache: StrategyCache) -> str:
        """Builds the strict, read-only state panel."""
        
        lines =[
            "=========================================================",
            "  📍 MISSION CONTROL : SYSTEM HUD",
            "=========================================================",
            f"MASTER GOAL: {tracker.master_goal}",
            f"WORKFLOW PHASE: {tracker.phase.value.upper()}",
            ""
        ]

        # 1. Queue Metrics
        m = tracker.metrics
        lines.append(f"[ QUEUE STATUS ]")
        lines.append(f"Total Targets: {m['total']} | Completed: {m['done']} | Skipped: {m['skipped']} | Pending: {m['pending']}")
        lines.append("")

        # 2. History Snippet (Data awareness without token bloat)
        lines.append(f"[ PREVIOUSLY COLLECTED (Total: {len(tracker.collected_data)}) ]")
        if not tracker.collected_data:
            lines.append("  (No data collected yet)")
        else:
            # Show ONLY the last 2 items compactly
            for idx, item in enumerate(tracker.collected_data[-2:], 1):
                preview = {k: v for k, v in item.items() if not str(k).startswith("_")}
                lines.append(f"  ... Item: {item.get('_title', 'Unknown')} -> {str(preview)[:100]}...")
            lines.append("  (Older items safely secured in Long-Term Database. DO NOT RE-EXTRACT THEM.)")
        lines.append("")

        # 3. The Active Target
        current = tracker.get_current()
        lines.append("[ CURRENT ACTIVE TARGET ]")
        if current:
            lines.append(f"Target ID: #{current.id}")
            lines.append(f"Name/Title: {current.title or 'N/A'}")
            lines.append(f"URI/Location: {current.target}")
            lines.append(f"Attempts: {current.attempts}")
        else:
            lines.append("  (No active target. Call `scratchpad_next` or transition phase.)")
        lines.append("")

        # 4. Strategy Cache
        lines.append("[ PROCEDURAL STRATEGY CACHE ]")
        lines.append(strategy_cache.get_formatted_rules())
        lines.append("=========================================================")

        return "\n".join(lines)