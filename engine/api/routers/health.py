"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint — polled by Electron every 30s."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "agents": {
            "planner": "idle",
            "browser": "idle",
            "os": "idle",
        },
    }
