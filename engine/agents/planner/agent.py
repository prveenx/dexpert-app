# FILE: /Planner/agent.py
import logging
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional

from core.base_agent import BaseAgent
from core.protocol import Message, AgentType, MessageType, TaskFrame, ResultFrame
from llm.client import LLMClient
from memory.state_manager import StateManager
from memory.personalization import PersonalizationEngine

from .Planner.config.config import PlannerSettings, PlannerPrompts
from .Planner.models import PlannerDecision
from config.config import resolve_model

log = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    """
    The Planner Agent is the brain of the PCAgent MAF.
    It interprets user intent and routes it to the appropriate specialist.
    """
    def __init__(self, state_manager: StateManager):
        super().__init__("Planner", AgentType.PLANNER)
        self.state_manager = state_manager
        self.settings = PlannerSettings.load()
        self.prompts = PlannerPrompts.load()
        
        # Initialize Personalization
        self.personalization = PersonalizationEngine(self.state_manager)
        # Resolve model based on global override
        model_to_use = resolve_model(self.settings.model.model_name)
        
        self.llm = LLMClient(
            model=model_to_use, 
            temperature=self.settings.model.temperature,
            max_tokens=self.settings.model.max_tokens,
            agent_name=self.name,
            session_id=self.state_manager.session_id
        )
        self.llm.set_event_handler(self.emit)

    async def process(self, message: Message) -> Message:
        if message.type != MessageType.CHAT:
            return self.create_message(message.sender, MessageType.ERROR, "Planner only accepts CHAT messages.")

        history = await self.state_manager.get_recent_interactions(limit=15)
        
        # 🚀 CACHE FIX: Filter out the CURRENT message from history
        # (This keeps the history prefix clean and stable)
        filtered_history = [h for h in history if h['content'] != message.content]
        
        llm_messages = [{"role": "user" if h['role'] == "user" else "assistant", "content": h['content']} for h in filtered_history]
        
        # The latest user query
        llm_messages.append({"role": "user", "content": message.content})

        # 🚀 1. Fetch Split Omni-Context (Static vs Dynamic)
        omni = await self.personalization.get_omni_context(current_task=str(message.content))
        
        # Static part goes to System (Most stable prefix)
        full_system_prompt = f"{omni['static']}\n\n{self.prompts.system_prompt}"
        
        # Dynamic part goes to the VERY END (Observation)
        # By placing this after the history and query, the entire prefix remains 100% cache-stable.
        llm_messages.append({"role": "system", "content": f"SYSTEM STATE OBSERVATION:\n{omni['dynamic']}"})

        try:
            response_text = await self.llm.generate(
                system=full_system_prompt, 
                messages=llm_messages,
                response_format="json"
            )
        except Exception as e:
            log.error(f"Planner LLM Error: {e}", exc_info=True)
            return self.create_message(AgentType.USER, MessageType.ERROR, f"Planner Error: {str(e)}")

        try:
            clean_json = response_text.strip()
            if clean_json.startswith("```json"): clean_json = clean_json[7:]
            if clean_json.endswith("```"): clean_json = clean_json[:-3]
            decision = PlannerDecision(**json.loads(clean_json))
        except Exception as e:
            return self.create_message(AgentType.USER, MessageType.ERROR, f"Failed to parse decision: {str(e)}")

        if self.settings.execution.get('show_thoughts') and decision.thought_process:
            await self.emit("THINK", decision.thought_process)

        if decision.decision_type == "CHAT":
            return self.create_message(AgentType.USER, MessageType.CHAT, decision.content)
        
        elif decision.decision_type == "ESCALATE":
            # 🚀 Escalate to User for human intervention
            return self.create_message(AgentType.USER, MessageType.QUESTION, decision.content)
        
        elif decision.decision_type in ["TASK", "COMPLEX_TASK"]:
            target_str = decision.target_agent or self.settings.execution.get('default_routing', 'browser')
            target_agent = AgentType.BROWSER if target_str == "browser" else AgentType.OS
            
            task_id = str(uuid.uuid4())[:8]
            workflow_plan = {"sub_tasks":[st.model_dump() for st in decision.sub_tasks]} if decision.sub_tasks else None
            
            # 🚀 2. Inject Global Context into the Task Payload
            task_frame = TaskFrame(
                task_id=task_id,
                goal=decision.content,
                context={
                    "task_complexity": decision.task_complexity or ("complex" if decision.decision_type == "COMPLEX_TASK" else "simple"),
                    "target_count": decision.target_count,
                    "workflow_plan": workflow_plan,
                    "omni_context": omni  # Pushed to specialists
                }
            )
            
            return self.create_message(target_agent, MessageType.TASK, task_frame)

        return self.create_message(AgentType.USER, MessageType.ERROR, f"Unexpected decision type.")