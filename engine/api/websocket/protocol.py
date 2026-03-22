"""
WebSocket protocol models matching @dexpert/types exactly.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel


class MessageType(str, Enum):
    TASK = "task"
    CHAT = "chat"
    CANCEL = "cancel"
    PING = "ping"


class EventType(str, Enum):
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    RESPONSE = "response"
    AGENT_STATUS = "agent_status"
    DONE = "done"
    ERROR = "error"
    PONG = "pong"
    TOKEN_USAGE = "token_usage"
    SCREENSHOT = "screenshot"


class AgentId(str, Enum):
    PLANNER = "planner"
    BROWSER = "browser"
    OS = "os"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"
