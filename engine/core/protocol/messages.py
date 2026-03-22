# FILE: core/protocol/messages.py
"""
Pydantic message schemas matching @dexpert/types.

Adapted from PCAgent MAF core/protocol.py.
These are the internal message types used by the agent runtime.
"""

import uuid
from enum import Enum
from typing import Any, Dict, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Identifies which agent sent/receives a message."""
    USER = "user"
    PLANNER = "planner"
    BROWSER = "browser"
    OS = "os"


class MessageType(str, Enum):
    """Internal message types for agent-to-agent communication."""
    TASK = "task"           # Instruction to do work (Planner → Specialist)
    RESULT = "result"       # Successful completion (Specialist → Planner)
    ERROR = "error"         # Fatal failure (Specialist → Planner)
    INFO = "info"           # Non-blocking updates/logs
    CHAT = "chat"           # Pure conversation
    QUESTION = "question"   # Specialist needs info from Planner/User


class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    SUCCESS = "success"
    FAILURE = "failure"


class TaskFrame(BaseModel):
    """The 'Directive' sent to a specialist agent."""
    task_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    goal: str = Field(..., description="The specific outcome required.")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata like current URL or credentials.",
    )


class ResultFrame(BaseModel):
    """The 'Report' returned by a specialist agent."""
    task_id: str
    status: AgentStatus
    summary: str = Field(..., description="Human-readable summary of what was achieved.")
    artifacts: Dict[str, Any] = Field(
        default_factory=dict,
        description="Data found, file paths, or screenshots.",
    )


class QuestionFrame(BaseModel):
    """Payload when an agent is blocked and needs info."""
    task_id: str
    question: str
    context_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Serialized state (scratchpad, history) to resume later.",
    )


class Message(BaseModel):
    """The envelope for all internal MAF communication."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    sender: AgentType
    receiver: AgentType
    type: MessageType
    content: Union[str, TaskFrame, ResultFrame, QuestionFrame, Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        sender: AgentType,
        receiver: AgentType,
        msg_type: MessageType,
        content: Any,
    ) -> "Message":
        return cls(sender=sender, receiver=receiver, type=msg_type, content=content)


# --- WS-facing schemas (for the client ↔ engine messages) ---

class ClientChatMessage(BaseModel):
    """What the frontend sends when user types a message."""
    sessionId: str
    content: str
    model: Optional[str] = None
    targetAgent: Optional[str] = None


class ClientTaskMessage(BaseModel):
    """What the frontend sends for a task request."""
    taskId: str
    sessionId: str
    goal: str
    context: Optional[str] = None
    targetAgent: Optional[str] = None
    parentTaskId: Optional[str] = None


class ClientCancelMessage(BaseModel):
    """What the frontend sends to cancel a running task."""
    taskId: str
