# FILE: engine/core/memory/workflow_tracker.py
"""
Workflow Tracker (The State Ledger)

Replaces volatile scratchpads with a strict, confidence-gated state machine.
Enforces the Omni-Queue (polymorphic targets) and prevents context degradation
by forcing self-correction on low-confidence extractions.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

log = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    SIMPLE = "simple"       # Shallow bulk (Gather -> Report)
    COMPLEX = "complex"     # Deep bulk (Gather -> Process -> Report)


class WorkflowPhase(str, Enum):
    IDLE = "idle"
    GATHER = "gather"
    PROCESS = "process"
    REPORT = "report"


class ItemStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class OmniQueueItem(BaseModel):
    """Polymorphic queue item (can be a URL, OS Path, UI Node ID, or Search Term)."""
    id: int
    target: str = Field(..., description="URL, Path, ax_id, or search term")
    title: str = ""
    status: ItemStatus = ItemStatus.PENDING
    data: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[int] = None
    error: Optional[str] = None
    attempts: int = 0
    added_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    model_config = ConfigDict(extra="ignore")


class WorkflowTracker(BaseModel):
    """
    The ultimate source of truth for the active task.
    Never wiped during episodic flushes.
    """
    task_id: Optional[str] = None
    master_goal: str = ""
    task_type: TaskComplexity = TaskComplexity.SIMPLE
    phase: WorkflowPhase = WorkflowPhase.IDLE
    target_count: Optional[int] = None

    # The Omni-Queue
    queue: List[OmniQueueItem] = Field(default_factory=list)
    current_index: Optional[int] = None
    _next_item_id: int = 1

    # Storage
    collected_data: List[Dict[str, Any]] = Field(default_factory=list)
    visited_targets: Set[str] = Field(default_factory=set)

    # Defensive Tracking
    _action_history: List[str] =[]
    _loop_threshold: int = 3
    workflow_notes: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")

    def init_workflow(self, task_id: str, goal: str, task_type: str = "simple", target_count: Optional[int] = None) -> None:
        self.task_id = task_id
        self.master_goal = goal
        self.task_type = TaskComplexity(task_type)
        self.target_count = target_count
        self.phase = WorkflowPhase.GATHER
        self._log_event(f"Workflow initialized: {self.task_type.value.upper()} | Target: {target_count or '∞'}")

    # --- OMNI-QUEUE MANAGEMENT ---

    def enqueue_items(self, items: List[Dict[str, Any]]) -> int:
        """Adds items to the polymorphic queue with deduping."""
        added = 0
        for raw in items:
            target = str(raw.get("target") or raw.get("url") or raw.get("ax_id") or "").strip()
            title = str(raw.get("title", "")).strip()

            if not target:
                continue

            if target in self.visited_targets or any(i.target == target for i in self.queue):
                continue

            q_item = OmniQueueItem(
                id=self._next_item_id,
                target=target,
                title=title,
                data={k: v for k, v in raw.items() if k not in ("target", "url", "ax_id", "title")}
            )
            self._next_item_id += 1
            self.queue.append(q_item)
            added += 1

        if added:
            self._log_event(f"Enqueued {added} items. (Total: {len(self.queue)})")
        return added

    def next_item(self) -> Optional[OmniQueueItem]:
        """Pops the next item and sets it to ACTIVE."""
        current = self.get_current()
        if current:
            # If next is called without committing the current item, auto-fail it.
            current.status = ItemStatus.FAILED
            current.error = "Auto-failed: next() called before commit/skip."
            self.current_index = None

        for i, item in enumerate(self.queue):
            if item.status == ItemStatus.PENDING:
                item.status = ItemStatus.ACTIVE
                item.attempts += 1
                self.current_index = i
                self.visited_targets.add(item.target)
                self._log_event(f"Processing Item #{item.id}: {item.title or item.target}")
                return item
        return None

    def get_current(self) -> Optional[OmniQueueItem]:
        if self.current_index is not None and 0 <= self.current_index < len(self.queue):
            item = self.queue[self.current_index]
            if item.status == ItemStatus.ACTIVE:
                return item
        return None

    # --- CONFIDENCE-GATED COMMIT ---

    def commit_current(self, data: Dict[str, Any], confidence: int, missing_fields: Optional[List[str]] = None) -> str:
        """
        Level 4.5 Self-Healing Gate. Rejects completion if confidence < 85%.
        """
        item = self.get_current()
        if not item:
            return "ERROR: No active item in the queue. Use `scratchpad_next` first."

        # THE GATE
        if confidence < 85:
            item.attempts += 1
            reason = f"Missing fields: {', '.join(missing_fields)}" if missing_fields else "General low confidence."
            log.warning(f"Self-Heal Triggered: Item #{item.id} rejected. Confidence: {confidence}%. {reason}")
            
            return (
                f"ACTION REJECTED. Your confidence score ({confidence}%) is below the 85% threshold.\n"
                f"Reason: {reason}\n"
                f"Do NOT complete this item yet. You must dig deeper (e.g., scroll, click 'More Info', use visual analysis) "
                f"to find the data. If the data absolutely does not exist, use the `scratchpad_skip` tool."
            )

        # ACCEPTED
        item.status = ItemStatus.DONE
        item.data.update(data)
        item.confidence = confidence
        
        # Build unified record
        record = {"_item_id": item.id, "_title": item.title, "_target": item.target}
        record.update(item.data)
        self.collected_data.append(record)

        self._log_event(f"Item #{item.id} COMMITTED. (Confidence: {confidence}%)")
        self.current_index = None
        return "SUCCESS: Item committed to Ledger. EPISODE COMPLETE. Call `scratchpad_next` to begin next item."

    def skip_current(self, reason: str, confidence: int) -> str:
        """Allows skipping an item if the agent is confident it's a dead end."""
        item = self.get_current()
        if not item:
            return "ERROR: No active item."

        item.status = ItemStatus.SKIPPED
        item.error = reason
        item.confidence = confidence
        self._log_event(f"Item #{item.id} SKIPPED. ({reason})")
        self.current_index = None
        return "SUCCESS: Item skipped. EPISODE COMPLETE. Call `scratchpad_next` to begin next item."

    def direct_save(self, data: Dict[str, Any], confidence: int) -> str:
        """Used for Shallow Bulk tasks where the queue is bypassed."""
        if confidence < 85:
            return f"ACTION REJECTED. Confidence ({confidence}%) too low. Verify the data."
        self.collected_data.append(data)
        return f"SUCCESS: Data saved. Total collected: {len(self.collected_data)}"

    # --- HUD EXPORTS ---

    @property
    def metrics(self) -> Dict[str, int]:
        total = len(self.queue)
        done = sum(1 for i in self.queue if i.status == ItemStatus.DONE)
        skipped = sum(1 for i in self.queue if i.status == ItemStatus.SKIPPED)
        failed = sum(1 for i in self.queue if i.status == ItemStatus.FAILED)
        pending = sum(1 for i in self.queue if i.status == ItemStatus.PENDING)
        return {"total": total, "done": done, "skipped": skipped, "failed": failed, "pending": pending}

    def _log_event(self, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.workflow_notes.append(f"[{ts}] {text}")
        if len(self.workflow_notes) > 20:
            self.workflow_notes = self.workflow_notes[-15:]