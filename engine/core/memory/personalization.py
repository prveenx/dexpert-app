# FILE: core/memory/personalization.py
"""
Background personalization engine — extracts and stores user preferences.

Adapted from PCAgent MAF memory/personalization.py.
Runs asynchronously after each user interaction to detect:
  - Personal facts (name, age, job, preferences)
  - Explicit remember requests
  - Corrections to known facts
  - Rules the user wants followed

Phase 1 (Classifier): Does the conversation contain anything worth remembering?
Phase 2 (CRUD Writer): Determine ADD/DELETE operations and execute them.
"""

import json
import asyncio
import uuid
import logging
from typing import List, Dict, Optional

from core.llm.client import LLMClient
from core.memory.database import Database

log = logging.getLogger(__name__)


class PersonalizationEngine:
    """Autonomous background memory manager."""

    def __init__(self, db: Database, llm: Optional[LLMClient] = None):
        self.db = db
        self.enabled = True  # Can be disabled via settings
        self.max_facts = 50

        # Use a utility-grade model for classification
        self.llm = llm or LLMClient(
            model="gemini/gemini-2.0-flash",
            temperature=0.1,
            max_tokens=2048,
            agent_name="Memory_Cortex",
        )
        self._processing_lock = asyncio.Lock()

    async def analyze_and_update(self, session_id: str) -> None:
        """Background task triggered after each user interaction completes."""
        if not self.enabled:
            return

        if self._processing_lock.locked():
            return

        async with self._processing_lock:
            try:
                interactions = await self.db.get_recent_interactions(
                    session_id, limit=6
                )
                if not interactions:
                    return

                conversation = ""
                user_query = ""
                for i in interactions:
                    role = "User" if i["role"] == "user" else "Dexpert"
                    conversation += f"{role}: {i['content']}\n"
                    if i["role"] == "user":
                        user_query = i["content"]

                is_memory, statement = await self._classify_memory(
                    conversation, user_query
                )
                if not is_memory:
                    return

                log.info(f"Memory_Cortex: Memory detected → \"{statement}\"")
                await self._execute_crud(conversation, statement)

            except Exception as e:
                log.error(f"PersonalizationEngine error: {e}", exc_info=True)

    async def _classify_memory(
        self, conversation: str, user_query: str
    ) -> tuple:
        """Phase 1: Determines if conversation contains anything worth remembering."""
        classifier_prompt = (
            "You are a Memory Classifier for a personal AI assistant.\n"
            "Analyze the conversation and determine if it contains personal facts, "
            "preferences, or explicit remember requests.\n\n"
            "Respond with strict JSON:\n"
            '{"detected": true, "statement": "concise summary"}\n'
            "or\n"
            '{"detected": false, "statement": ""}\n'
        )

        user_content = f"CONVERSATION:\n{conversation}"
        if user_query:
            user_content += f"\n\nLATEST USER QUERY:\n{user_query}"

        try:
            response = await self.llm.generate(
                system=classifier_prompt,
                messages=[{"role": "user", "content": user_content}],
            )

            clean_json = self._extract_json(response)
            data = json.loads(clean_json)
            detected = data.get("detected", False)
            statement = data.get("statement", "")

            if isinstance(detected, str):
                detected = detected.lower() in ("true", "yes", "1")

            return (bool(detected), str(statement))

        except Exception as e:
            log.warning(f"Memory_Cortex: Classifier failed: {e}")
            return (False, "")

    async def _execute_crud(self, conversation: str, statement: str) -> None:
        """Phase 2: Determine and execute ADD/DELETE operations."""
        current_facts = await self.db.get_all_facts()

        if current_facts:
            current_mem_str = "\n".join(
                [
                    f"  ID: '{f['key']}' | [{f['category']}] {f['value']}"
                    for f in current_facts
                ]
            )
        else:
            current_mem_str = "  (Empty)"

        crud_prompt = (
            "You are the Memory CRUD Manager.\n"
            "Output strict JSON:\n"
            '{"operations": [{"action": "ADD", "fact": "...", "category": "..."}, '
            '{"action": "DELETE", "id": "..."}]}\n'
            "Categories: user_profile, user_preferences, user_rules, work, personal, general\n"
        )

        user_content = (
            f"STATEMENT: \"{statement}\"\n\n"
            f"CURRENT DATABASE:\n{current_mem_str}\n"
        )

        try:
            response = await self.llm.generate(
                system=crud_prompt,
                messages=[{"role": "user", "content": user_content}],
            )

            clean_json = self._extract_json(response)
            data = json.loads(clean_json)
            operations = data.get("operations", [])

            for op in operations:
                action = op.get("action", "").upper()
                if action == "ADD":
                    fact = op.get("fact", "").strip()
                    cat = op.get("category", "general").strip()
                    if fact:
                        key = f"fact_{uuid.uuid5(uuid.NAMESPACE_DNS, fact).hex[:8]}"
                        await self.db.learn_fact(key, fact, cat)
                        log.info(f"🧠 MEMORY ADDED: [{cat}] {fact}")
                elif action == "DELETE":
                    fact_id = op.get("id", "").strip()
                    if fact_id:
                        await self.db.delete_fact(fact_id)
                        log.info(f"🧠 MEMORY DELETED: {fact_id}")

        except Exception as e:
            log.error(f"Memory_Cortex: CRUD failed: {e}", exc_info=True)

    @staticmethod
    def _extract_json(text: str) -> str:
        """Robustly extract JSON from LLM response text."""
        if not text:
            return "{}"
        text = text.strip()

        if "```json" in text:
            text = text.split("```json", 1)[-1]
            if "```" in text:
                text = text.split("```", 1)[0]
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1]

        text = text.strip()

        if not text.startswith(("{", "[")):
            brace = text.find("{")
            bracket = text.find("[")
            if brace >= 0 and (bracket < 0 or brace < bracket):
                text = text[brace:]
            elif bracket >= 0:
                text = text[bracket:]

        return text
