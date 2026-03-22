
import sys
import os
import asyncio
import json

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

from .os.perception.bridge import OSBridgeClient
from .os.perception.processor import SemanticProcessor

async def main():
    binary_path = os.path.join(project_root, "", "os", "perception", "rust_layer", "target", "release", "pcagent_bridge.exe")
    bridge = OSBridgeClient(binary_path) 
    # Excel HWND was 3473734 in the previous run
    # Find the Excel window HWND dynamically to be safe
    windows = bridge.get_active_windows()
    excel_hwnd = None
    for win in windows:
        if "Excel" in win.get('title', ''):
            excel_hwnd = win.get('hwnd')
            break
    
    if not excel_hwnd:
        print("Excel window not found.")
        return

    print(f"Scanning Excel window HWND: {excel_hwnd}")
    tree = bridge.scan_ui_tree(excel_hwnd)
    
    processed_tree = SemanticProcessor.process(tree)
    
    output_path = os.path.join(current_dir, "test_table_output.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(processed_tree)
    
    print(f"Done. Output saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
