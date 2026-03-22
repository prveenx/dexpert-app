# FILE: agents/base.py
"""
Base Agent — abstract class for all Dexpert agents.

Adapted from PCAgent MAF core/base_agent.py.
Provides: status tracking, event emission, LLM client access.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncGenerator
import logging

from core.llm.client import LLMClient
from core.config.settings import AgentConfig, DexpertSettings
from core.protocol.messages import TaskFrame
from core.protocol.events import (
    EngineEvent, ThinkingEvent, ResponseEvent, AgentStatusEvent
)

log = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all Dexpert agents."""

    def __init__(
        self,
        agent_id: str,
        config: Optional[AgentConfig] = None,
        globals: Optional[DexpertSettings] = None,
    ):
        self.agent_id = agent_id
        self.config = config or AgentConfig()
        self.globals = globals or DexpertSettings()
        self.status = "idle"

        # Resolve API Key based on model provider
        api_key = self._resolve_api_key()

        # LLM client — initialized with agent-specific settings
        self.llm = LLMClient(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            api_key=api_key,
            agent_name=self.agent_id,
        )

        log.info(f"Agent [{self.agent_id}] initialized with model={self.config.model}")

    def _resolve_api_key(self) -> Optional[str]:
        """Determine which API key to use based on the model string."""
        model = self.config.model.lower()
        if "gemini" in model:
            return self.globals.google_ai_api_key
        if "openai" in model:
            return self.globals.openai_api_key
        if "anthropic" in model or "claude" in model:
            return self.globals.anthropic_api_key
        if "groq" in model:
            return self.globals.groq_api_key
        return None

    @abstractmethod
    async def execute(self, task: TaskFrame) -> AsyncGenerator[EngineEvent, None]:
        """Execute a task and yield a stream of events."""
        ...

    # ── Event Helpers ─────────────────────────────────────

    def emit_thinking(self, content: str, session_id: str = "default") -> ThinkingEvent:
        """Create a thinking event."""
        return ThinkingEvent(
            sessionId=session_id,
            agentId=self.agent_id,
            content=content
        )

    def emit_response(self, content: str, is_streaming: bool = True, session_id: str = "default") -> ResponseEvent:
        """Create a response event."""
        return ResponseEvent(
            sessionId=session_id,
            agentId=self.agent_id,
            content=content,
            isStreaming=is_streaming
        )

    def emit_status(self, status: str, action: Optional[str] = None) -> AgentStatusEvent:
        """Create a status update event."""
        self.status = status
        return AgentStatusEvent(
            agentId=self.agent_id,
            status=status,
            action=action
        )

    async def cleanup(self) -> None:
        """Clean up resources. Override in subclasses if needed."""
        pass
