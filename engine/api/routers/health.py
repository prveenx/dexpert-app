"""Health check endpoint — polled by Electron every 30s."""

import time
from fastapi import APIRouter
from core.config.settings import get_settings

router = APIRouter()

_start_time = time.time()


@router.get("/health")
async def health_check():
    """Health check endpoint with engine uptime and agent states."""
    settings = get_settings()
    uptime = int(time.time() - _start_time)

    return {
        "status": "healthy",
        "version": "0.1.0",
        "uptime_seconds": uptime,
        "agents": {
            "planner": {
                "status": "idle",
                "enabled": settings.planner.enabled,
            },
            "browser": {
                "status": "idle",
                "enabled": settings.browser.enabled,
            },
            "os": {
                "status": "idle",
                "enabled": settings.os_agent.enabled,
            },
        },
    }
