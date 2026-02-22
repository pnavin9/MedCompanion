"""Session management API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from server.api.schemas import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    SessionDetailResponse,
    MessageResponse
)
from server.db import get_db
from server.services import session_manager

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
def create_session(
    request: SessionCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new chat session."""
    session = session_manager.create_session(db, title=request.title)
    
    return SessionResponse(
        session_id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0
    )


@router.get("", response_model=List[SessionResponse])
def list_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all sessions."""
    sessions = session_manager.list_sessions(db, skip=skip, limit=limit)
    
    return [
        SessionResponse(
            session_id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=len(s.messages)
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get a session with full message history."""
    session = session_manager.get_session(db, session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = session_manager.get_session_messages(db, session_id)
    
    return SessionDetailResponse(
        session_id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                image_path=msg.image_path,
                timestamp=msg.timestamp
            )
            for msg in messages
        ]
    )


@router.put("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update a session's metadata."""
    session = session_manager.update_session(db, session_id, request.title)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        session_id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(session.messages)
    )


@router.delete("/{session_id}")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete a session and all its messages."""
    success = session_manager.delete_session(db, session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"success": True}
