import asyncio
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and their associated tasks."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        # websocket -> {task_id/session_id: asyncio.Task}
        self.active_tasks: dict[WebSocket, dict[str, asyncio.Task]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.active_tasks[websocket] = {}

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Cancel all tasks for this connection
        if websocket in self.active_tasks:
            for task in self.active_tasks[websocket].values():
                task.cancel()
            del self.active_tasks[websocket]

    def register_task(self, websocket: WebSocket, task_key: str, task: asyncio.Task):
        """Register a running task for potential cancellation."""
        if websocket in self.active_tasks:
            # Cancel existing task for this key if it exists
            if task_key in self.active_tasks[websocket]:
                self.active_tasks[websocket][task_key].cancel()
            self.active_tasks[websocket][task_key] = task

    def unregister_task(self, websocket: WebSocket, task_key: str):
        """Remove task from registry when finished."""
        if websocket in self.active_tasks and task_key in self.active_tasks[websocket]:
            del self.active_tasks[websocket][task_key]

    async def cancel_task(self, websocket: WebSocket, task_key: str):
        """Explicitly cancel a specific task."""
        if websocket in self.active_tasks and task_key in self.active_tasks[websocket]:
            task = self.active_tasks[websocket][task_key]
            task.cancel()
            del self.active_tasks[websocket][task_key]
            return True
        return False

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

    async def send_to(self, websocket: WebSocket, message: dict):
        """Send message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)
