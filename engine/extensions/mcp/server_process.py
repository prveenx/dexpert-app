import asyncio
import logging
import subprocess
from typing import Optional, Callable

log = logging.getLogger(__name__)

class McpServerProcess:
    def __init__(self, command: str, args: list[str], on_crash: Optional[Callable] = None):
        self.command = command
        self.args = args
        self.process: Optional[asyncio.subprocess.Process] = None
        self.on_crash = on_crash
        self._running = False
        self._monitor_task = None

    async def start(self):
        cmd = [self.command] + self.args
        log.info(f"Starting MCP Server: {' '.join(cmd)}")
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor())

    async def _monitor(self):
        while self.process and self._running:
            return_code = await self.process.wait()
            self._running = False
            log.warning(f"MCP Server '{self.command}' stopped with exit code {return_code}")
            
            if self.on_crash:
                self.on_crash(return_code)

    async def read_stdout_line(self) -> bytes:
        if self.process and self.process.stdout:
            try:
                line = await self.process.stdout.readline()
                return line
            except Exception as e:
                log.error(f"Error reading stdout from MCP server: {e}")
                return b""
        return b""

    async def write_stdin(self, data: bytes):
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(data)
                await self.process.stdin.drain()
            except Exception as e:
                log.error(f"Error writing stdin to MCP server: {e}")

    async def read_stderr(self):
        if self.process and self.process.stderr:
            try:
                data = await self.process.stderr.read()
                return data
            except Exception:
                return b""

    async def stop(self):
        self._running = False
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                self.process.kill()
            self.process = None
