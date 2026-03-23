"""
Session History — manages message appends and retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
from core.memory.database import Database

log = logging.getLogger(__name__)


class HistoryManager:
    """Per-session message history manager backed by SQLite."""

    def __init__(self):
        self.db = Database()

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sender: str = "assistant",
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a message to a session's history (persisted)."""
        # Note: metadata is not currently stored in interaction_log, 
        # but could be serialized into content or a separate table if needed.
        await self.db.log_interaction(session_id, role, sender, content)
        
        return {
            "role": role,
            "sender": sender,
            "content": content,
            "agent_id": agent_id,
        }

    async def get_messages(
        self, session_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get messages for a session from the database."""
        return await self.db.get_recent_interactions(session_id, limit=limit)

    async def get_llm_messages(
        self, session_id: str, limit: int = 20
    ) -> List[Dict[str, str]]:
        """Get messages in LLM-compatible format (role + content only)."""
        messages = await self.get_messages(session_id, limit)
        result = []
        for msg in messages:
            role = msg["role"]
            # Normalize roles for LLM
            if role.lower() in ("user",):
                llm_role = "user"
            elif role.lower() in ("assistant", "planner", "agent"):
                llm_role = "assistant"
            else:
                continue
            result.append({"role": llm_role, "content": msg["content"]})
        return result

    async def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session (soft delete via DB)."""
        # In current DB it's harder to soft-delete interactions only, 
        # so for now we leave them as they are or we could add a clear_interactions method.
        pass

    async def get_message_count(self, session_id: str) -> int:
        messages = await self.get_messages(session_id)
        return len(messages)
