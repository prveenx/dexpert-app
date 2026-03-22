# FILE: /os/agent.py
import logging
import os
import platform
import json
import asyncio
import time
from typing import Dict, Any, List

from core.base_agent import BaseAgent
from core.protocol import Message, AgentType, MessageType, TaskFrame, ResultFrame, QuestionFrame, AgentStatus
from core.context_manager import ContextManager
from llm.client import LLMClient
from llm.parser import ActionParser

from .config.config import OSSettings, OSPrompts
from .controller.execution import ExecutionController
from .controller.filesystem import FilesystemController
from .controller.system import SystemController
from .controller.network import NetworkController

from .os.tools.models import (
    ExecuteScriptInput, CheckStatusInput, WaitInput,
    ReadFileInput, WriteFileInput, EditFileInput, ManageFileSystemInput, ListDirInput, SearchFilesInput,
    GetSystemInfoInput, ManageProcessInput,
    HttpRequestInput, ListWindowsInput, FocusWindowInput, LaunchAppInput,
    ScanWindowInput, ClickElementInput, InputTextInput, PressKeyInput, ScrollInput, DragAndDropInput, AnalyzeVisualInput
)
from .perception.bridge import OSBridgeClient
from .controller.interaction import OSInteractionController
from .perception.perception import OSPerceptionPipeline
from .tools.registry import OSToolRegistry
from config.config import resolve_model, resolve_vision_model

log = logging.getLogger(__name__)

class OSAgent(BaseAgent):
    def __init__(self, session=None):
        super().__init__("OSSpecialist", AgentType.OS)
        self.session = session
        
        self.settings = OSSettings.load()
        self.prompts = OSPrompts.load()
        
        # SOTA: Auto-Tracking UI state to save tokens
        self.continuous_ui_scan = False
        
        local_model = self.settings.model.get('model_name', 'gemini/gemini-1.5-flash')
        model_to_use = resolve_model(local_model)
        
        self.llm = LLMClient(
            model=model_to_use, 
            agent_name=self.name,
            session_id=self.session.session_id if self.session else None
        )
        self.llm.set_event_handler(self.emit)
        self._parser = ActionParser()
        
        # Reduced recent_window to 10 to guarantee flat token scaling.
        self._context_mgr = ContextManager(max_tokens=100_000, recent_window=10)
        
        # Subsystems
        work_dir = self.settings.execution['scripting']['working_dir']
        self.exec_ctrl = ExecutionController(work_dir)
        self.fs_ctrl = FilesystemController(work_dir)
        self.sys_ctrl = SystemController()
        self.net_ctrl = NetworkController()
        
        # Native OS (Bridge)
        bridge_path = os.path.join(os.path.dirname(__file__), "perception", "rust_layer", "target", "release", "pcagent_bridge.exe")
        self.bridge = OSBridgeClient(bridge_path)
        self.interact = OSInteractionController(self.bridge)
        
        vision_model_str = self.settings.model.get('vision_model', local_model)
        v_model = resolve_vision_model(local_main_model=local_model, local_vision_model=vision_model_str)
        self.vision_llm = LLMClient(
            model=v_model, 
            agent_name=f"{self.name}_Vision",
            session_id=self.session.session_id if self.session else None
        )
        self.perc = OSPerceptionPipeline(self.bridge, self.vision_llm, self.prompts)
        
        self.registry = OSToolRegistry()
        self._register_tools()
    
    async def cleanup(self):
        log.info("Cleaning up OS Agent resources...")
        await self.exec_ctrl.stop_all()
        await self.bridge.stop()

    def _register_tools(self):
        # Execution
        self.registry.register("execute_script", ExecuteScriptInput, self.exec_ctrl.execute_script)
        self.registry.register("check_status", CheckStatusInput, self.exec_ctrl.check_script_status)
        self.registry.register("wait", WaitInput, self.exec_ctrl.wait)
        
        # File System
        self.registry.register("read_file", ReadFileInput, self.fs_ctrl.read_file)
        self.registry.register("write_file", WriteFileInput, self.fs_ctrl.write_file)
        self.registry.register("edit_file", EditFileInput, self.fs_ctrl.edit_file)
        self.registry.register("manage_file_system", ManageFileSystemInput, self.fs_ctrl.manage_file_system)
        self.registry.register("list_dir", ListDirInput, self.fs_ctrl.list_dir)
        self.registry.register("search_files", SearchFilesInput, self.fs_ctrl.search_files)
        
        # System
        self.registry.register("get_system_info", GetSystemInfoInput, self.sys_ctrl.get_system_info)
        self.registry.register("manage_process", ManageProcessInput, self.sys_ctrl.manage_process)
        
        # Network
        self.registry.register("http_request", HttpRequestInput, self.net_ctrl.http_request)
        
        # Macro OS (Window Management)
        self.registry.register("list_windows", ListWindowsInput, self.interact.list_windows)
        self.registry.register("focus_window", FocusWindowInput, self.interact.focus_window)
        self.registry.register("launch_app", LaunchAppInput, self.interact.launch_app)
        
        # Micro OS (Active Window Perception & Interaction)
        self.registry.register("scan_window", ScanWindowInput, self.interact.scan_focused_window)
        self.registry.register("click_element", ClickElementInput, self.interact.click_element)
        self.registry.register("input_text", InputTextInput, self.interact.input_text)
        self.registry.register("press_key", PressKeyInput, self.interact.press_key)
        self.registry.register("scroll", ScrollInput, self.interact.scroll)
        self.registry.register("drag_and_drop", DragAndDropInput, self.interact.drag_and_drop)
        self.registry.register("analyze_visual", AnalyzeVisualInput, self.perc.analyze_visual)

    async def process(self, message: Message) -> Message:
        if message.type != MessageType.TASK:
            return self.create_message(message.sender, MessageType.ERROR, "OS Agent only accepts TASKs.")

        task: TaskFrame = message.content
        log.info(f"OSAgent: Starting '{task.goal}'")
        
        omni = task.context.get("omni_context", {"static": "", "dynamic": ""})
        max_retries = 3
        last_error = None
        
        try:
            for attempt in range(max_retries):
                # Reset UI tracking lock on fresh attempts
                self.continuous_ui_scan = False
                
                try:
                    if attempt > 0:
                        await self.emit("THINK", f"Retry attempt {attempt}/{max_retries} due to: {last_error}")
                        await asyncio.sleep(2 * attempt)

                    await self.emit("THINK", f"Booting OS Environment ({platform.system()})...")

                    self._context_mgr.clear()
                    
                    if task.context.get("resume_with_answer"):
                        saved_state = task.context.get("saved_state") or {}
                        saved_history = saved_state.get("history",[])
                        if saved_history:
                            self._context_mgr.set_history(saved_history)
                        
                        answer = task.context["resume_with_answer"]
                        self._context_mgr.add("user", f"SYSTEM NOTIFICATION (CLARIFICATION RECEIVED):\n{answer}\nResume your task based on this.")
                    else:
                        self._context_mgr.add("user", f"TASK GOAL: {task.goal}\nPlease begin execution. Plan your steps and take the first action.")

                    cwd = self.settings.execution['scripting']['working_dir']
                    max_steps = self.settings.execution['scripting'].get('max_steps', 20)
                    step_delay = self.settings.execution['scripting'].get('step_delay', 3.0)
                    
                    for step in range(max_steps): 
                        if step > 0:
                            await asyncio.sleep(step_delay)

                        await self.emit("STATUS", f"Step {step+1}/{max_steps}")
                        
                        # 🚀 SOTA: Live Auto-Tracking Injection
                        auto_ui_context = ""
                        if self.continuous_ui_scan:
                            try:
                                # By leaving window_id empty, the Rust layer targets the physical Foreground Window.
                                # This natively guarantees that if a popup or dialog spawned, we instantly capture it!
                                tree = await self.interact.scan_focused_window()
                                auto_ui_context = f"\n\n--- LIVE FOREGROUND WINDOW SCAN ---\n{tree[:2500]}\n(Note: This is automatically updated. You do not need to call scan_window manually.)\n-----------------------------------"
                            except Exception as e:
                                auto_ui_context = f"\n\n[Auto-Scan Failed: {e}]"
                                
                        try:
                            base_prompt = self.prompts.system_prompt.format(
                                cwd=cwd, 
                                os_name=platform.system(),
                                tool_definitions=self.registry.get_definitions()
                            )
                            raw_system_prompt = f"{omni['static']}\n\n{base_prompt}"
                        except Exception as e:
                            log.error(f"Prompt formatting error: {e}")
                            raw_system_prompt = f"You are PCAgent operating in OS Mode.\nSystem Error: {str(e)}"
                        
                        messages = self._context_mgr.get_context_window(
                            system_prompt=raw_system_prompt,
                            current_observation=f"GOAL: {task.goal}\nENVIRONMENT:\n{omni['dynamic']}{auto_ui_context}\n\nYou are currently at Step {step+1}. What is your next move?"
                        )

                        try:
                            response = await self.llm.generate(
                                system=raw_system_prompt,
                                messages=messages
                            )
                        except Exception as e:
                            raise e

                        self._context_mgr.add("assistant", response)
                        
                        parsed = self._parser.parse(response)
                        
                        if parsed.thinking:
                            await self.emit("THINK", parsed.thinking)
                        else:
                            preview = response.split("<action>")[0].split("<done>")[0].strip()
                            if preview and len(preview) > 10:
                                await self.emit("THINK", preview[:300] + ("..." if len(preview) > 300 else ""))

                        if parsed.is_done:
                            return self.create_message(
                                AgentType.PLANNER,
                                MessageType.RESULT,
                                ResultFrame(task_id=task.task_id, status=AgentStatus.SUCCESS, summary=parsed.done)
                            )

                        if not parsed.has_actions:
                            valid_tools = ", ".join(self.registry.tools.keys())
                            await self.emit("ERROR", "No <action> or <done> block found. Retrying...")
                            self._context_mgr.add(
                                "user", 
                                f"SYSTEM: No valid action found. You MUST respond with either:\n"
                                f"1. <action>[{{\"tool_name\": \"...\", \"parameters\": {{...}}}}]</action>\n"
                                f"2. <done>Your summary here</done>\n"
                                f"Available tools: {valid_tools}"
                            )
                            continue

                        for action in parsed.actions:
                            tool = action.get("tool_name")
                            params = action.get("parameters") or {}
                            
                            if not params and len(action) > 1:
                                params = {k: v for k, v in action.items() if k != "tool_name"}

                            if not tool:
                                error_msg = f"Malformed action (no tool_name): {str(action)[:120]}"
                                await self.emit("ERROR", error_msg)
                                self._context_mgr.add("user", f"SYSTEM ERROR: {error_msg}")
                                continue

                            if tool not in self.registry.tools and tool not in ("task_complete", "ask_clarification"):
                                valid_tools = ", ".join(self.registry.tools.keys())
                                error_msg = f"Unknown tool '{tool}'. Valid: {valid_tools}"
                                await self.emit("ERROR", error_msg)
                                self._context_mgr.add("user", f"SYSTEM ERROR: {error_msg}. Use 'execute_script' for commands.")
                                continue

                            params_preview = str(params)[:80]
                            await self.emit("ACTION", f"{tool}({params_preview})")
                            
                            # 🚀 Toggles & Intercepts
                            if tool == "list_windows":
                                # Automatically drop UI lock when backing out to macro view
                                self.continuous_ui_scan = False 
                            
                            if tool == "scan_window":
                                if params.get("continuous") is True:
                                    self.continuous_ui_scan = True
                                elif params.get("continuous") is False:
                                    self.continuous_ui_scan = False

                            if tool == "task_complete":
                                summary = params.get("summary", "Task completed.")
                                await self.emit("THINK", f"Finalizing: {summary}")
                                return self.create_message(
                                    AgentType.PLANNER, 
                                    MessageType.RESULT, 
                                    ResultFrame(task_id=task.task_id, status=AgentStatus.SUCCESS, summary=summary)
                                )
                            
                            if tool == "ask_clarification":
                                return self.create_message(
                                    AgentType.PLANNER,
                                    MessageType.QUESTION,
                                    QuestionFrame(
                                        task_id=task.task_id, 
                                        question=params.get("question"),
                                        context_snapshot={"history": self._context_mgr.get_raw_history()}
                                    )
                                )

                            output = await self.registry.execute(tool, params)
                            
                            display_output = output[:500] + ("..." if len(output) > 500 else "")
                            is_error = output.startswith("Error")
                            if is_error:
                                await self.emit("ERROR", f"{tool}: {display_output}")
                            else:
                                await self.emit("TOOL_OUTPUT", f"{tool} → {display_output}")
                            
                            # Memory Injection
                            self._context_mgr.add("user", f"TOOL RESULT ({tool}):\n{output}")

                    return self.create_message(AgentType.PLANNER, MessageType.ERROR, "Task timed out. Reached max steps.")

                except Exception as e:
                    last_error = str(e)
                    log.error(f"OSAgent Attempt {attempt+1} failed: {e}", exc_info=True)
                    if attempt == max_retries - 1:
                        return self.create_message(AgentType.PLANNER, MessageType.ERROR, f"OS Agent crashed after {max_retries} attempts: {last_error}")
        finally:
            await self.cleanup()