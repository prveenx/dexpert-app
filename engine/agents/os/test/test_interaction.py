import os
import sys
import asyncio
import logging
import pyautogui

# Setup paths
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.dirname(os.path.dirname(base_dir))) # add root

from .os.perception.bridge import OSBridgeClient
from .os.controller.interaction import OSInteractionController

logging.basicConfig(level=logging.INFO)

async def test_all():
    # 1. Start bridge
    bridge_path = os.path.join(base_dir, "perception", "rust_layer", "target", "release", "pcagent_bridge.exe")
    print(f"Starting OSBridge with {bridge_path}")
    bridge = OSBridgeClient(bridge_path)
    
    interact = OSInteractionController(bridge)
    
    # 2. List windows
    print("\n--- Listing Windows ---")
    windows = await interact.list_windows()
    print(windows)

    # 3. Focus a common window if possible, or skip
    print("\n--- Scanning Focused Window ---")
    tree = await interact.scan_focused_window()
    print(f"Got tree length: {len(tree)}")
    if len(tree) > 500:
        print("Tree snippet:", tree[:500])
    else:
        print("Tree:", tree)
        
    print("\n--- Test PyAutoGUI direct interaction ---")
    # Instead of randomly clicking, we just move the mouse to the center of the screen
    w, h = pyautogui.size()
    print(f"Screen size is {w}x{h}. Moving mouse to center...")
    pyautogui.moveTo(w//2, h//2, duration=1.0)
    print("Mouse moved.")
    
    print("\nTests completed successfully.")
    await bridge.stop()

if __name__ == "__main__":
    asyncio.run(test_all())
