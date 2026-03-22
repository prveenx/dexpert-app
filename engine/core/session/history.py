# FILE: core/session/history.py
"""
Session History — manages message appends and retrieval.

Wraps the in-memory session store with conversation-aware operations.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

log = logging.getLogger(__name__)


class MessageStore:
    """Per-session message history manager."""

    def __init__(self):
        self._messages: Dict[str, List[Dict[str, Any]]] = {}

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a message to a session's history."""
        if session_id not in self._messages:
            self._messages[session_id] = []

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        if agent_id:
            message["agentId"] = agent_id
        if metadata:
            message["metadata"] = metadata

        self._messages[session_id].append(message)
        return message

    def get_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get messages for a session, optionally limited."""
        messages = self._messages.get(session_id, [])
        if limit:
            return messages[-limit:]
        return messages

    def get_llm_messages(
        self, session_id: str, limit: int = 20
    ) -> List[Dict[str, str]]:
        """Get messages in LLM-compatible format (role + content only)."""
        messages = self.get_messages(session_id, limit)
        result = []
        for msg in messages:
            role = msg["role"]
            # Normalize roles for LLM
            if role in ("user",):
                llm_role = "user"
            elif role in ("assistant", "planner", "agent"):
                llm_role = "assistant"
            else:
                continue  # Skip system, tool, etc.
            result.append({"role": llm_role, "content": msg["content"]})
        return result

    def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session."""
        self._messages.pop(session_id, None)

    def get_message_count(self, session_id: str) -> int:
        return len(self._messages.get(session_id, []))
