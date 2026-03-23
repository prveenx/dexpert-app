import os
import sys
import asyncio
import logging

# 1. Setup Environment
ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from agents.planner.agent import PlannerAgent
from agents.os.agent import OSAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("TestPlannerOS")

async def run_test():
    log.info("--- Starting Planner -> OS Delegation Test ---")
    
    # 2. Initialize Planner
    planner = PlannerAgent()
    
    # 3. Setup Event Listener
    async def event_handler(event_type, content):
        color = "\033[94m" # Blue
        if event_type == "ACTION": color = "\033[92m" # Green
        elif event_type == "ERROR": color = "\033[91m" # Red
        elif event_type == "TOOL_OUTPUT": color = "\033[93m" # Yellow
        print(f"{color}[{event_type}]\033[0m {content}")

    planner.set_event_handler(event_handler)
    
    # 4. Define Task
    task_goal = "Open the calculator (calc.exe), type '5 + 5', and tell me the result shown on screen."
    log.info(f"Task: {task_goal}")
    
    messages = [{"role": "user", "content": task_goal}]
    
    try:
        async for event in planner.stream_chat(messages, session_id="test_os_session"):
            if hasattr(event, 'content') and not getattr(event, 'isStreaming', False):
                # Only print final/non-streaming responses
                print(f"\033[1m[PLANNER RESPONSE]\033[0m {event.content}")
    except Exception as e:
        log.error(f"Test failed: {e}", exc_info=True)
    finally:
        await planner.cleanup()

if __name__ == "__main__":
    asyncio.run(run_test())
