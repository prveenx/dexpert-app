# FILE: core/scratchpad.py
"""
Per-task reasoning store — volatile working memory for specialist agents.

Adapted from PCAgent MAF core/scratchpad.py.
Persists across steps within a single task but is cleared between tasks.

Supports:
  - Generic item queue (URL + title + metadata) with dedup and status tracking
  - Phase-aware state machine (idle → gather → process → report)
  - Position tracker (knows "item 3 of 10, page 2")
  - Loop detection (breaks infinite action loops)
  - Per-item data store
  - Compact progress summary for LLM prompt injection
"""

from typing import Dict, List, Any, Optional, Set
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

import logging

log = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"


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


class QueueItem(BaseModel):
    """Single item in the processing queue."""
    id: int = 0
    title: str = ""
    url: str = ""
    status: ItemStatus = ItemStatus.PENDING
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    attempts: int = 0
    added_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    model_config = ConfigDict(extra="ignore")


class Scratchpad(BaseModel):
    """
    Volatile working memory for specialist agents.

    Simple Task: gather → report
    Complex Task: gather → process → report
    """

    # --- Task context ---
    task_id: Optional[str] = None
    goal: str = ""
    task_type: TaskComplexity = TaskComplexity.SIMPLE
    phase: WorkflowPhase = WorkflowPhase.IDLE
    target_count: Optional[int] = None

    # --- URL/Item Queue ---
    queue: List[QueueItem] = Field(default_factory=list)
    current_index: Optional[int] = None
    _next_item_id: int = 1

    # --- Data Collection ---
    collected_data: List[Dict[str, Any]] = Field(default_factory=list)
    notes: str = ""

    # --- Loop Detection ---
    visited_urls: Set[str] = Field(default_factory=set)
    _action_history: List[str] = []
    _loop_threshold: int = 3

    # --- Pagination ---
    current_page: int = 1
    total_pages: Optional[int] = None

    # --- Workflow Metadata ---
    source_url: Optional[str] = None
    workflow_notes: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")

    def init_workflow(
        self,
        task_id: str,
        goal: str,
        task_type: str = "simple",
        target_count: Optional[int] = None,
        source_url: Optional[str] = None,
    ) -> None:
        """Initialize for a new workflow."""
        self.reset()
        self.task_id = task_id
        self.goal = goal
        self.task_type = (
            TaskComplexity(task_type) if isinstance(task_type, str) else task_type
        )
        self.target_count = target_count
        self.source_url = source_url
        self.phase = WorkflowPhase.GATHER
        self._log_event(f"Workflow initialized: {task_type} | target={target_count}")

    def transition_to(self, phase: WorkflowPhase) -> str:
        """Explicit phase transition with validation."""
        old_phase = self.phase
        valid_transitions = {
            WorkflowPhase.IDLE: [WorkflowPhase.GATHER],
            WorkflowPhase.GATHER: [WorkflowPhase.PROCESS, WorkflowPhase.REPORT],
            WorkflowPhase.PROCESS: [WorkflowPhase.REPORT, WorkflowPhase.GATHER],
            WorkflowPhase.REPORT: [WorkflowPhase.IDLE],
        }

        if phase not in valid_transitions.get(old_phase, []):
            msg = f"Invalid transition: {old_phase} -> {phase}"
            log.warning(f"Scratchpad: {msg}")
            return msg

        self.phase = phase
        self._log_event(f"Phase: {old_phase.value} -> {phase.value}")
        return f"OK: Phase is now '{phase.value}'"

    def reset(self) -> None:
        """Clear everything — called between tasks."""
        self.task_id = None
        self.goal = ""
        self.task_type = TaskComplexity.SIMPLE
        self.phase = WorkflowPhase.IDLE
        self.target_count = None
        self.queue = []
        self.current_index = None
        self._next_item_id = 1
        self.collected_data = []
        self.notes = ""
        self.visited_urls = set()
        self._action_history = []
        self.current_page = 1
        self.total_pages = None
        self.source_url = None
        self.workflow_notes = []

    def enqueue_items(self, items: List[Dict[str, Any]]) -> int:
        """Add items to the queue with dedup. Returns count added."""
        existing_urls = {item.url for item in self.queue if item.url}
        existing_titles = {
            item.title for item in self.queue if item.title and not item.url
        }
        added = 0

        for raw in items:
            url = raw.get("url", "").strip()
            title = raw.get("title", "").strip()

            if url:
                if url in existing_urls or url in self.visited_urls:
                    continue
                existing_urls.add(url)
            elif title:
                if title in existing_titles:
                    continue
                existing_titles.add(title)
            else:
                continue

            q_item = QueueItem(
                id=self._next_item_id,
                title=title,
                url=url,
                data={k: v for k, v in raw.items() if k not in ("url", "title")},
            )
            self._next_item_id += 1
            self.queue.append(q_item)
            added += 1

        if added:
            self._log_event(f"Enqueued {added} items (total: {len(self.queue)})")
        return added

    def next(self) -> Optional[QueueItem]:
        """Get the next pending item and mark it as active."""
        current = self.get_current()
        if current:
            current.status = ItemStatus.FAILED
            current.error = "Auto-failed: next() called without complete/fail"
            self.current_index = None

        for i, item in enumerate(self.queue):
            if item.status == ItemStatus.PENDING:
                item.status = ItemStatus.ACTIVE
                item.attempts += 1
                self.current_index = i
                if item.url:
                    self.visited_urls.add(item.url)
                self._log_event(
                    f"Processing #{item.id}: {item.title or item.url}"
                )
                return item
        return None

    def get_current(self) -> Optional[QueueItem]:
        """Returns the currently active queue item."""
        if (
            self.current_index is not None
            and 0 <= self.current_index < len(self.queue)
        ):
            item = self.queue[self.current_index]
            if item.status == ItemStatus.ACTIVE:
                return item
        return None

    def complete_current(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Mark the current item as done and store extracted data."""
        item = self.get_current()
        if not item:
            return

        item.status = ItemStatus.DONE
        if data:
            item.data.update(data)
            record = {"_item_id": item.id, "_title": item.title}
            if item.url:
                record["_url"] = item.url
            record.update(data)
            self.collected_data.append(record)

        self._log_event(f"Completed #{item.id} ({self.done_count}/{len(self.queue)})")
        self.current_index = None

    def fail_current(self, error: str) -> None:
        """Mark the current item as failed."""
        item = self.get_current()
        if item:
            item.status = ItemStatus.FAILED
            item.error = error
            self._log_event(f"Failed #{item.id}: {error[:50]}")
            self.current_index = None

    def save_data(self, data: Dict[str, Any]) -> None:
        """Save data directly (not tied to a queue item). Used in SIMPLE tasks."""
        self.collected_data.append(data)

    def detect_loop(self, action_signature: str) -> bool:
        """Detects if the agent is stuck repeating the same action."""
        self._action_history.append(action_signature)
        if len(self._action_history) > 20:
            self._action_history = self._action_history[-20:]

        if len(self._action_history) >= self._loop_threshold:
            recent = self._action_history[-self._loop_threshold :]
            if len(set(recent)) == 1:
                log.warning(f"Scratchpad: Loop detected! '{action_signature}'")
                return True
        return False

    @property
    def done_count(self) -> int:
        return sum(1 for item in self.queue if item.status == ItemStatus.DONE)

    @property
    def pending_count(self) -> int:
        return sum(1 for item in self.queue if item.status == ItemStatus.PENDING)

    @property
    def is_queue_exhausted(self) -> bool:
        return self.pending_count == 0 and len(self.queue) > 0

    def progress_summary(self) -> str:
        """Compact status string for LLM prompt injection."""
        lines = [f"=== SCRATCHPAD STATUS ==="]
        lines.append(f"Task Type: {self.task_type.value}")
        lines.append(f"Phase: {self.phase.value}")

        if self.target_count:
            lines.append(
                f"Target: {self.target_count} items | Collected: {len(self.collected_data)}"
            )
        if self.queue:
            lines.append(
                f"Queue: {self.done_count} done / {self.pending_count} pending"
            )

        current = self.get_current()
        if current:
            label = current.title or current.url or f"Item #{current.id}"
            lines.append(f"Active Target: {label} (attempt #{current.attempts})")

        return "\n".join(lines)

    def _log_event(self, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.workflow_notes.append(f"[{ts}] {text}")
        if len(self.workflow_notes) > 30:
            self.workflow_notes = self.workflow_notes[-20:]
