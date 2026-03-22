"""Sessions API router."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/sessions")
async def list_sessions():
    """List all sessions."""
    return {"sessions": []}


@router.post("/sessions")
async def create_session():
    """Create a new session."""
    return {"id": "new-session", "title": "New Session", "createdAt": "", "updatedAt": ""}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a session by ID."""
    return {"id": session_id, "title": "Session", "messages": []}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    return {"deleted": True, "id": session_id}
