"""
FastAPI application factory.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import health, sessions, agents, settings, extensions
from api.websocket.handler import websocket_endpoint
from extensions.manager import ExtensionManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    mgr = ExtensionManager.get_instance()
    await mgr.start()
    print("Application startup complete")
    yield
    print("[Engine] Shutting down...")
    await mgr.stop()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Dexpert Engine",
        version="0.1.0",
        description="Dexpert AI Multi-Agent Engine API",
        lifespan=lifespan,
    )

    # CORS — only allow local connections
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(sessions.router, prefix="/api", tags=["sessions"])
    app.include_router(agents.router, prefix="/api", tags=["agents"])
    app.include_router(settings.router, prefix="/api", tags=["settings"])

    # WebSocket
    app.add_api_websocket_route("/ws", websocket_endpoint)

    return app
