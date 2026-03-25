# FILE: engine/api/routers/settings.py
"""
Settings API router — engine configuration management.
"""

from fastapi import APIRouter
from core.config.settings import get_settings, reload_settings

router = APIRouter()

@router.get("/settings")
async def get_all_settings():
    """Get all engine settings (masks API keys for security)."""
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
        "apiKeys": {
            "hasGoogle": bool(settings.google_api_key),
            "hasOpenAI": bool(settings.openai_api_key),
            "hasAnthropic": bool(settings.anthropic_api_key),
            "hasGroq": bool(settings.groq_api_key),
        },
        "agents": {
            "planner": {
                "enabled": settings.planner.enabled,
                "model": settings.planner.model,
            },
            "browser": {
                "enabled": settings.browser.enabled,
                "model": settings.browser.model,
            },
            "os": {
                "enabled": settings.os_agent.enabled,
                "model": settings.os_agent.model,
            },
        },
    }


@router.patch("/settings")
async def update_settings(body: dict):
    """Update engine settings at runtime and persist them."""
    settings = get_settings()

    if "defaultModel" in body:
        settings.default_model = body["defaultModel"]
    if "globalModelOverride" in body:
        settings.global_model_override = body["globalModelOverride"]
    if "enablePersonalization" in body:
        settings.enable_personalization = body["enablePersonalization"]
    if "logLevel" in body:
        settings.log_level = body["logLevel"]

    if "apiKeys" in body:
        keys = body["apiKeys"]
        if "google" in keys: settings.google_api_key = keys["google"]
        if "openai" in keys: settings.openai_api_key = keys["openai"]
        if "anthropic" in keys: settings.anthropic_api_key = keys["anthropic"]
        if "groq" in keys: settings.groq_api_key = keys["groq"]

    # Persist changes to disk
    settings.save_user_config()

    return {"updated": True}


@router.post("/settings/reload")
async def force_reload_settings():
    """Force reload settings from environment/.env file."""
    reload_settings()
    return {"reloaded": True}