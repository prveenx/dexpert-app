from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
from core.memory.database import Database


class SessionManager:
    """Manages session lifecycle with persistent SQLite backing."""

    def __init__(self):
        self.db = Database()

    async def create(self, user_id: str, title: str = "New Session") -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        await self.db.create_session(session_id, title, user_id=user_id)
        
        # Return a consistent schema
        return {
            "id": session_id,
            "title": title,
            "isActive": True,
            "messages": []
        }

    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = await self.db.get_session(session_id)
        if not session:
            return None
        
        # Load messages
        messages = await self.db.get_recent_interactions(session_id, limit=100)
        session["messages"] = messages
        session["messageCount"] = len(messages)
        return session

    async def list_all(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.db.list_sessions(user_id=user_id)

    async def delete(self, session_id: str) -> bool:
        session = await self.db.get_session(session_id)
        if session:
            await self.db.delete_session(session_id)
            return True
        return False

    async def add_message(self, session_id: str, role: str, content: str, sender: str = "system") -> None:
        await self.db.log_interaction(session_id, role, sender, content)
        await self.db.update_session_timestamp(session_id)
