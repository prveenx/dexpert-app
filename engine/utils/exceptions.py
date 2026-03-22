"""
Dexpert Error types — matching @dexpert/types ErrorCode enum.
"""

from enum import Enum


class ErrorCode(str, Enum):
    UNKNOWN = "UNKNOWN"
    INTERNAL = "INTERNAL"
    VALIDATION = "VALIDATION"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    ENGINE_NOT_READY = "ENGINE_NOT_READY"
    ENGINE_TIMEOUT = "ENGINE_TIMEOUT"
    ENGINE_CRASHED = "ENGINE_CRASHED"
    AGENT_DISABLED = "AGENT_DISABLED"
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    AGENT_ERROR = "AGENT_ERROR"
    TASK_CANCELLED = "TASK_CANCELLED"
    TASK_FAILED = "TASK_FAILED"
    LLM_API_ERROR = "LLM_API_ERROR"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    LLM_CONTEXT_OVERFLOW = "LLM_CONTEXT_OVERFLOW"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_EXECUTION_ERROR = "TOOL_EXECUTION_ERROR"
    AUTH_EXPIRED = "AUTH_EXPIRED"
    AUTH_INVALID = "AUTH_INVALID"
    MCP_CONNECTION_FAILED = "MCP_CONNECTION_FAILED"
    MCP_SERVER_ERROR = "MCP_SERVER_ERROR"
    PLUGIN_LOAD_ERROR = "PLUGIN_LOAD_ERROR"
    PLUGIN_EXECUTION_ERROR = "PLUGIN_EXECUTION_ERROR"


class DexpertError(Exception):
    """Typed error with error code matching the TypeScript ErrorCode enum."""

    def __init__(self, code: ErrorCode, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
        }
