"""
Dexpert Engine — FastAPI + uvicorn entry point.

Prints "Application startup complete" on ready (Electron watches for this).
"""

import os
import sys

# Ensure the engine directory is in the Python path
# so all imports like `from core.config.settings import ...` resolve.
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import uvicorn
import logging
from api.server import create_app
from core.config.settings import get_settings


def setup_logging(level: str):
    """Configure basic logging."""
    logging.basicConfig(
        level=level.upper(),
        format="%(levelname)s:     %(message)s",
        stream=sys.stderr,  # Alignment with uvicorn default
    )


def main():
    settings = get_settings()
    setup_logging(settings.log_level)
    
    port = int(os.getenv("DEXPERT_ENGINE_PORT", str(settings.engine_port)))
    host = os.getenv("DEXPERT_ENGINE_HOST", settings.engine_host)

    # Ensure runtime directories exist
    os.makedirs(settings.runtime_dir, exist_ok=True)
    os.makedirs(settings.log_dir, exist_ok=True)
    os.makedirs(settings.session_dir, exist_ok=True)

    app = create_app()

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level=settings.log_level,
        reload=False,
    )
    server = uvicorn.Server(config)

    try:
        server.run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
