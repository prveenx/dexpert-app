# FILE: core/session/checkpoint.py
"""
Session Checkpoint — serializes active tasks to disk for crash recovery.

Adapted from PCAgent MAF core/session.py SessionManager.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

log = logging.getLogger(__name__)

RUNTIME_DIR = "runtime"
CHECKPOINT_DIR = os.path.join(RUNTIME_DIR, "sessions")


class CheckpointManager:
    """Manages session checkpoints for crash recovery."""

    def __init__(self, base_dir: str = CHECKPOINT_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _checkpoint_path(self, session_id: str) -> str:
        return os.path.join(self.base_dir, f"{session_id}.checkpoint.json")

    async def save(
        self, session_id: str, state: Dict[str, Any]
    ) -> None:
        """Save a checkpoint for crash recovery."""
        path = self._checkpoint_path(session_id)
        try:
            data = {
                "session_id": session_id,
                "saved_at": datetime.now().isoformat(),
                "state": state,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            log.debug(f"Checkpoint saved: {session_id}")
        except Exception as e:
            log.error(f"Failed to save checkpoint: {e}")

    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a checkpoint if one exists."""
        path = self._checkpoint_path(session_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            log.info(f"Checkpoint loaded: {session_id}")
            return data.get("state")
        except Exception as e:
            log.error(f"Failed to load checkpoint: {e}")
            return None

    async def clear(self, session_id: str) -> None:
        """Remove a checkpoint after successful completion."""
        path = self._checkpoint_path(session_id)
        if os.path.exists(path):
            os.remove(path)
            log.debug(f"Checkpoint cleared: {session_id}")

    def list_checkpoints(self) -> list:
        """List all saved checkpoints."""
        try:
            files = os.listdir(self.base_dir)
            return [
                f.replace(".checkpoint.json", "")
                for f in files
                if f.endswith(".checkpoint.json")
            ]
        except Exception:
            return []
