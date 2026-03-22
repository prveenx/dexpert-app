"""
Session Manager — lifecycle management for sessions.
"""

from typing import Optional
import uuid
from datetime import datetime


class SessionManager:
    """Manages session lifecycle: create, resume, pause, archive."""

    def __init__(self):
        self.sessions: dict[str, dict] = {}

    async def create(self, title: str = "New Session") -> dict:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        session = {
            "id": session_id,
            "title": title,
            "createdAt": now,
            "updatedAt": now,
            "isActive": True,
            "messageCount": 0,
            "messages": [],
        }
        self.sessions[session_id] = session
        return session

    async def get(self, session_id: str) -> Optional[dict]:
        return self.sessions.get(session_id)

    async def list_all(self) -> list[dict]:
        return list(self.sessions.values())

    async def delete(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    async def add_message(self, session_id: str, message: dict) -> None:
        session = self.sessions.get(session_id)
        if session:
            session["messages"].append(message)
            session["messageCount"] = len(session["messages"])
            session["updatedAt"] = datetime.utcnow().isoformat()
