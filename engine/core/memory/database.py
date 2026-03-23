# FILE: core/memory/database.py
"""
SQLite operations for persistent storage.

Provides async database operations for:
  - Knowledge store (user facts, preferences)
  - Task log (audit trail)
  - Interaction log (conversation history)
  - Workflow state (scratchpad persistence)
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import aiosqlite
from core.config.settings import get_settings

log = logging.getLogger(__name__)

class Database:
    """Async SQLite database wrapper."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = get_settings().db_path
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Initialize database connection and schema."""
        async with self._lock:
            if self._conn is not None:
                return

            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            self._conn = await aiosqlite.connect(self.db_path)
            await self._init_schema()
            log.info(f"Database connected: {self.db_path}")

    async def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS knowledge (
                key TEXT PRIMARY KEY,
                value TEXT,
                category TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS task_log (
                task_id TEXT,
                agent TEXT,
                goal TEXT,
                result TEXT,
                status TEXT DEFAULT 'success',
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS interaction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                sender TEXT,
                content TEXT,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                user_id TEXT,
                sync_id TEXT,
                created_at TEXT,
                updated_at TEXT,
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS workflow_state (
                task_id TEXT PRIMARY KEY,
                agent TEXT,
                state_json TEXT,
                updated_at TEXT
            );
        """)
        await self._conn.commit()

    async def _get_conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            await self.connect()
        assert self._conn is not None
        return self._conn

    # ─── Knowledge (Facts) ───────────────────────────────────

    async def learn_fact(self, key: str, value: str, category: str = "general") -> None:
        conn = await self._get_conn()
        await conn.execute(
            "INSERT OR REPLACE INTO knowledge (key, value, category, updated_at) VALUES (?, ?, ?, ?)",
            (key, value, category, datetime.now().isoformat()),
        )
        await conn.commit()

    async def get_all_facts(self) -> List[Dict[str, str]]:
        conn = await self._get_conn()
        async with conn.execute("SELECT key, value, category FROM knowledge") as cursor:
            rows = await cursor.fetchall()
        return [{"key": r[0], "value": r[1], "category": r[2]} for r in rows]

    async def delete_fact(self, key: str) -> None:
        conn = await self._get_conn()
        await conn.execute("DELETE FROM knowledge WHERE key = ?", (key,))
        await conn.commit()

    async def clear_all_facts(self) -> None:
        conn = await self._get_conn()
        await conn.execute("DELETE FROM knowledge")
        await conn.commit()

    # ─── Sessions ────────────────────────────────────────────

    async def create_session(self, session_id: str, title: str, user_id: str = "default") -> None:
        conn = await self._get_conn()
        now = datetime.now().isoformat()
        await conn.execute(
            "INSERT INTO sessions (id, title, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, title, user_id, now, now),
        )
        await conn.commit()

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        conn = await self._get_conn()
        async with conn.execute(
            "SELECT id, title, user_id, created_at, updated_at, is_active FROM sessions WHERE id = ?",
            (session_id,),
        ) as cursor:
            row = await cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "title": row[1],
                "user_id": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "is_active": bool(row[5]),
            }
        return None

    async def list_sessions(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        conn = await self._get_conn()
        query = "SELECT id, title, user_id, created_at, updated_at, is_active FROM sessions"
        params: List[Any] = []
        
        if user_id:
            query += " WHERE user_id = ?"
            params.append(user_id)
            
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        async with conn.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "title": r[1],
                "user_id": r[2],
                "created_at": r[3],
                "updated_at": r[4],
                "is_active": bool(r[5]),
            }
            for r in rows
        ]

    async def delete_session(self, session_id: str) -> None:
        conn = await self._get_conn()
        await conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await conn.execute("DELETE FROM interaction_log WHERE session_id = ?", (session_id,))
        await conn.commit()

    async def update_session_timestamp(self, session_id: str) -> None:
        conn = await self._get_conn()
        await conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), session_id),
        )
        await conn.commit()

    # ─── Interaction Log ─────────────────────────────────────

    async def log_interaction(
        self, session_id: str, role: str, sender: str, content: str
    ) -> None:
        conn = await self._get_conn()
        await conn.execute(
            "INSERT INTO interaction_log (session_id, role, sender, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, sender, str(content), datetime.now().isoformat()),
        )
        await conn.commit()

    async def get_recent_interactions(
        self, session_id: str, limit: int = 15
    ) -> List[Dict[str, str]]:
        conn = await self._get_conn()
        async with conn.execute(
            "SELECT role, sender, content, timestamp FROM interaction_log "
            "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [
            {"role": r[0], "sender": r[1], "content": r[2], "timestamp": r[3]}
            for r in reversed(rows)
        ]

    # ─── Task Log ────────────────────────────────────────────

    async def log_task(
        self,
        task_id: str,
        agent: str,
        goal: str,
        result: str,
        status: str = "success",
    ) -> None:
        conn = await self._get_conn()
        await conn.execute(
            "INSERT INTO task_log VALUES (?, ?, ?, ?, ?, ?)",
            (task_id, agent, goal, result, status, datetime.now().isoformat()),
        )
        await conn.commit()

    async def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, str]]:
        conn = await self._get_conn()
        async with conn.execute(
            "SELECT task_id, agent, goal, result, status, timestamp "
            "FROM task_log ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [
            {
                "task_id": r[0],
                "agent": r[1],
                "goal": r[2],
                "result": r[3],
                "status": r[4],
                "timestamp": r[5],
            }
            for r in rows
        ]

    # ─── Workflow State ──────────────────────────────────────

    async def save_workflow_state(
        self, task_id: str, agent: str, state_dict: Dict[str, Any]
    ) -> None:
        state_json = json.dumps(state_dict, default=str)
        conn = await self._get_conn()
        await conn.execute(
            "INSERT OR REPLACE INTO workflow_state VALUES (?, ?, ?, ?)",
            (task_id, agent, state_json, datetime.now().isoformat()),
        )
        await conn.commit()

    async def load_workflow_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        conn = await self._get_conn()
        async with conn.execute(
            "SELECT state_json FROM workflow_state WHERE task_id = ?", (task_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    # ─── Lifecycle ───────────────────────────────────────────

    async def close(self) -> None:
        async with self._lock:
            if self._conn is not None:
                await self._conn.close()
                self._conn = None
                log.info("Database connection closed")
