import asyncio
import os
import json
import logging
import uuid
import sys
import time
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pathlib import Path

log = logging.getLogger(__name__)

class ScriptStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessHandle:
    """Holds state for a background process."""
    def __init__(self, pid: int, process: asyncio.subprocess.Process, task_id: str):
        self.pid = pid
        self.process = process
        self.task_id = task_id
        self.stdout_buffer = []
        self.stderr_buffer = []
        self.start_time = time.time()

class ExecutionController:
    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir).resolve()  # Always absolute
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.active_processes: Dict[str, ProcessHandle] = {}

    async def execute_script(
        self, 
        code: str, 
        language: str, 
        timeout: float = 30.0,
        blocking: bool = False,
        cwd: str = None,
        env: Dict[str, str] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Unified execution tool.
        - language: python, powershell, bash, cmd, shell
        - blocking: if True, waits up to `timeout` for completion.
        """
        task_id = str(uuid.uuid4())[:8]
        
        # 1. Setup Environment
        run_env = os.environ.copy()
        if env: run_env.update(env)
        run_env["PYTHONIOENCODING"] = "utf-8"
        
        if context:
            ctx_path = self.work_dir / f"ctx_{task_id}.json"
            with open(ctx_path, "w", encoding="utf-8") as f:
                json.dump(context, f, default=str)
            run_env["PCAGENT_CONTEXT_PATH"] = str(ctx_path)
            
        working_dir = str(Path(cwd).resolve()) if cwd else str(self.work_dir)
        try:
             os.makedirs(working_dir, exist_ok=True)
        except: pass

        # 2. Map 'shell' 
        if language == "shell":
            language = "cmd" if os.name == 'nt' else "bash"

        # 3. Write Script
        ext_map = {"python": ".py", "powershell": ".ps1", "bash": ".sh", "cmd": ".bat"}
        script_path = (self.work_dir / f"script_{task_id}{ext_map.get(language, '.txt')}").resolve()  # Always absolute
        
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        # 4. Build Command
        cmd = self._get_command(language, script_path)
        
        try:
            # 5. Spawn Process
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=run_env
            )
            
            handle = ProcessHandle(proc.pid, proc, task_id)
            self.active_processes[task_id] = handle
            
            # Start stream readers
            asyncio.create_task(self._read_stream(proc.stdout, handle.stdout_buffer))
            asyncio.create_task(self._read_stream(proc.stderr, handle.stderr_buffer))

            # 6. Wait Logic
            wait_time = timeout
            
            try:
                await asyncio.wait_for(proc.wait(), timeout=wait_time)
                return self._finalize_process(task_id) # Finished!
            except asyncio.TimeoutError:
                if blocking:
                    # Blocking mode, but timed out
                    return {
                        "status": "timeout",
                        "task_id": task_id,
                        "pid": proc.pid,
                        "message": f"Execution timed out after {timeout}s. Process continuing in background."
                    }
                else:
                    # Fire & Forget mode
                    return {
                        "status": ScriptStatus.RUNNING,
                        "task_id": task_id,
                        "pid": proc.pid,
                        "stdout_preview": "".join(handle.stdout_buffer)[-500:],
                        "message": f"Script running. Use check_status(task_id='{task_id}') to poll."
                    }

        except Exception as e:
            log.error(f"Execution failed: {e}")
            return {"status": ScriptStatus.FAILED, "error": str(e)}

    async def check_script_status(self, task_id: str = None, pid: int = None, wait_seconds: float = 0.0) -> Dict[str, Any]:
        """Polls a task. Optionally waits `wait_seconds` for it to finish."""
        
        # Resolve Task ID
        if not task_id and pid:
            for tid, handle in self.active_processes.items():
                if handle.pid == pid:
                    task_id = tid
                    break
        
        if not task_id:
            return {"status": ScriptStatus.FAILED, "error": "Task ID or valid PID required."}

        handle = self.active_processes.get(task_id)
        if not handle:
            return {"status": ScriptStatus.FAILED, "error": "Task ID not found or already cleaned up."}

        # Check if already done
        if handle.process.returncode is not None:
            return self._finalize_process(task_id)

        # Optional Blocking Wait
        if wait_seconds > 0:
            try:
                await asyncio.wait_for(handle.process.wait(), timeout=wait_seconds)
                return self._finalize_process(task_id)
            except asyncio.TimeoutError:
                pass 

        # Return snapshot with delta
        stdout_delta = "".join(handle.stdout_buffer)
        stderr_delta = "".join(handle.stderr_buffer)
        
        handle.stdout_buffer.clear()
        handle.stderr_buffer.clear()

        return {
            "status": ScriptStatus.RUNNING,
            "task_id": task_id,
            "pid": handle.pid,
            "stdout": stdout_delta,
            "stderr": stderr_delta,
            "duration_ms": (time.time() - handle.start_time) * 1000
        }

    async def wait(self, seconds: int, reason: str = None) -> Dict[str, Any]:
        await asyncio.sleep(seconds)
        return {"waited_seconds": seconds, "reason": reason, "timestamp": time.time()}

    def _get_command(self, language: str, path: Path) -> list:
        if language == "python": return [sys.executable, "-u", str(path)]
        if language == "powershell": return ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(path)]
        if language == "bash": return ["bash", str(path)]
        if language == "cmd": return ["cmd", "/c", str(path)]
        return [str(path)]

    async def _read_stream(self, stream, buffer):
        while True:
            line = await stream.readline()
            if not line: break
            buffer.append(line.decode('utf-8', errors='replace'))

    async def stop_all(self):
        """Kills all active background processes."""
        if not self.active_processes:
            return
            
        log.info(f"Killing {len(self.active_processes)} active scripts...")
        for task_id in list(self.active_processes.keys()):
            handle = self.active_processes.get(task_id)
            if handle and handle.process.returncode is None:
                try:
                    handle.process.kill()
                    await handle.process.wait()
                except Exception as e:
                    log.error(f"Failed to kill script {task_id}: {e}")
            self.active_processes.pop(task_id, None)

    def _finalize_process(self, task_id: str) -> Dict[str, Any]:
        handle = self.active_processes.pop(task_id, None)
        if not handle: return {"error": "Lost handle during finalization"}
        
        return {
            "status": ScriptStatus.COMPLETED,
            "return_code": handle.process.returncode,
            "stdout": "".join(handle.stdout_buffer),
            "stderr": "".join(handle.stderr_buffer),
            "task_id": task_id,
            "duration_ms": (time.time() - handle.start_time) * 1000
        }