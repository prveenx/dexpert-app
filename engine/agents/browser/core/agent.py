# FILE: /browser/core/agent.py
"""
Production-grade Browser Agent for the PCAgent MAF.

Implements a single consolidated ReAct (Reasoning + Action) loop with:
  - Workflow-aware execution (simple vs complex task routing)
  - Scratchpad-driven multi-page processing
  - Multi-action per turn (form filling, compound interactions)
  - Automatic captcha detection & solving
  - On-demand vision via analyze_visual tool
  - Loop detection to prevent infinite action repetition
  - Clean error boundaries (Fatal vs Retryable)
  - Checkpoint persistence for crash recovery

SIMPLE TASK FLOW:
  init_workflow(simple) → gather phase → extract on-page → save_data → done

COMPLEX TASK FLOW:
  init_workflow(complex) → gather phase → enqueue items
  → transition(process) → next → navigate → extract → complete → repeat
  → transition(report) → deliver results
"""

import os
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple

from agents.base import BaseAgent
from core.protocol import (
    Message, AgentType, MessageType, AgentStatus, TaskFrame, ResultFrame, QuestionFrame
)
from core.scratchpad import Scratchpad, WorkflowPhase, TaskComplexity
from core.context.episodic import EpisodicContext as ContextManager
from llm.client import LLMClient
from llm.parser import ActionParser
from utils.exeception import FatalToolError, RetryableToolError

from .browser.config.config import BrowserAgentSettings, BrowserPrompts
from .browser.manager import BrowserManager
from .browser.context import BrowserAgentContext
from .browser.state import BrowserState

from config.config import resolve_model, resolve_vision_model

# Session manager is optional (for backward compat)
try:
    from core.session import SessionManager
except ImportError:
    SessionManager = None

log = logging.getLogger(__name__)

# Constants for safety
_MAX_STEPS = 50         # Increased for complex tasks (was 25)
_MAX_SIMPLE_STEPS = 25  # Simple tasks still capped at 25
_MAX_CONSECUTIVE_ERRORS = 5


class BrowserAgent(BaseAgent):
    """
    Specialist sub-agent for all web-based tasks.
    
    Now session-aware: checkpoints are isolated per session and
    context is managed via a token-aware sliding window.
    """

    def __init__(self, session=None):
        super().__init__("BrowserSpecialist", AgentType.BROWSER)

        # Session Manager (optional, for checkpoint isolation)
        self.session = session

        # 1. Load Configuration & Prompts
        self.settings = BrowserAgentSettings.load_from_yaml(
            "/browser/config/setting.yaml"
        )
        self.prompts = BrowserPrompts.load_from_yaml(
            "/browser/config/prompt.yaml"
        )

        # 2. Infrastructure (Lazy Load)
        self.browser_manager = BrowserManager(self.settings)

        # 3. Intelligence
        main_model = resolve_model(self.settings.perception.model_name)
        vision_model = resolve_vision_model(
            local_main_model=self.settings.perception.model_name,
            local_vision_model=self.settings.perception.vision_model
        )

        self.llm = LLMClient(
            model=main_model, 
            temperature=0, 
            agent_name=self.name,
            session_id=self.session.session_id if self.session else None
        )
        self.llm.set_event_handler(self.emit)

        if vision_model == main_model:
            self.vision_llm = self.llm
        else:
            self.vision_llm = LLMClient(
                model=vision_model, 
                temperature=0, 
                agent_name=f"{self.name}_Vision",
                session_id=self.session.session_id if self.session else None
            )
            self.vision_llm.set_event_handler(self.emit)

        self._parser = ActionParser()

        # 4. Context Manager (120k token budget)
        self._context_mgr = ContextManager(
            max_tokens=120_000,
            recent_window=15,
        )

    async def cleanup(self):
        log.info("Cleaning up Browser Agent resources...")
        await self.browser_manager.close(force=True)

    async def process(self, message: Message) -> Message:
        """
        Main Agent Entry Point.
        Accepts TASK, runs ReAct Loop, returns RESULT/ERROR.
        """
        if message.type != MessageType.TASK:
            return self.create_message(
                message.sender, MessageType.ERROR,
                "Browser Agent only accepts TASK messages.",
            )

        task: TaskFrame = message.content
        log.info(f"BrowserAgent: Starting Task '{task.goal}' (ID: {task.task_id})")
        
        # 🚀 1. Extract Split Omni-Context (Static vs Dynamic)
        omni = task.context.get("omni_context", {"static": "", "dynamic": ""})

        is_resume_clarification = "resume_with_answer" in task.context
        max_retries = getattr(self.settings.controller, 'max_retries_per_task', 3) if hasattr(self.settings, 'controller') else 3

        last_error = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    await self.emit("THINK", f"Retry attempt {attempt}/{max_retries} due to: {last_error}")
                    await asyncio.sleep(2 * attempt) # Exponential backoff

                await self.emit("THINK", f"Initializing context for: {task.goal}")

                # A. Initialize / Attach Browser
                await self.browser_manager.initialize()
                page = await self.browser_manager.get_page()

                # B. Build Execution Context
                ctx = BrowserAgentContext.build(
                    page=page,
                    browser_context=self.browser_manager.context,
                    settings=self.settings,
                    prompts=self.prompts,
                    manager=self.browser_manager,
                    llm=self.llm,
                    vision_llm=self.vision_llm,
                    emit_func=self.emit,
                )

                # C. Handle Context State (Resume vs New Task)
                self._context_mgr.clear()
                
                if is_resume_clarification:
                    log.info("BrowserAgent: Resuming from clarification state...")
                    saved_state = task.context.get("saved_state", {})
                    
                    # 1. Restore Scratchpad and original Goal
                    if "scratchpad" in saved_state:
                        ctx.scratchpad = Scratchpad(**saved_state["scratchpad"])
                        goal = ctx.scratchpad.goal or task.goal
                    else:
                        goal = task.goal

                    # 2. Restore History
                    if "history" in saved_state:
                        self._context_mgr.set_history(saved_state["history"])
                        
                    # 3. Inject the Answer seamlessly into the Context Manager
                    answer = task.context["resume_with_answer"]
                    self._context_mgr.add(
                        "user", 
                        f"SYSTEM NOTIFICATION (CLARIFICATION RECEIVED):\n{answer}\nResume your task based on this new information. Do NOT start over, continue from where you left off."
                    )
                    
                    # 4. Navigate back to the URL where the block happened if needed
                    start_url = saved_state.get("url")
                    if start_url and start_url != "about:blank":
                        if page.url == "about:blank" or page.url != start_url:
                            await ctx.navigator.navigate_to(start_url)
                else:
                    # Normal Initialization
                    self._init_scratchpad_from_task(ctx, task)
                    goal = task.goal

                    # Only load checkpoint in RESUME mode (prevents zombie state)
                    if self.session and self.session.is_resume:
                        checkpoint = self._load_checkpoint()
                        if checkpoint:
                            saved_task = checkpoint.get('task_id', '')
                            log.info(f"Session RESUME: Loading checkpoint (task: {saved_task})")
                            
                            saved_history = checkpoint.get("history", [])
                            if saved_history:
                                self._context_mgr.set_history(saved_history)
                            
                            if "scratchpad" in checkpoint:
                                scratchpad_data = checkpoint.get("scratchpad") or {}
                                ctx.scratchpad = Scratchpad(**scratchpad_data)
                                goal = ctx.scratchpad.goal
    
                            last_url = checkpoint.get("url")
                            if last_url and last_url != "about:blank":
                                if page.url == "about:blank":
                                    await ctx.navigator.navigate_to(last_url)
                        else:
                            log.info("Session RESUME: No checkpoint found, starting fresh.")
                    else:
                        log.info("New session: Starting with clean state (no checkpoint).")

                # Explicit Context Injection overrides checkpoint
                start_url = task.context.get("url") or task.context.get("start_url")
                if start_url:
                    await ctx.navigator.navigate_to(start_url)

                # E. Determine max steps based on complexity
                max_steps = _MAX_STEPS if ctx.scratchpad.task_type == TaskComplexity.COMPLEX else _MAX_SIMPLE_STEPS

                # F. Run The Loop (pass the preserved goal!)
                result_data = await self._run_react_loop(
                    goal, task.task_id, ctx,
                    max_steps=max_steps,
                    omni_context=omni
                )

                # G. Handle "Blocked" State (Agent triggered ask_clarification)
                if result_data.get("status") == "BLOCKED":
                    q_frame = QuestionFrame(
                        task_id=task.task_id,
                        question=result_data.get("question", "Blocked"),
                        context_snapshot=result_data.get("snapshot", {})
                    )
                    return self.create_message(AgentType.PLANNER, MessageType.QUESTION, q_frame)

                # H. Return Final Result
                artifacts = result_data.get("data", {})
                if isinstance(artifacts, list):
                    artifacts = {"collected_items": artifacts}

                result_frame = ResultFrame(
                    task_id=task.task_id,
                    status=result_data["status"],
                    summary=result_data["summary"],
                    artifacts=artifacts,
                )

                return self.create_message(AgentType.PLANNER, MessageType.RESULT, result_frame)

            except Exception as e:
                last_error = str(e)
                log.error(f"BrowserAgent Attempt {attempt+1} failed: {e}", exc_info=True)
                if attempt == max_retries - 1:
                    return self.create_message(
                        AgentType.PLANNER, MessageType.ERROR,
                        f"Browser Agent crashed after {max_retries} attempts: {last_error}",
                    )
                # Ensure browser is closed before retry
                await self.browser_manager.close(force=True)
            finally:
                await self.browser_manager.close()

    def _init_scratchpad_from_task(self, ctx: BrowserAgentContext, task: TaskFrame) -> None:
        """
        Initialize the scratchpad based on the task's workflow plan.

        The Planner embeds complexity info in task.context:
          - task_complexity: "simple" or "complex"
          - target_count: number of items to collect
          - workflow_plan: {sub_tasks: [...]}
        """
        task_complexity = task.context.get("task_complexity", "simple") or "simple"
        target_count = task.context.get("target_count")
        workflow_plan = task.context.get("workflow_plan") or {}

        ctx.scratchpad.init_workflow(
            task_id=task.task_id,
            goal=task.goal,
            task_type=task_complexity,
            target_count=target_count,
        )

        # Store sub-tasks in scratchpad notes for LLM reference
        sub_tasks = (workflow_plan.get("sub_tasks") or []) if isinstance(workflow_plan, dict) else []
        if sub_tasks:
            plan_text = "WORKFLOW PLAN:\n"
            for st in sub_tasks:
                plan_text += f"  Step {st.get('step')} [{st.get('agent', '').upper()}]: {st.get('instruction', '')[:100]}\n"
            ctx.scratchpad.log(plan_text)

        log.info(
            f"Scratchpad initialized: type={task_complexity}, "
            f"target={target_count}, sub_tasks={len(sub_tasks)}"
        )

    def _save_checkpoint(self, task_id: str, ctx: BrowserAgentContext):
        """Saves current state to the session directory (or legacy path)."""
        try:
            data = {
                "task_id": task_id,
                "url": ctx.navigator.page.url,
                "scratchpad": ctx.scratchpad.model_dump(mode='json'),
                "history": self._context_mgr.get_raw_history()[-10:],
            }
            
            if self.session:
                # Session-aware: save to data/sessions/<session_id>/
                self.session.save_checkpoint(data)
            else:
                # Fallback: legacy path
                with open(".browser_checkpoint.json", "w") as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            log.warning(f"BrowserAgent: Failed to save checkpoint: {e}")

    def _load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Loads state from the session directory."""
        if self.session:
            return self.session.load_checkpoint()
        
        # Fallback: legacy path
        try:
            if os.path.exists(".browser_checkpoint.json"):
                with open(".browser_checkpoint.json", "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    async def _run_react_loop(
        self,
        goal: str,
        task_id: str,
        ctx: BrowserAgentContext,
        max_steps: int = _MAX_SIMPLE_STEPS,
        omni_context: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        The Core Loop: Observe → Think → Act → Feedback
        
        Now uses ContextManager for token-aware history management
        instead of a raw list with naive truncation.
        """
        consecutive_errors = 0

        for step in range(1, max_steps + 1):
            log.info(f"--- Step {step}/{max_steps} ---")
            await self.emit("STATUS", f"Step {step}/{max_steps}")

            # 1. PERCEPTION
            try:
                state = await ctx.perception.capture(ctx.navigator.page)
                
                from .browser.state import BrowserTab, DownloadTask
                tabs_data = await ctx.navigator.get_tabs_info()
                state.tabs = [
                    BrowserTab(page_id=t["index"], title=t["title"], url=t["url"], is_active=t["active"]) 
                    for t in tabs_data
                ]

                # 🚀 UPGRADE: Inject real-time background downloads into the Agent's eyes
                raw_downloads = ctx.manager.get_all_downloads()
                state.downloads = [DownloadTask(**d) for d in raw_downloads]
                
                # Prune completed downloads that have been shown to the LLM once
                # (wait_for_download still sees them before they're pruned since it runs synchronously)
                if raw_downloads:
                    completed_ids = [d["id"] for d in raw_downloads if d.get("status") in ("completed", "failed")]
                    if completed_ids:
                        ctx.manager.completed_downloads = [
                            d for d in ctx.manager.completed_downloads 
                            if d["id"] not in completed_ids or d["id"] in ctx.manager.active_downloads
                        ]

                try:
                    await ctx.navigator._inject_tab_indicator()
                except Exception: pass

            except Exception as e:
                log.error(f"Perception Error: {e}")
                consecutive_errors += 1
                if consecutive_errors >= _MAX_CONSECUTIVE_ERRORS:
                    return {"status": AgentStatus.FAILURE, "summary": f"Perception failed: {e}"}
                await asyncio.sleep(1)
                continue

            # 2. AUTO-CAPTCHA
            captcha_res = await ctx.captcha_handler.detect_and_solve(state, ctx.navigator.page)
            if captcha_res:
                await self.emit("ACTION", f"CAPTCHA Auto-Solved: {captcha_res.text}")
                if captcha_res.input_ax_id:
                    await ctx.interactor.input_text(state, captcha_res.input_ax_id, captcha_res.text)
                    await ctx.navigator.page.keyboard.press("Enter")
                    await asyncio.sleep(2)
                    continue

            # 3. PROMPT ENGINEERING
            # Build rich tab context for the LLM
            tab_context = await ctx.navigator.get_tab_context_string()
            step_prompt = self._build_step_prompt(goal, state, ctx.scratchpad, tab_context=tab_context)

            # 4. LLM CALL
            try:
                user_content = step_prompt
                if self.settings.perception.visual_mode and state.screenshot_base64:
                    user_content = [
                        {"type": "text", "text": step_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{state.screenshot_base64}"}
                        }
                    ]

                # 🚀 SOTA: Combine Global Static Memory with Browser Prompt (PREFIX ORDER)
                omni = omni_context or {"static": "", "dynamic": ""}
                raw_system_prompt = f"{omni['static']}\n\n{self.prompts.system_prompt}"
                
                # Dynamic part goes into the turn payload
                observation_with_env = f"ENVIRONMENT:\n{omni['dynamic']}\n\n{user_content}"
                
                messages = self._context_mgr.get_context_window(
                    system_prompt=raw_system_prompt,
                    current_observation=observation_with_env,
                    scratchpad_status=ctx.scratchpad.progress_summary() if ctx.scratchpad.phase != WorkflowPhase.IDLE else None,
                )
                
                response_text = await self.llm.generate(system=raw_system_prompt, messages=messages)
                
            except Exception as e:
                log.error(f"LLM Error: {e}")
                consecutive_errors += 1
                if consecutive_errors >= _MAX_CONSECUTIVE_ERRORS:
                    return {"status": AgentStatus.FAILURE, "summary": f"LLM Error: {e}"}
                await asyncio.sleep(2)
                continue

            consecutive_errors = 0

            # Commit to context manager (compressed observation, full response)
            self._context_mgr.add("user", f"OBSERVATION (Step {step}): URL: {state.url}")
            self._context_mgr.add("assistant", response_text)

            # 5. PARSING (XML-based)
            parsed = self._parser.parse(response_text)

            if parsed.thinking:
                await self.emit("THINK", parsed.thinking)

            # Handle <done> tag
            if parsed.is_done:
                return {
                    "status": AgentStatus.SUCCESS,
                    "summary": parsed.done,
                    "data": ctx.scratchpad.collected_data
                }

            actions = parsed.actions

            if not actions:
                err_msg = "No valid <action> or <done> block found. Use <action>[...]</action> or <done>summary</done>."
                await self.emit("ERROR", "Parsing Failed - No Actions")
                self._context_mgr.add("user", f"SYSTEM ERROR: {err_msg}")
                continue

            # 6. EXECUTION
            # Snapshot tab count before actions to detect new tabs
            ctx.navigator.snapshot_tab_count()

            completion_result, feedback_logs = await self._execute_batch(actions, state, ctx)

            if completion_result:
                return completion_result

            # --- NEW TAB DETECTION ---
            # Check if any action opened a new tab and inject context for the LLM
            new_tab_event = ctx.navigator.consume_new_tab_event()
            if new_tab_event:
                tab_notification = (
                    f"TAB SWITCH NOTIFICATION: A new browser tab just opened!\n"
                    f"  Previous tab: '{new_tab_event.get('from_tab_title', 'unknown')}'\n"
                    f"  New active tab: Tab {new_tab_event.get('new_tab_index')} - "
                    f"'{new_tab_event.get('new_tab_title', '')}' ({new_tab_event.get('new_tab_url', '')})\n"
                    f"  Total tabs open: {new_tab_event.get('total_tabs', '?')}\n"
                    f"  DOM data in your NEXT observation will be from this new tab.\n"
                    f"  If this tab is not useful, use close_tab() to close it and return to the previous tab."
                )
                feedback_logs.append(tab_notification)
                await self.emit("STATUS", f"New tab opened: {new_tab_event.get('new_tab_title', '')}")

            # FEEDBACK LOOP: Inject tool outputs into context manager
            if feedback_logs:
                feedback_str = "\n".join(feedback_logs)
                self._context_mgr.add("user", f"TOOL OUTPUTS:\n{feedback_str}")

            # 7. LOOP DETECTION
            if actions:
                action_sig = json.dumps(actions, sort_keys=True, default=str)[:100]
                if ctx.scratchpad.detect_loop(action_sig):
                    await self.emit("ERROR", "Loop detected! Executing Defensive Escape Sequence.")
                    
                    # PHYSICAL ESCAPE MACRO
                    try:
                        # 1. Press Escape to kill modals
                        await ctx.navigator.page.keyboard.press("Escape")
                        await asyncio.sleep(0.5)
                        # 2. Click absolute top-left corner to unfocus blocking iframes
                        await ctx.navigator.page.mouse.click(1, 1)
                        await asyncio.sleep(0.5)
                        # 3. Log it deterministically
                        ctx.scratchpad._log_event("Triggered System Escape Macro (ESC + Click away).")
                    except Exception as esc_err:
                        log.debug(f"Escape macro minor error: {esc_err}")

                    # Hard-inject the error so the LLM changes its strategy
                    self._context_mgr.add(
                        "user",
                        "SYSTEM CRITICAL WARNING: You are stuck in a loop repeating the same action 3 times without progress! "
                        "I have forcefully pressed 'Escape' and clicked the background to clear any invisible modals or blockers. "
                        "You MUST use a DIFFERENT strategy, target a DIFFERENT element, or use 'scratchpad_skip' to skip this item."
                    )

            # 8. PERSISTENCE
            self._save_checkpoint(task_id, ctx)

        return {
            "status": AgentStatus.FAILURE,
            "summary": f"Max steps ({max_steps}) reached without completion.",
            "data": ctx.scratchpad.collected_data
        }

    async def _execute_batch(
        self,
        actions: List[Dict[str, Any]],
        state: BrowserState,
        ctx: BrowserAgentContext,
    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Executes a list of actions.
        Returns:
            (ResultDict or None, List of Feedback Strings)
        """
        feedback = []

        for i, action in enumerate(actions):
            tool_name = action.get("tool_name")
            if "parameters" in action:
                params = action["parameters"] or {}
            else:
                params = {k: v for k, v in action.items() if k != "tool_name"}

            await self.emit("ACTION", f"{tool_name} {str(params)[:60]}")

            # --- CONTROL TOOLS ---

            if tool_name == "task_complete":
                return {
                    "status": AgentStatus.SUCCESS,
                    "summary": params.get("summary", "Task Completed"),
                    "data": {"collected": ctx.scratchpad.collected_data, "notes": ctx.scratchpad.notes}
                }, feedback

            if tool_name == "ask_clarification":
                try:
                    scratchpad_dump = ctx.scratchpad.model_dump(mode='json')
                except Exception:
                    scratchpad_dump = ctx.scratchpad.model_dump()
                    
                snapshot = {
                    "scratchpad": scratchpad_dump,
                    "history": self._context_mgr.get_raw_history()[-10:],
                    "url": state.url
                }
                return {
                    "status": "BLOCKED",
                    "question": params.get("question"),
                    "snapshot": snapshot
                }, feedback

            if tool_name == "start_extraction":
                from .browser.controller.extraction import ExtractionWorkflow
                extractor = ExtractionWorkflow(ctx)
                res = await extractor.execute(
                    instruction=params.get("instruction", ""),
                    max_items=params.get("max_items", 10)
                )
                feedback.append(f"Extraction Complete. Items: {res.get('items_collected', 0)}")
                ctx.scratchpad.collected_data.extend(res.get("data", []))
                continue

            # --- STANDARD TOOLS ---
            try:
                output = await ctx.tool_registry.execute(tool_name, params, state)
                feedback.append(f"[{i+1}] {tool_name}: {output}")
            except FatalToolError as e:
                return {
                    "status": AgentStatus.FAILURE,
                    "summary": f"Fatal Tool Error: {e}"
                }, feedback
            except RetryableToolError as e:
                feedback.append(f"[{i+1}] {tool_name} FAILED (Retryable): {e}")
            except Exception as e:
                feedback.append(f"[{i+1}] {tool_name} CRASHED: {e}")

        return None, feedback

    def _build_step_prompt(
        self,
        goal: str,
        state: BrowserState,
        scratchpad: Scratchpad,
        tab_context: str = "",
    ) -> str:
        """Constructs the dense context prompt for the LLM."""
        
        # 1. Header (Compact)
        blocks = [f"GOAL: {goal}", f"URL: {state.url}, TITLE: {state.title}"]

        # 2. Tabs (Condensed)
        if state.tabs:
            active = next((t for t in state.tabs if t.is_active), None)
            if active:
                blocks.append(f"TAB: {active.title}")
            # If multiple tabs, mention count
            if len(state.tabs) > 1:
                blocks.append(f"OPEN TABS: {len(state.tabs)}")

        # 3. The DOM (The big part)
        blocks.append("-" * 10)
        blocks.append(state.prompt_representation())
        blocks.append("-" * 10)

        # 4. Workflow (Critical for logic, keep it)
        if scratchpad.phase != WorkflowPhase.IDLE:
            blocks.append(f"WORKFLOW: {scratchpad.phase.value.upper()}")
            blocks.append(f"Queue: {scratchpad.done_count}/{len(scratchpad.queue)} done. Data: {len(scratchpad.collected_data)}")

        if state.errors:
            blocks.append(f"PAGE ERRORS: {str(state.errors)}")

        blocks.append("Think step-by-step. Output <thinking> and <action> or <done>.")

        return "\n".join(blocks)