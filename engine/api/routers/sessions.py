"""
Sessions API router — CRUD for conversation sessions.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from core.session.manager import SessionManager
from api.dependencies import verify_token, get_session_manager

router = APIRouter()


@router.get("/sessions")
async def list_sessions(
    auth: dict = Depends(verify_token),
    mgr: SessionManager = Depends(get_session_manager)
):
    """List all sessions for the authenticated user."""
    user_id = auth.get("sub", "default")
    sessions = await mgr.list_all(user_id=user_id)
    return {"sessions": sessions}


@router.post("/sessions")
async def create_session(
    body: Optional[dict] = None,
    auth: dict = Depends(verify_token),
    mgr: SessionManager = Depends(get_session_manager)
):
    """Create a new session for the authenticated user."""
    user_id = auth.get("sub", "default")
    title = (body or {}).get("title", "New Session")
    session = await mgr.create(user_id=user_id, title=title)
    return session


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    auth: dict = Depends(verify_token),
    mgr: SessionManager = Depends(get_session_manager)
):
    """Get a specific session (ownership verified)."""
    user_id = auth.get("sub", "default")
    session = await mgr.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify ownership (if user_id in DB)
    if session.get("user_id") and session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized session access")
        
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    auth: dict = Depends(verify_token),
    mgr: SessionManager = Depends(get_session_manager)
):
    """Delete a session (ownership verified)."""
    user_id = auth.get("sub", "default")
    session = await mgr.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.get("user_id") and session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized session access")
        
    await mgr.delete(session_id)
    return {"deleted": True, "id": session_id}
