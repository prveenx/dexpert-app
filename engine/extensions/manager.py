import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from .mcp.client import McpClient
from .mcp.discoverer import McpServerConfig

log = logging.getLogger(__name__)

class ExtensionManager:
    """Manages MCP servers and local Python plugins."""
    
    _instance = None
    
    def __init__(self, mcp_config_path: str = "mcp_servers.json"):
        self.mcp_config_path = Path(mcp_config_path)
        self.mcp_clients: Dict[str, McpClient] = {}
        # In a real system we'd manage python plugins here too
        
    @classmethod
    def get_instance(cls) -> "ExtensionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self):
        log.info("Starting ExtensionManager...")
        await self.load_mcp_servers()
        # Plugins would be loaded here

    async def stop(self):
        log.info("Stopping ExtensionManager...")
        for client in self.mcp_clients.values():
            await client.stop()

    async def load_mcp_servers(self):
        if not self.mcp_config_path.exists():
            with open(self.mcp_config_path, "w") as f:
                json.dump({"mcpServers": {}}, f, indent=2)

        try:
            with open(self.mcp_config_path, "r") as f:
                config = json.load(f)
            servers = config.get("mcpServers", {})
            for server_id, details in servers.items():
                command = details.get("command")
                args = details.get("args", [])
                
                if not command:
                    continue
                
                await self.connect_server(server_id, command, args)
        except Exception as e:
            log.error(f"Failed to load MCP servers: {e}")

    async def connect_server(self, server_id: str, command: str, args: List[str]):
        if server_id in self.mcp_clients:
            await self.mcp_clients[server_id].stop()

        client = McpClient(command, args, server_id)
        self.mcp_clients[server_id] = client
        
        try:
            await client.connect()
            await client.sync_tools()
        except Exception as e:
            log.error(f"Failed to connect MCP server {server_id}: {e}")
            await client.stop()
            del self.mcp_clients[server_id]

    async def disconnect_server(self, server_id: str):
        if server_id in self.mcp_clients:
            client = self.mcp_clients.pop(server_id)
            await client.stop()
            
    def get_all_tools(self) -> List[dict]:
        tools = []
        for client_id, client in self.mcp_clients.items():
            for t in client.tools:
                tools.append({
                    "id": f"{client_id}:{t.name}",
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.inputSchema.model_dump() if t.inputSchema else None,
                    "source": {"type": "mcp", "id": client_id}
                })
        return tools
