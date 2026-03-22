"""
Dexpert Engine — FastAPI + uvicorn entry point.
Prints "Application startup complete" on ready (Electron watches for this).
"""

import os
import sys
import asyncio
import uvicorn
from api.server import create_app

def main():
    port = int(os.getenv("ENGINE_PORT", "48765"))
    host = os.getenv("ENGINE_HOST", "127.0.0.1")

    app = create_app()

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        reload=False,
    )
    server = uvicorn.Server(config)

    try:
        server.run()
    except KeyboardInterrupt:
        print("[Engine] Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
