"""
Settings API router — engine configuration management.
"""

from fastapi import APIRouter
from core.config.settings import get_settings, reload_settings

router = APIRouter()


@router.get("/settings")
async def get_all_settings():
    """Get all engine settings."""
    settings = get_settings()
    return {
        "port": settings.engine_port,
        "host": settings.engine_host,
        "logLevel": settings.log_level,
        "defaultModel": settings.default_model,
        "defaultTemperature": settings.default_temperature,
        "defaultMaxTokens": settings.default_max_tokens,
        "globalModelOverride": settings.global_model_override,
        "enablePersonalization": settings.enable_personalization,
        "memoryMaxFacts": settings.memory_max_facts,
        "agents": {
            "planner": {
                "enabled": settings.planner.enabled,
                "model": settings.planner.model,
                "temperature": settings.planner.temperature,
                "maxTokens": settings.planner.max_tokens,
                "timeout": settings.planner.timeout,
                "maxRetries": settings.planner.max_retries,
            },
            "browser": {
                "enabled": settings.browser.enabled,
                "model": settings.browser.model,
                "temperature": settings.browser.temperature,
                "maxTokens": settings.browser.max_tokens,
                "timeout": settings.browser.timeout,
                "maxRetries": settings.browser.max_retries,
            },
            "os": {
                "enabled": settings.os_agent.enabled,
                "model": settings.os_agent.model,
                "temperature": settings.os_agent.temperature,
                "maxTokens": settings.os_agent.max_tokens,
                "timeout": settings.os_agent.timeout,
                "maxRetries": settings.os_agent.max_retries,
            },
        },
    }


@router.patch("/settings")
async def update_settings(body: dict):
    """Update engine settings at runtime."""
    settings = get_settings()

    if "defaultModel" in body:
        settings.default_model = body["defaultModel"]
    if "globalModelOverride" in body:
        settings.global_model_override = body["globalModelOverride"]
    if "defaultTemperature" in body:
        settings.default_temperature = body["defaultTemperature"]
    if "defaultMaxTokens" in body:
        settings.default_max_tokens = body["defaultMaxTokens"]
    if "enablePersonalization" in body:
        settings.enable_personalization = body["enablePersonalization"]
    if "logLevel" in body:
        settings.log_level = body["logLevel"]

    return {"updated": True}


@router.post("/settings/reload")
async def force_reload_settings():
    """Force reload settings from environment/.env file."""
    reload_settings()
    return {"reloaded": True}
