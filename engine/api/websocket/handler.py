# FILE: api/websocket/handler.py
"""
WebSocket handler — main communication channel between Electron and engine.

Routes incoming messages to the agent system and streams responses back.
Uses the EngineEvent protocol for all UI updates.
"""

import json
import logging
import asyncio
import jwt
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
from core.config.settings import get_settings
from core.memory.state_manager import StateManager

log = logging.getLogger(__name__)

ws_manager = ConnectionManager()

# Cache for session-specific agents
_session_planners = {}
_browser = None
_os_agent = None

def _get_session_planner(session_id: str):
    """Get or create a Planner agent for a specific session."""
    if session_id not in _session_planners:
        from agents.planner.agent import PlannerAgent
        state_mgr = StateManager(session_id=session_id)
        _session_planners[session_id] = PlannerAgent(state_manager=state_mgr)
    return _session_planners[session_id]


def _get_browser():
    """Lazy-init the Browser agent."""
    global _browser
    if _browser is None:
        from agents.browser.agent import BrowserAgent
        _browser = BrowserAgent()
    return _browser


def _get_os_agent():
    """Lazy-init the OS agent."""
    global _os_agent
    if _os_agent is None:
        from agents.os.agent import OSAgent
        _os_agent = OSAgent()
    return _os_agent


async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections from Electron main process."""
    # Auth verification
    token = websocket.query_params.get("token") or websocket.headers.get("authorization")
    if token and " " in token:
        token = token.split(" ")[1]
    
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    try:
        settings = get_settings()
        jwt.decode(token, settings.better_auth_secret, algorithms=["HS256"])
    except Exception as e:
        await websocket.close(code=4002, reason=f"Invalid token: {str(e)}")
        return

    await ws_manager.connect(websocket)
    log.info("WebSocket client connected (Authenticated)")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Run message handling in background task so we don't block receiving
                # especially for 'cancel' messages
                asyncio.create_task(handle_message(websocket, message))
            except json.JSONDecodeError:
                await websocket.send_json(
                    ErrorEvent(
                        code="VALIDATION",
                        message="Invalid JSON payload",
                    ).model_dump()
                )
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        log.info("WebSocket client disconnected")
    except Exception as e:
        log.error(f"WebSocket processing error: {e}", exc_info=True)
        ws_manager.disconnect(websocket)


async def handle_message(websocket: WebSocket, message: dict):
    """Route incoming messages via their 'type' field."""
    msg_type = message.get("type")
    log.info(f"Received WebSocket message: type={msg_type}")

    if msg_type == "ping":
        await websocket.send_json(
            PongEvent(timestamp=message.get("timestamp", 0)).model_dump()
        )

    elif msg_type == "chat":
        log.info(f"Routing to handle_chat: {len(str(message.get('content', '')))} chars")
        await handle_chat(websocket, message)

    elif msg_type == "task":
        target = message.get("targetAgent") or message.get("payload", {}).get("targetAgent")
        if target == "browser":
            await handle_agent_task(websocket, message, _get_browser)
        elif target == "os":
            await handle_agent_task(websocket, message, _get_os_agent)
        else:
            await handle_chat(websocket, message)

    elif msg_type == "get_sessions":
        from core.session.manager import SessionManager
        sm = SessionManager()
        user_id = message.get("userId", "default")
        sessions = await sm.list_all(user_id)
        await websocket.send_json({
            "type": "sync_sessions",
            "sessions": sessions
        })

    elif msg_type == "get_messages":
        from core.session.manager import SessionManager
        sm = SessionManager()
        session_id = message.get("sessionId")
        if session_id:
            session = await sm.get(session_id)
            messages = session.get("messages", []) if session else []
            await websocket.send_json({
                "type": "sync_messages",
                "sessionId": session_id,
                "messages": messages
            })
            
    elif msg_type == "delete_session":
        from core.session.manager import SessionManager
        sm = SessionManager()
        session_id = message.get("sessionId")
        if session_id:
            await sm.delete(session_id)
            await websocket.send_json({
                "type": "session_deleted",
                "sessionId": session_id
            })

    elif msg_type == "cancel":

        session_id = message.get("sessionId")
        task_id = message.get("taskId")
        key = task_id or session_id or "default"
        
        log.info(f"Cancel requested for key: {key}")
        cancelled = await ws_manager.cancel_task(websocket, key)
        
        if cancelled:
            await websocket.send_json(
                DoneEvent(
                    sessionId=session_id,
                    taskId=task_id,
                    success=False,
                ).model_dump()
            )
        else:
            log.warning(f"No active task found to cancel for key: {key}")

    else:
        await websocket.send_json(
            ErrorEvent(
                code="UNKNOWN_TYPE",
                message=f"Unknown message type: {msg_type}",
            ).model_dump()
        )


async def handle_chat(websocket: WebSocket, message: dict):
    """
    Handle a chat message — executes in a managed background task.
    """
    session_id = message.get("sessionId", "default")
    
    # Define the actual work
    async def chat_task():
        try:
            await _run_chat_stream(websocket, message)
        except asyncio.CancelledError:
            log.info(f"Chat task cancelled for session: {session_id}")
            # Ensure client knows it's done (already cancelled)
            try:
                await websocket.send_json(
                    DoneEvent(sessionId=session_id, success=False).model_dump()
                )
            except: pass
        finally:
            ws_manager.unregister_task(websocket, session_id)

    task = asyncio.create_task(chat_task())
    ws_manager.register_task(websocket, session_id, task)


async def _run_chat_stream(websocket: WebSocket, message: dict):
    """Internal helper to stream the chat logic."""
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

    # Ensure session exists in DB
    from core.session.manager import SessionManager
    session_mgr = SessionManager()
    
    # Simple check/create logic for "first message" session creation
    existing = await session_mgr.get(session_id)
    if not existing:
        log.info(f"Creating new session on first message: {session_id}")
        await session_mgr.db.create_session(
            session_id=session_id,
            title=content[:30] + "..." if len(content) > 30 else content,
            user_id="default" # Could be extracted from JWT if needed
        )

    planner = _get_session_planner(session_id)

    try:
        messages = [{"role": "user", "content": content}]

        async for event in planner.stream_chat(
            messages=messages,
            session_id=session_id,
            model=model,
        ):
            await websocket.send_json(event.model_dump())

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


async def handle_agent_task(websocket: WebSocket, message: dict, agent_factory):
    """
    Handle a task message — executes in a managed background task.
    """
    task_id = message.get("taskId", "default")
    session_id = message.get("sessionId", "default")
    key = task_id or session_id

    async def run_task():
        try:
            await _run_agent_task_logic(websocket, message, agent_factory)
        except asyncio.CancelledError:
            log.info(f"Agent task cancelled: {key}")
            try:
                await websocket.send_json(
                    DoneEvent(sessionId=session_id, taskId=task_id, success=False).model_dump()
                )
            except: pass
        finally:
            ws_manager.unregister_task(websocket, key)

    task = asyncio.create_task(run_task())
    ws_manager.register_task(websocket, key, task)


async def _run_agent_task_logic(websocket: WebSocket, message: dict, agent_factory):
    """Internal helper to stream the agent task logic."""
    session_id = message.get("sessionId", "default")
    goal = message.get("content") or message.get("payload", {}).get("goal", "")
    task_id = message.get("taskId", "")

    if not goal.strip():
        await websocket.send_json(
            ErrorEvent(
                sessionId=session_id,
                code="VALIDATION",
                message="Task goal is empty",
            ).model_dump()
        )
        return

    agent = agent_factory()

    # Wire event handler to stream events to WebSocket
    async def event_handler(event_type: str, content: str):
        """Bridge between agent.emit() and WebSocket."""
        event_map = {
            "THINK": ThinkingEvent(
                sessionId=session_id, agentId=agent.agent_id, content=content,
            ),
            "ACTION": ThinkingEvent(
                sessionId=session_id, agentId=agent.agent_id,
                content=f"🔧 {content}",
            ),
            "STATUS": AgentStatusEvent(
                agentId=agent.agent_id, status="running", action=content,
            ),
            "ERROR": ErrorEvent(
                sessionId=session_id, code="AGENT_ERROR", message=content,
            ),
            "TOOL_OUTPUT": ThinkingEvent(
                sessionId=session_id, agentId=agent.agent_id,
                content=f"📋 {content}",
            ),
        }
        event = event_map.get(event_type)
        if event:
            await websocket.send_json(event.model_dump())

    agent.set_event_handler(event_handler)

    try:
        from core.protocol.messages import (
            Message, AgentType, MessageType, TaskFrame,
        )

        task_frame = TaskFrame(
            task_id=task_id,
            goal=goal,
            context=message.get("context", {}),
        )

        msg = Message.create(
            sender=AgentType.PLANNER,
            receiver=agent.agent_type,
            msg_type=MessageType.TASK,
            content=task_frame,
        )

        result = await agent.process(msg)

        # Stream the result back
        result_content = str(result.content)
        await websocket.send_json(
            ResponseEvent(
                sessionId=session_id,
                agentId=agent.agent_id,
                content=result_content,
                isStreaming=False,
            ).model_dump()
        )

        success = result.type != MessageType.ERROR
        await websocket.send_json(
            DoneEvent(
                sessionId=session_id,
                taskId=task_id,
                success=success,
            ).model_dump()
        )

    except Exception as e:
        log.error(f"Agent task error: {e}", exc_info=True)
        await websocket.send_json(
            ErrorEvent(
                sessionId=session_id,
                code="AGENT_ERROR",
                message=str(e),
            ).model_dump()
        )
        await websocket.send_json(
            DoneEvent(
                sessionId=session_id,
                taskId=task_id,
                success=False,
            ).model_dump()
        )
