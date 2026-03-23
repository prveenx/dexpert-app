"""
State Manager — session-scoped state for agents.

Adapter that wraps core.session and core.memory.database for
the PCAgent-style StateManager API expected by the Planner agent.
"""

import logging
from typing import List, Dict, Any, Optional

from core.memory.database import Database

log = logging.getLogger(__name__)


class StateManager:
    """
    Session-scoped state manager.

    Provides the interface the PCAgent planner agent expects:
      - session_id tracking
      - get_recent_interactions() for chat history
      - add_interaction() for recording messages
      - save/load checkpoint via DB workflow state
    """

    def __init__(self, session_id: str = "global", db_path: str = "runtime/memory.db"):
        self.session_id = session_id
        self._interactions: List[Dict[str, str]] = []
        self._db = Database(db_path)
        self.is_resume = False
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Lazy-connect to database on first use."""
        if not self._initialized:
            await self._db.connect()
            self._initialized = True

    async def get_recent_interactions(self, limit: int = 15) -> List[Dict[str, str]]:
        """Get recent chat interactions for the session."""
        await self._ensure_initialized()
        if self._interactions:
            return self._interactions[-limit:]
        return await self._db.get_recent_interactions(self.session_id, limit)

    async def add_interaction(self, role: str, content: str) -> None:
        """Record an interaction."""
        await self._ensure_initialized()
        self._interactions.append({"role": role, "content": content})
        await self._db.log_interaction(
            session_id=self.session_id,
            role=role,
            sender=role,
            content=content,
        )

    async def save_checkpoint(self, data: dict) -> None:
        """Save checkpoint data for the session."""
        await self._ensure_initialized()
        try:
            await self._db.save_workflow_state(
                task_id=self.session_id,
                agent="planner",
                state_dict=data,
            )
        except Exception as e:
            log.warning(f"Failed to save checkpoint: {e}")

    async def load_checkpoint(self) -> Optional[dict]:
        """Load checkpoint data for the session."""
        await self._ensure_initialized()
        try:
            return await self._db.load_workflow_state(self.session_id)
        except Exception:
            return None

    def clear(self) -> None:
        """Clear interaction history."""
        self._interactions.clear()

    async def close(self) -> None:
        """Close database connection."""
        if self._initialized:
            await self._db.close()
