"""Settings API router."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/settings")
async def get_settings():
    """Get engine settings."""
    return {
        "port": 48765,
        "host": "127.0.0.1",
        "logLevel": "info",
        "agents": {},
        "defaultModel": {
            "provider": "google",
            "model": "gemini-2.0-flash",
            "temperature": 0.7,
            "maxTokens": 4096,
        },
    }


@router.patch("/settings")
async def update_settings(settings: dict):
    """Update engine settings."""
    return {"updated": True, "settings": settings}
