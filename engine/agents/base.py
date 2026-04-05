# FILE: agents/base.py
"""
Base Agent — abstract class for all Dexpert agents.

Bridges the PCAgent MAF agent API with the Dexpert production architecture.
Provides:
  - Dual API: execute() for Dexpert, process() for PCAgent-compatible agents
  - Status tracking & event emission
  - LLM client access via centralized core.config settings
  - create_message() helper for inter-agent messaging
  - emit() for streaming events to the UI
  - stream_chat() for conversational streaming
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncGenerator, Callable, Awaitable, List, Dict
import logging

from core.llm.client import LLMClient
from core.config.settings import AgentConfig, DexpertSettings, get_settings, resolve_model
from core.protocol.messages import (
    AgentType, MessageType, AgentStatus,
    TaskFrame, ResultFrame, QuestionFrame, Message,
)
from core.protocol.events import (
    ThinkingEvent, ResponseEvent,
    AgentStatusEvent, ToolCallEvent, ToolResultEvent,
)

log = logging.getLogger(__name__)


# Type alias for the event callback
EventCallback = Callable[[str, str], Awaitable[None]]


class BaseAgent(ABC):
    """
    Abstract base class for all Dexpert agents.

    Supports two constructor styles:
      - Dexpert-style: BaseAgent(agent_id, config, globals)
      - PCAgent-compat: BaseAgent(name, agent_type)  [agent_type is AgentType enum]
    """

    def __init__(
        self,
        agent_id: str,
        agent_type_or_config=None,
        globals_settings: Optional[DexpertSettings] = None,
    ):
        """
        Initialize a base agent.

        Args:
            agent_id: Unique agent identifier (e.g. "planner", "BrowserSpecialist")
            agent_type_or_config: Either an AgentType enum (PCAgent compat) or AgentConfig
            globals_settings: DexpertSettings instance (falls back to singleton)
        """
        self.agent_id = agent_id
        self.name = agent_id  # PCAgent compat alias
        self.status = "idle"
        self._event_handler: Optional[EventCallback] = None

        # Resolve settings
        self.globals = globals_settings or get_settings()

        # Determine agent_type (PCAgent compat)
        if isinstance(agent_type_or_config, AgentType):
            self.agent_type = agent_type_or_config
            self.config = self._config_for_type(agent_type_or_config)
        elif isinstance(agent_type_or_config, AgentConfig):
            self.config = agent_type_or_config
            self.agent_type = AgentType.PLANNER  # fallback
        else:
            self.config = AgentConfig()
            self.agent_type = AgentType.PLANNER  # fallback

        # Resolve API Key based on model provider
        api_key = self._resolve_api_key()

        # LLM client — initialized with agent-specific settings
        self.llm = LLMClient(
            model=resolve_model(self.config.model),
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            api_key=api_key,
            agent_name=self.agent_id,
        )

        log.info(f"Agent [{self.agent_id}] initialized with model={self.config.model}")

    def _config_for_type(self, agent_type: AgentType) -> AgentConfig:
        """Get the AgentConfig from global settings for a given agent type."""
        if agent_type == AgentType.PLANNER:
            return self.globals.planner
        elif agent_type == AgentType.BROWSER:
            return self.globals.browser
        elif agent_type == AgentType.OS:
            return self.globals.os_agent
        return AgentConfig()

    def _resolve_api_key(self) -> Optional[str]:
        """Determine which API key to use based on the model string."""
        model = self.config.model.lower()
        if "gemini" in model:
            return self.globals.google_api_key
        if "openai" in model or "gpt" in model:
            return self.globals.openai_api_key
        if "anthropic" in model or "claude" in model:
            return self.globals.anthropic_api_key
        if "groq" in model:
            return self.globals.groq_api_key
        return None

    # ── Abstract Methods ─────────────────────────────────

    @abstractmethod
    async def process(self, message: Message) -> Message:
        """
        PCAgent-style entry point: receive a Message, return a Message.
        All ported agents implement this.
        """
        ...

    async def execute(self, task: TaskFrame) -> AsyncGenerator[Any, None]:
        """
        Dexpert-style entry point: execute a task and yield events.
        Default implementation wraps process() for backward compatibility.
        """
        msg = Message.create(
            sender=AgentType.PLANNER,
            receiver=self.agent_type,
            msg_type=MessageType.TASK,
            content=task,
        )
        result = await self.process(msg)
        yield self.emit_response(
            content=str(result.content),
            is_streaming=False,
        )

    # ── Inter-Agent Messaging (PCAgent compat) ───────────

    def create_message(
        self,
        receiver: AgentType,
        msg_type: MessageType,
        content: Any,
    ) -> Message:
        """Create an inter-agent message."""
        return Message.create(
            sender=self.agent_type,
            receiver=receiver,
            msg_type=msg_type,
            content=content,
        )

    # ── Event Streaming ──────────────────────────────────

    async def emit(self, event_type: str, content: str) -> None:
        """
        Emit a UI event. PCAgent agents call this as:
            await self.emit("THINK", "Processing...")
            await self.emit("ACTION", "click(42)")
            await self.emit("STATUS", "Step 3/10")
            await self.emit("ERROR", "Something failed")
            await self.emit("TOOL_OUTPUT", "read_file → content...")
        """
        if self._event_handler:
            await self._event_handler(event_type, content)

    def set_event_handler(self, handler: EventCallback) -> None:
        """Set the callback for emit(). Used by ws handler to stream to UI."""
        self._event_handler = handler

    # ── Event Factory Helpers ────────────────────────────

    def emit_thinking(self, content: str, session_id: str = "default") -> ThinkingEvent:
        """Create a thinking event."""
        return ThinkingEvent(
            sessionId=session_id,
            agentId=self.agent_id,
            content=content,
        )

    def emit_response(self, content: str, is_streaming: bool = True, session_id: str = "default") -> ResponseEvent:
        """Create a response event."""
        return ResponseEvent(
            sessionId=session_id,
            agentId=self.agent_id,
            content=content,
            isStreaming=is_streaming,
        )

    def emit_status(self, status: str, action: Optional[str] = None) -> AgentStatusEvent:
        """Create a status update event."""
        self.status = status
        return AgentStatusEvent(
            agentId=self.agent_id,
            status=status,
            action=action,
        )

    def emit_file_created(self, file_path: str, content: str, language: str = "text", session_id: str = "default") -> Any:
        """Create a file created event."""
        from core.protocol.events import FileCreatedEvent
        return FileCreatedEvent(
            sessionId=session_id,
            agentId=self.agent_id,
            filePath=file_path,
            content=content,
            language=language
        )

    def emit_file_modified(self, file_path: str, diff: str, new_content: str = "", session_id: str = "default") -> Any:
        """Create a file modified event."""
        from core.protocol.events import FileModifiedEvent
        return FileModifiedEvent(
            sessionId=session_id,
            agentId=self.agent_id,
            filePath=file_path,
            diff=diff,
            newContent=new_content
        )

    def emit_terminal_output(self, command: str, output: str, exit_code: Optional[int] = None, is_error: bool = False, session_id: str = "default") -> Any:
        """Create a terminal output event."""
        from core.protocol.events import TerminalOutputEvent
        return TerminalOutputEvent(
            sessionId=session_id,
            agentId=self.agent_id,
            command=command,
            output=output,
            exitCode=exit_code,
            isError=is_error
        )

    def emit_handoff(self, to_agent: str, task_summary: str, session_id: str = "default") -> Any:
        """Create an agent handoff event."""
        from core.protocol.events import AgentHandoffEvent
        return AgentHandoffEvent(
            sessionId=session_id,
            fromAgent=self.agent_id,
            toAgent=to_agent,
            taskSummary=task_summary
        )

    # ── Streaming Chat (for WebSocket handler) ───────────

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        session_id: str = "default",
        model: Optional[str] = None,
    ) -> AsyncGenerator[Any, None]:
        """
        Conversational streaming for direct chat.
        Used by the WebSocket handler for the Planner's chat mode.
        """
        system_prompt = getattr(self, '_system_prompt', None)
        if not system_prompt:
            system_prompt = f"You are {self.agent_id}, an AI assistant."

        yield self.emit_status("running", "Thinking...")

        try:
            full_response = ""
            async for chunk in self.llm.stream(
                system=system_prompt,
                messages=messages,
                model=model,
            ):
                full_response += chunk
                yield self.emit_response(
                    content=chunk,
                    is_streaming=True,
                    session_id=session_id,
                )

            # Final non-streaming response with full content
            yield self.emit_response(
                content=full_response,
                is_streaming=False,
                session_id=session_id,
            )

        except Exception as e:
            log.error(f"stream_chat error: {e}", exc_info=True)
            raise
        finally:
            yield self.emit_status("idle")

    # ── Lifecycle ────────────────────────────────────────

    async def cleanup(self) -> None:
        """Clean up resources. Override in subclasses if needed."""
        pass
