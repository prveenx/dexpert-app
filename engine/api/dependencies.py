"""
FastAPI dependency injection — shared service instances.

These dependencies are available to all route handlers.
"""

from typing import Optional
from core.config.settings import DexpertSettings, get_settings
from core.session.manager import SessionManager
from core.memory.database import Database
import jwt
from fastapi import Header, HTTPException

# Singleton instances
_session_manager: Optional[SessionManager] = None
_database: Optional[Database] = None


def get_engine_settings() -> DexpertSettings:
    """Dependency: get the global engine settings."""
    return get_settings()


def get_session_manager() -> SessionManager:
    """Dependency: get the session manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def get_database() -> Database:
    """Dependency: get the memory database singleton."""
    global _database
    if _database is None:
        settings = get_settings()
        _database = Database(settings.db_path)
    return _database


def verify_token(authorization: str = Header(None)) -> dict:
    """
    Dependency: Verify the JWT from Electron.
    Checks against the shared auth_secret.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        # Expected format: Bearer <jwt>
        token = authorization.split(" ")[1] if " " in authorization else authorization
        settings = get_settings()
        payload = jwt.decode(
            token,
            settings.better_auth_secret,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
