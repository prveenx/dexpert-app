import os
import sys
import traceback
import importlib

# Ensure the engine directory is in the Python path
ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

print(f"Testing Engine Imports...")
print(f"ENGINE_DIR: {ENGINE_DIR}")
print(f"Python version: {sys.version}")
print("-" * 50)

def test_module_import(name):
    print(f"Testing {name:.<40}", end=" ")
    try:
        # Clear any existing reference in sys.modules to force re-import if needed
        # (Though for a test script this isn't strictly necessary)
        if name in sys.modules:
            del sys.modules[name]
        
        importlib.import_module(name)
        print("✅ SUCCESS")
        return True
    except ImportError as e:
        print("❌ FAILED (ImportError)")
        print(f"   Reason: {e}")
        return False
    except Exception as e:
        print("⚠️  ERROR")
        print(f"   Reason: {type(e).__name__}: {e}")
        # traceback.print_exc() # uncomment if you need full traces
        return False

# List of critical third-party dependencies to check
dependencies = [
    "fastapi",
    "pydantic",
    "pydantic_settings",
    "litellm",
    "aiosqlite",
    "jwt", # pyjwt
    "httpx",
    "psutil",
    "pyautogui",
]

# List of internal engine modules to check
internal_modules = [
    "core.config.settings",
    "core.llm.client",
    "core.memory.database",
    "core.session.history",
    "core.session.manager",
    "core.scratchpad",
    "api.dependencies",
    "api.server",
    "api.routers.agents",
    "api.routers.sessions",
    "agents.base",
    "agents.planner.agent",
    "agents.browser.agent",
    "agents.os.agent",
    "utils.logger",
    "utils.exceptions",
]

print("--- Third-Party Dependencies ---")
dep_results = [test_module_import(d) for d in dependencies]

print("\n--- Internal Engine Modules ---")
int_results = [test_module_import(m) for m in internal_modules]

print("-" * 50)
total_success = all(dep_results) and all(int_results)

if total_success:
    print("✨ ALL IMPORTS WORKING CORRECTLY ✨")
    print("If your IDE still shows errors, it's likely using the wrong Python interpreter.")
    print("Make sure your IDE is pointed at the virtual environment in ./engine/.venv")
else:
    print("❌ SOME IMPORTS FAILED.")
    print("Please fix the missing dependencies or path issues above.")
    sys.exit(1)
