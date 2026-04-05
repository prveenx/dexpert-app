# FILE: core/protocol/events.py
"""
WebSocket event schemas matching @dexpert/types EngineEvent.

These are the JSON payloads the engine sends TO the renderer via WebSocket.
"""

from __future__ import annotations
from typing import Optional, Any, Dict, List, Union
from pydantic import BaseModel


class ThinkingEvent(BaseModel):
    """Agent's inner reasoning — displayed in a collapsible ThinkingBlock."""
    type: str = "thinking"
    sessionId: str
    agentId: str
    content: str


class ResponseEvent(BaseModel):
    """Agent's final response — streamed token by token."""
    type: str = "response"
    sessionId: str
    agentId: str
    content: str
    isStreaming: bool = False


class ToolCallEvent(BaseModel):
    """Emitted when an agent starts executing a tool."""
    type: str = "tool_call"
    sessionId: str
    agentId: str
    toolName: str
    args: Dict[str, Any] = {}
    callId: Optional[str] = None


class ToolResultEvent(BaseModel):
    """Emitted when a tool execution completes."""
    type: str = "tool_result"
    sessionId: str
    agentId: str
    toolName: str
    result: str
    success: bool = True
    callId: Optional[str] = None


class AgentStatusEvent(BaseModel):
    """Agent status change — updates the agent card in the UI."""
    type: str = "agent_status"
    agentId: str
    status: str  # idle | running | error | disabled
    action: Optional[str] = None


class DoneEvent(BaseModel):
    """Task/chat completion signal."""
    type: str = "done"
    sessionId: str
    taskId: Optional[str] = None
    success: bool


class ErrorEvent(BaseModel):
    """Error event — displayed as an error banner or toast."""
    type: str = "error"
    sessionId: Optional[str] = None
    code: str
    message: str


class TokenUsageEvent(BaseModel):
    """Token usage report — updates the cost display."""
    type: str = "token_usage"
    sessionId: str
    agentId: str
    model: str
    promptTokens: int = 0
    completionTokens: int = 0
    totalTokens: int = 0
    costUsd: float = 0.0


class PongEvent(BaseModel):
    """Response to ping."""
    type: str = "pong"
    timestamp: int


class QuestionEvent(BaseModel):
    """Agent needs user input — shows inline question in chat."""
    type: str = "question"
    sessionId: str
    agentId: str
    question: str
    taskId: Optional[str] = None


class ScreenshotEvent(BaseModel):
    """Browser screenshot frame — displayed in BrowserPreview."""
    type: str = "screenshot"
    sessionId: str
    agentId: str
    imageBase64: str
    url: str = ""


class SystemNoticeEvent(BaseModel):
    """System-level notice — displayed as a SystemNotice in the chat."""
    type: str = "system_notice"
    sessionId: str
    content: str


# ── Workspace Events (v2) ──────────────────────────────

class FileCreatedEvent(BaseModel):
    """Emitted when an agent creates a new file."""
    type: str = "file_created"
    sessionId: str
    agentId: str
    filePath: str
    content: str
    language: str = "text"


class FileModifiedEvent(BaseModel):
    """Emitted when an agent modifies an existing file."""
    type: str = "file_modified"
    sessionId: str
    agentId: str
    filePath: str
    diff: str  # unified diff format
    newContent: str = ""


class TerminalOutputEvent(BaseModel):
    """Emitted when an agent executes a terminal command."""
    type: str = "terminal_output"
    sessionId: str
    agentId: str
    command: str
    output: str
    exitCode: Optional[int] = None
    isError: bool = False


class WorkspaceFileNode(BaseModel):
    """A file or directory node in the workspace tree."""
    name: str
    path: str
    type: str  # "file" | "directory"
    language: Optional[str] = None
    status: Optional[str] = None  # "new" | "modified" | "deleted"
    children: Optional[List["WorkspaceFileNode"]] = None


class WorkspaceUpdateEvent(BaseModel):
    """Full workspace file tree update."""
    type: str = "workspace_update"
    sessionId: str
    agentId: str
    rootPath: str
    fileTree: List[WorkspaceFileNode] = []


class AgentHandoffEvent(BaseModel):
    """Emitted when one agent delegates work to another."""
    type: str = "agent_handoff"
    sessionId: str
    fromAgent: str
    toAgent: str
    taskSummary: str


# Union type for all engine events
EngineEvent = Union[
    ThinkingEvent,
    ResponseEvent,
    ToolCallEvent,
    ToolResultEvent,
    AgentStatusEvent,
    DoneEvent,
    ErrorEvent,
    TokenUsageEvent,
    PongEvent,
    QuestionEvent,
    ScreenshotEvent,
    SystemNoticeEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    TerminalOutputEvent,
    WorkspaceUpdateEvent,
    AgentHandoffEvent,
]
