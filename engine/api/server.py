"""
FastAPI application factory.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import health, sessions, agents, settings, extensions
from api.websocket.handler import websocket_endpoint
from extensions.manager import ExtensionManager
from core.config.settings import get_settings

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    log.info("[Engine] Starting up...")

    # Initialize extension manager (MCP servers, plugins)
    mgr = ExtensionManager.get_instance()
    await mgr.start()

    log.info("[Engine] Startup complete — all systems online")
    yield
    log.info("[Engine] Shutting down...")
    await mgr.stop()
    log.info("[Engine] Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app_settings = get_settings()

    app = FastAPI(
        title="Dexpert Engine",
        version="0.1.0",
        description="Dexpert AI Multi-Agent Engine API",
        lifespan=lifespan,
    )

    # CORS — allow local Electron and dev server connections
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(sessions.router, prefix="/api", tags=["sessions"])
    app.include_router(agents.router, prefix="/api", tags=["agents"])
    app.include_router(settings.router, prefix="/api", tags=["settings"])
    app.include_router(extensions.router, prefix="/api", tags=["extensions"])

    # WebSocket
    app.add_api_websocket_route("/ws", websocket_endpoint)

    return app
