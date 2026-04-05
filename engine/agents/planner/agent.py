# FILE: agents/planner/agent.py
"""
Planner Agent — the routing brain of the Dexpert multi-agent system.

Interprets user intent, decomposes complex goals, and routes tasks
to specialist agents (Browser, OS).
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator

from agents.base import BaseAgent
from core.protocol.messages import (
    Message, AgentType, MessageType,
    TaskFrame, ResultFrame, QuestionFrame,
    AgentStatus
)
from core.protocol.events import (
    ThinkingEvent, ResponseEvent, AgentStatusEvent,
)
from core.llm.client import LLMClient
from core.memory.state_manager import StateManager
from core.memory.personalization import PersonalizationEngine
from core.memory.database import Database
from core.config.settings import get_settings, resolve_model

from .config.config import PlannerSettings, PlannerPrompts
from .models import PlannerDecision

log = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """
    The Planner Agent is the brain of the Dexpert MAS.
    It interprets user intent and routes it to the appropriate specialist.
    """

    def __init__(self, state_manager: Optional[StateManager] = None):
        super().__init__("planner", AgentType.PLANNER)
        settings = get_settings()

        # State manager (session-scoped interaction history)
        self.state_manager = state_manager or StateManager(session_id="global")

        # Load agent-specific config and prompts
        try:
            self.agent_settings = PlannerSettings.load()
            self.prompts = PlannerPrompts.load()
            self._system_prompt = self.prompts.system_prompt
        except FileNotFoundError:
            log.warning("Planner config files not found, using defaults")
            self.agent_settings = None
            self.prompts = None
            self._system_prompt = (
                "You are Dexpert, an advanced AI assistant with specialist agents. "
                "Analyze user requests and decide how to handle them. "
                "Respond with JSON: {\"decision_type\": \"CHAT|TASK|COMPLEX_TASK|ESCALATE\", "
                "\"content\": \"...\", \"thought_process\": \"...\", "
                "\"target_agent\": \"browser|os\", \"task_complexity\": \"simple|complex\", "
                "\"target_count\": null, \"sub_tasks\": []}"
            )

        # Initialize Personalization Engine with the database
        db = Database(settings.db_path)
        self.personalization = PersonalizationEngine(db=db, llm=self.llm)

        # Override LLM with agent-specific model if available
        if self.agent_settings:
            resolved = resolve_model(self.agent_settings.model.model_name)
            self.llm = LLMClient(
                model=resolved,
                temperature=self.agent_settings.model.temperature,
                max_tokens=self.agent_settings.model.max_tokens,
                api_key=self._resolve_api_key(),
                agent_name=self.name,
                session_id=self.state_manager.session_id,
            )

    async def process(self, message: Message) -> Message:
        """Route incoming messages through the planner decision pipeline."""
        if message.type != MessageType.CHAT:
            return self.create_message(
                message.sender, MessageType.ERROR,
                "Planner only accepts CHAT messages.",
            )

        history = await self.state_manager.get_recent_interactions(limit=15)

        # Filter out the current message from history to keep prefix cache-stable
        content_str = str(message.content)
        filtered_history = [
            h for h in history if h.get("content", "") != content_str
        ]

        llm_messages = [
            {
                "role": "user" if h["role"] == "user" else "assistant",
                "content": h["content"],
            }
            for h in filtered_history
        ]
        llm_messages.append({"role": "user", "content": content_str})

        # Fetch split omni-context (static + dynamic)
        try:
            # INTEGRATION: Using personalization engine for superior context depth
            omni = await self.personalization.get_omni_context(
                current_task=content_str,
            )
            full_system = f"{omni.get('static', '')}\n\n{self._system_prompt}"
            llm_messages.append({
                "role": "system",
                "content": f"SYSTEM STATE OBSERVATION:\n{omni.get('dynamic', '')}",
            })
        except Exception as e:
            log.warning(f"Omni-context fetch failed: {e}")
            full_system = self._system_prompt
            omni = {"static": "", "dynamic": ""}

        try:
            response_text = await self.llm.generate(
                system=full_system,
                messages=llm_messages,
            )
        except Exception as e:
            log.error(f"Planner LLM Error: {e}", exc_info=True)
            return self.create_message(
                AgentType.USER, MessageType.ERROR,
                f"Planner Error: {str(e)}",
            )

        # Parse the decision JSON
        try:
            clean_json = self._extract_json(response_text)
            decision = PlannerDecision(**json.loads(clean_json))
        except Exception as e:
            log.warning(f"Decision parse failed, treating as chat: {e}")
            return self.create_message(
                AgentType.USER, MessageType.CHAT, response_text,
            )

        # Emit thinking if configured
        show_thoughts = True
        if self.agent_settings and hasattr(self.agent_settings, "execution"):
            show_thoughts = self.agent_settings.execution.get("show_thoughts", True)

        if show_thoughts and decision.thought_process:
            await self.emit("THINK", decision.thought_process)

        # Route by decision type
        if decision.decision_type == "CHAT":
            return self.create_message(
                AgentType.USER, MessageType.CHAT, decision.content,
            )

        elif decision.decision_type == "ESCALATE":
            return self.create_message(
                AgentType.USER, MessageType.QUESTION, decision.content,
            )

        elif decision.decision_type in ("TASK", "COMPLEX_TASK"):
            default_routing = "browser"
            if self.agent_settings and hasattr(self.agent_settings, "execution"):
                default_routing = self.agent_settings.execution.get(
                    "default_routing", "browser",
                )

            target_str = decision.target_agent or default_routing
            target_agent = (
                AgentType.BROWSER if target_str == "browser" else AgentType.OS
            )

            task_id = uuid.uuid4().hex[:8]
            workflow_plan = None
            if decision.sub_tasks:
                workflow_plan = {
                    "sub_tasks": [st.model_dump() for st in decision.sub_tasks],
                }

            task_frame = TaskFrame(
                task_id=task_id,
                goal=decision.content,
                context={
                    "task_complexity": decision.task_complexity or (
                        "complex" if decision.decision_type == "COMPLEX_TASK"
                        else "simple"
                    ),
                    "target_count": decision.target_count,
                    "workflow_plan": workflow_plan,
                    "omni_context": omni,
                },
            )

            return self.create_message(target_agent, MessageType.TASK, task_frame)

        return self.create_message(
            AgentType.USER, MessageType.ERROR,
            f"Unexpected decision type: {decision.decision_type}",
        )

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        session_id: str = "default",
        model: Optional[str] = None,
    ) -> AsyncGenerator[Any, None]:
        """
        Streaming chat mode with autonomous delegation.
        The heart of the Dexpert Multi-Agent Orchestration.
        """
        yield self.emit_status("running", "Analyzing request...")

        try:
            # 1. Decision Hub - Run the full decision pipeline
            user_content = messages[-1].get("content", "") if messages else ""
            
            # Persist incoming user message
            await self.state_manager.add_interaction("user", user_content)

            msg = Message.create(
                sender=AgentType.USER,
                receiver=AgentType.PLANNER,
                msg_type=MessageType.CHAT,
                content=user_content
            )

            # 2. Get Decision
            log.info(f"Planner [session:{session_id}] deciding on: {user_content[:50]}...")
            result = await self.process(msg)

            # 3. Handle Decision & Delegate
            if result.type == MessageType.CHAT:
                # Direct response — True Streaming
                content = str(result.content)
                full_response = ""
                
                # We use the content from result as a base, but for true streaming, 
                # we call LLM stream again to give that "typewriter" feel or just 
                # use the provided content if it was already generated.
                # Since 'process' currently returns a full non-streamed response, 
                # let's refactor it to return a stream if possible, or just stream the existing content.
                
                # Streaming existing content in small bursts for UI responsiveness
                chunk_size = 50
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    full_response += chunk
                    yield self.emit_response(
                        content=chunk,
                        is_streaming=True,
                        session_id=session_id,
                    )
                    await asyncio.sleep(0.005) # Extreme low latency smoothness

                yield self.emit_response(
                    content=full_response,
                    is_streaming=False,
                    session_id=session_id,
                )

            elif result.type == MessageType.TASK:
                # Delegation!
                task_frame: TaskFrame = result.content
                target = result.receiver
                
                # Emit sleek Handoff event for UI transition
                yield self.emit_handoff(
                    to_agent=target.value.lower(),
                    task_summary=task_frame.goal,
                    session_id=session_id
                )

                # Get the specialist agent
                agent = None
                current_session = self.state_manager.session_id
                if target == AgentType.BROWSER:
                    from agents.browser.agent import BrowserAgent
                    agent = BrowserAgent(session_id=current_session)
                elif target == AgentType.OS:
                    from agents.os.agent import OSAgent
                    agent = OSAgent(session_id=current_session)
                
                if agent:
                    # Pipe events from sub-agent
                    event_queue = asyncio.Queue()
                    
                    async def event_handler(event_type: str, content: Any):
                        await event_queue.put(content)
                    
                    agent.set_event_handler(event_handler)
                    
                    # Run agent process in background
                    task = asyncio.create_task(agent.execute(task_frame))
                    
                    # Yield events as they come from sub-agent
                    while not task.done() or not event_queue.empty():
                        try:
                            # Forward events directly (they are already Event objects)
                            event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                            yield event
                        except (asyncio.TimeoutError, asyncio.QueueEmpty):
                            continue

                    agent_result_list = await task
                    # Note: agent.execute yields events, so the result is just the final state
                    # The UI already received all intermediate responses.

            elif result.type == MessageType.QUESTION:
                # Escalation
                yield self.emit_response(
                    content=str(result.content.get("question", result.content)),
                    is_streaming=False,
                    session_id=session_id
                )

            # Record final interaction
            if result.type != MessageType.TASK:
                await self.state_manager.add_interaction("assistant", str(result.content))

        except Exception as e:
            log.error(f"Planner stream_chat error: {e}", exc_info=True)
            yield self.emit_thinking(f"System Error: {str(e)}", session_id=session_id)
            raise
        finally:
            yield self.emit_status("idle")

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return text