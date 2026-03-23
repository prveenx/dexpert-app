"""
Agents API router — agent status, config, and control.
"""

from fastapi import APIRouter, Depends
from core.config.settings import get_settings
from api.dependencies import verify_token

router = APIRouter()


@router.get("/agents")
async def list_agents(auth: dict = Depends(verify_token)):
    """List all agents and their current statuses."""
    settings = get_settings()
    return {
        "agents": [
            {
                "id": "planner",
                "status": "idle",
                "enabled": settings.planner.enabled,
                "model": settings.planner.model,
            },
            {
                "id": "browser",
                "status": "idle",
                "enabled": settings.browser.enabled,
                "model": settings.browser.model,
            },
            {
                "id": "os",
                "status": "idle",
                "enabled": settings.os_agent.enabled,
                "model": settings.os_agent.model,
            },
        ]
    }


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, auth: dict = Depends(verify_token)):
    """Get a specific agent's status and config."""
    settings = get_settings()
    agent_map = {
        "planner": settings.planner,
        "browser": settings.browser,
        "os": settings.os_agent,
    }
    config = agent_map.get(agent_id)
    if not config:
        return {"error": f"Agent '{agent_id}' not found"}
    return {
        "id": agent_id,
        "status": "idle",
        "enabled": config.enabled,
        "model": config.model,
        "temperature": config.temperature,
        "maxTokens": config.max_tokens,
        "timeout": config.timeout,
        "maxRetries": config.max_retries,
    }


@router.patch("/agents/{agent_id}")
async def update_agent(agent_id: str, body: dict, auth: dict = Depends(verify_token)):
    """Update an agent's config (runtime override)."""
    settings = get_settings()
    agent_map = {
        "planner": settings.planner,
        "browser": settings.browser,
        "os": settings.os_agent,
    }
    config = agent_map.get(agent_id)
    if not config:
        return {"error": f"Agent '{agent_id}' not found"}

    if "enabled" in body:
        config.enabled = body["enabled"]
    if "model" in body:
        config.model = body["model"]
    if "temperature" in body:
        config.temperature = body["temperature"]
    if "maxTokens" in body:
        config.max_tokens = body["maxTokens"]

    return {"updated": True, "id": agent_id}
