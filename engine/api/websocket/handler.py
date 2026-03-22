# FILE: api/websocket/handler.py
"""
WebSocket handler — main communication channel between Electron and engine.

Routes incoming messages to the agent system and streams responses back.
Uses the EngineEvent protocol for all UI updates.
"""

import json
import asyncio
import logging
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from api.websocket.manager import ConnectionManager
from core.protocol.events import (
    ThinkingEvent,
    ResponseEvent,
    AgentStatusEvent,
    DoneEvent,
    ErrorEvent,
    PongEvent,
)
from core.config.settings import DexpertSettings
from agents.planner.agent import PlannerAgent

log = logging.getLogger(__name__)

manager = ConnectionManager()
_planner: Optional[PlannerAgent] = None


def _get_planner() -> PlannerAgent:
    """Lazy-init the Planner agent."""
    global _planner
    if _planner is None:
        settings = DexpertSettings()
        _planner = PlannerAgent(config=settings.planner, globals=settings)
    return _planner


async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections from Electron main process."""
    await manager.connect(websocket)
    log.info("WebSocket client connected")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_message(websocket, message)
            except json.JSONDecodeError:
                await websocket.send_json(
                    ErrorEvent(
                        code="VALIDATION",
                        message="Invalid JSON payload",
                    ).model_dump()
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        log.info("WebSocket client disconnected")
    except Exception as e:
        log.error(f"WebSocket processing error: {e}", exc_info=True)
        manager.disconnect(websocket)


async def handle_message(websocket: WebSocket, message: dict):
    """Route incoming messages via their 'type' field."""
    msg_type = message.get("type")

    if msg_type == "ping":
        await websocket.send_json(
            PongEvent(timestamp=message.get("timestamp", 0)).model_dump()
        )

    elif msg_type == "chat":
        await handle_chat(websocket, message)

    elif msg_type == "task":
        # MVP: Task currently routes through conversational planner
        # In Phase 2, this will use task-specific logic (execute)
        await handle_chat(websocket, message)

    elif msg_type == "cancel":
        # Cancellation support will be added in Phase 2
        pass

    else:
        await websocket.send_json(
            ErrorEvent(
                code="UNKNOWN_TYPE",
                message=f"Unknown message type: {msg_type}",
            ).model_dump()
        )


async def handle_chat(websocket: WebSocket, message: dict):
    """
    Handle a chat/task message — stream full EngineEvent protocol.
    """
    session_id = message.get("sessionId", "default")
    content = message.get("content") or message.get("payload", {}).get("goal", "")
    model = message.get("model")

    if not content.strip():
        await websocket.send_json(
            ErrorEvent(
                sessionId=session_id,
                code="VALIDATION",
                message="Message content is empty",
            ).model_dump()
        )
        return

    planner = _get_planner()

    try:
        # Simple history — MVP for Phase 1
        messages = [{"role": "user", "content": content}]

        # Planner now yields EngineEvent objects directly!
        async for event in planner.stream_chat(
            messages=messages,
            session_id=session_id,
            model=model,
        ):
            await websocket.send_json(event.model_dump())

        # Finalize the turn in UI
        await websocket.send_json(
            DoneEvent(
                sessionId=session_id,
                success=True,
            ).model_dump()
        )

    except Exception as e:
        log.error(f"Chat stream processing error: {e}", exc_info=True)
        await websocket.send_json(
            ErrorEvent(
                sessionId=session_id,
                code="STREAM_ERROR",
                message=str(e),
            ).model_dump()
        )
        await websocket.send_json(
            DoneEvent(
                sessionId=session_id,
                success=False,
            ).model_dump()
        )
