# FILE: /os/perception/bridge.py
import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)

class OSBridgeClient:
    """
    Production-grade Async IPC Client for the Rust OS Daemon.
    Provides persistent JSON-RPC connection to native desktop bindings.
    """
    
    def __init__(self, binary_path: str):
        self.binary_path = os.path.abspath(binary_path)
        self.proc: Optional = None
        self._lock = asyncio.Lock()
        self._is_running = False

    async def start(self):
        """Spawns the Rust daemon and waits for the ready signal."""
        if self._is_running and self.proc and self.proc.returncode is None:
            return

        if not os.path.exists(self.binary_path):
            log.warning(f"OS Bridge binary missing at: {self.binary_path}. Please build the Rust layer (`cargo build --release`).")
            raise FileNotFoundError(f"Bridge not found: {self.binary_path}")

        log.info("Booting Rust OS Perception Daemon...")
        
        self.proc = await asyncio.create_subprocess_exec(
            self.binary_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=1024 * 1024 * 50, # 50MB buffer for massive native DOM trees
        )
        
        asyncio.create_task(self._monitor_stderr())

        # Wait for the handshake
        ready_line = await self.proc.stdout.readline()
        if not ready_line:
            raise RuntimeError("Rust daemon crashed during boot.")
            
        try:
            ready_data = json.loads(ready_line.decode('utf-8'))
            if ready_data.get("status") == "ready":
                self._is_running = True
                log.info(f"Rust OS Daemon connected successfully. (PID: {self.proc.pid})")
            else:
                raise RuntimeError(f"Unexpected boot response: {ready_data}")
        except json.JSONDecodeError:
            raise RuntimeError(f"Malformed boot response from Rust: {ready_line}")

    async def request(self, payload: Dict, timeout: float = 15.0) -> Dict:
        """Sends a JSON command to Rust and awaits the response."""
        await self.start() # Ensure running lazily
        
        async with self._lock:
            try:
                req_str = json.dumps(payload) + "\n"
                self.proc.stdin.write(req_str.encode('utf-8'))
                await self.proc.stdin.drain()
                
                res_bytes = await asyncio.wait_for(self.proc.stdout.readline(), timeout=timeout)
                
                if not res_bytes:
                    self._is_running = False
                    return {"error": "Fatal: Rust daemon closed connection unexpectedly."}
                    
                return json.loads(res_bytes.decode('utf-8'))
                
            except asyncio.TimeoutError:
                log.error("OS Bridge request timed out. Daemon might be hung.")
                await self.restart()
                return {"error": "Request timed out waiting for OS layer."}
            except Exception as e:
                log.error(f"OS Bridge IPC Error: {e}")
                self._is_running = False
                return {"error": str(e)}

    async def _monitor_stderr(self):
        """Pipes Rust internal tracing to Python's debug logger."""
        if not self.proc or not self.proc.stderr:
            return
        try:
            while True:
                line = await self.proc.stderr.readline()
                if not line: break
                log.debug(f" {line.decode('utf-8').strip()}")
        except Exception:
            pass

    async def restart(self):
        await self.stop()
        await self.start()

    async def stop(self):
        """Gracefully shuts down the daemon."""
        if self.proc and self.proc.returncode is None:
            try:
                self.proc.stdin.write(b'{"action": "exit"}\n')
                await self.proc.stdin.drain()
                await asyncio.wait_for(self.proc.wait(), timeout=2.0)
            except Exception:
                self.proc.kill()
        self._is_running = False
        log.info("Rust OS Daemon terminated.")