import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional
from pydantic import ValidationError

from .protocol import (
    JsonRpcRequest, JsonRpcResponse, JsonRpcNotification,
    InitializeParams, InitializeResult, Tool, CallToolRequestParams, CallToolResult
)
from .server_process import McpServerProcess

log = logging.getLogger(__name__)

class McpClient:
    def __init__(self, command: str, args: list[str], server_id: str):
        self.command = command
        self.args = args
        self.server_id = server_id
        
        self.process = McpServerProcess(command, args, on_crash=self._handle_crash)
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._handlers: Dict[str, Callable] = {}
        self._next_req_id = 1
        self._listener_task: Optional[asyncio.Task] = None
        self._running = False
        
        self.tools: List[Tool] = []

    async def connect(self):
        log.info(f"Connecting MCP client for {self.server_id}")
        await self.process.start()
        self._running = True
        self._listener_task = asyncio.create_task(self._listen())
        
        # Handshake
        init_res = await self.request("initialize", InitializeParams().model_dump())
        if init_res:
            res_obj = InitializeResult(**init_res)
            log.info(f"MCP server {self.server_id} initialized with capabilities: {list(res_obj.capabilities.model_dump().keys())}")
            # Notify initialized
            await self.notify("notifications/initialized", {})

    async def _handle_crash(self, return_code: int):
        log.warning(f"MCP Client for {self.server_id} detected crash (code {return_code})")
        self._running = False
        # In a full implementation, we might try reconnecting if needed.
        for future in self._pending_requests.values():
            if not future.done():
                future.set_exception(RuntimeError("Server crashed"))

    async def _listen(self):
        while self._running:
            line = await self.process.read_stdout_line()
            if not line:
                if not self.process._running:
                    break
                continue
            
            try:
                data = json.loads(line.decode("utf-8").strip())
                log.debug(f"MCP {self.server_id} RECV: {data}")
                
                if "method" in data and "id" in data:
                    # Request from server
                    log.warning(f"Server requested something, which is unhandled: {data}")
                elif "method" in data:
                    # Notification from server
                    method = data["method"]
                    if method in self._handlers:
                        await self._handlers[method](data.get("params"))
                elif "id" in data:
                    # Response to our request
                    req_id = str(data["id"])
                    if req_id in self._pending_requests:
                        future = self._pending_requests.pop(req_id)
                        if "error" in data and data["error"]:
                            future.set_exception(Exception(f"MCP RPC Error: {data['error']}"))
                        else:
                            future.set_result(data.get("result"))
                else:
                    log.warning(f"Unknown MCP message shape: {data}")
            except Exception as e:
                log.error(f"Failed to parse MCP read: {e} -> {line}")

    async def request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if not self._running:
            raise RuntimeError("Client is not running")
        
        req_id = str(self._next_req_id)
        self._next_req_id += 1
        
        req = JsonRpcRequest(id=req_id, method=method, params=params)
        req_str = req.model_dump_json(exclude_none=True)
        log.debug(f"MCP {self.server_id} SEND: {req_str}")
        
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[req_id] = future
        
        await self.process.write_stdin((req_str + "\n").encode("utf-8"))
        return await future

    async def notify(self, method: str, params: Optional[Dict[str, Any]] = None):
        if not self._running:
            return
        msg = JsonRpcNotification(method=method, params=params).model_dump_json(exclude_none=True)
        await self.process.write_stdin((msg + "\n").encode("utf-8"))

    async def sync_tools(self) -> List[Tool]:
        """Fetch tools from the server and store them."""
        try:
            res = await self.request("tools/list")
            raw_tools = res.get("tools", []) if res else []
            self.tools = [Tool(**t) for t in raw_tools]
            return self.tools
        except Exception as e:
            log.error(f"Failed to sync tools for {self.server_id}: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> CallToolResult:
        params = CallToolRequestParams(name=tool_name, arguments=arguments)
        res = await self.request("tools/call", params.model_dump())
        return CallToolResult(**res)

    async def stop(self):
        self._running = False
        await self.process.stop()
        task = self._listener_task
        if task is not None:
            task.cancel()
