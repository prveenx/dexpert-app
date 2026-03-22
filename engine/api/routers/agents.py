"""Agents API router."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/agents")
async def list_agents():
    """List all agents and their statuses."""
    return {
        "agents": [
            {"id": "planner", "status": "idle", "enabled": True},
            {"id": "browser", "status": "idle", "enabled": True},
            {"id": "os", "status": "idle", "enabled": True},
        ]
    }


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent status."""
    return {"id": agent_id, "status": "idle", "enabled": True}
