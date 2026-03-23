import os
import sys
import asyncio
import uuid
import logging

# 1. Setup Environment
ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from agents.planner.agent import PlannerAgent
from core.protocol.messages import Message, MessageType, AgentType, TaskFrame

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("TestPlannerBrowser")

async def run_test():
    log.info("--- Starting Planner -> Browser Delegation Test ---")
    
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
    task_goal = "Search Google for 'Dexpert AI' and return the title of the first organic result."
    
    # Simulate a stream_chat interaction or direct process
    # Since PlannerAgent.process() is the standard entry point for inter-agent tasks,
    # and stream_chat() is for UI, we'll test stream_chat to see the whole flow.
    
    log.info(f"Task: {task_goal}")
    
    messages = [{"role": "user", "content": task_goal}]
    
    try:
        async for event in planner.stream_chat(messages, session_id="test_session"):
            # The events yielded are protocol events (ThinkingEvent, ResponseEvent, etc.)
            # Our custom event_handler above will catch the low-level EMITs from sub-agents.
            if hasattr(event, 'content'):
                if hasattr(event, 'isStreaming') and event.isStreaming:
                    # Avoid flooding if it's a long response
                    pass
                else:
                    print(f"\033[1m[PLANNER RESPONSE]\033[0m {event.content}")
    except Exception as e:
        log.error(f"Test failed: {e}", exc_info=True)
    finally:
        await planner.cleanup()

if __name__ == "__main__":
    asyncio.run(run_test())
