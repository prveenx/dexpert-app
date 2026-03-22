from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from extensions.manager import ExtensionManager
from extensions.mcp.discoverer import McpDiscoverer

router = APIRouter(prefix="/extensions", tags=["extensions"])

class ConnectRequest(BaseModel):
    command: str
    args: List[str]

@router.get("/mcp")
async def list_mcp_servers():
    """List all configured MCP servers."""
    mgr = ExtensionManager._instance
    if not mgr:
        # Mocking for testing if manager not loaded
        return []
        
    return [{"id": sid, "connected": True} for sid in mgr.mcp_clients.keys()]

@router.post("/mcp/{server_id}")
async def add_server(server_id: str, req: ConnectRequest):
    mgr = ExtensionManager._instance
    # Needs to persist
    return {"status": "added", "id": server_id}

@router.post("/mcp/{server_id}/connect")
async def connect_mcp_server(server_id: str, req: ConnectRequest):
    """Force connect an MCP server."""
    mgr = ExtensionManager._instance
    if mgr:
        await mgr.connect_server(server_id, req.command, req.args)
    return {"status": "connected"}

@router.post("/mcp/{server_id}/disconnect")
async def disconnect_mcp_server(server_id: str):
    mgr = ExtensionManager._instance
    if mgr:
        await mgr.disconnect_server(server_id)
    return {"status": "disconnected"}

@router.get("/mcp/discover")
async def discover_mcp_servers():
    """Discover servers."""
    found = McpDiscoverer.discover_all()
    return [{"id": f.id, "command": f.command, "args": f.args} for f in found]

@router.get("/tools")
async def get_all_tools():
    mgr = ExtensionManager._instance
    if mgr:
        return mgr.get_all_tools()
    return []
