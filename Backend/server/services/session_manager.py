"""Session management service."""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from server.db.models import Session as SessionModel, Message as MessageModel


class SessionManager:
    """Service for managing chat sessions and messages."""
    
    def create_session(self, db: Session, title: Optional[str] = None) -> SessionModel:
        """Create a new chat session."""
        session = SessionModel(title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    def get_session(self, db: Session, session_id: str) -> Optional[SessionModel]:
        """Get a session by ID."""
        return db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    def list_sessions(self, db: Session, skip: int = 0, limit: int = 100) -> List[SessionModel]:
        """List all sessions."""
        return db.query(SessionModel).order_by(SessionModel.updated_at.desc()).offset(skip).limit(limit).all()
    
    def update_session(self, db: Session, session_id: str, title: str) -> Optional[SessionModel]:
        """Update a session's title."""
        session = self.get_session(db, session_id)
        if session:
            session.title = title
            session.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(session)
        return session
    
    def delete_session(self, db: Session, session_id: str) -> bool:
        """Delete a session and all its messages."""
        session = self.get_session(db, session_id)
        if session:
            db.delete(session)
            db.commit()
            return True
        return False
    
    def add_message(
        self,
        db: Session,
        session_id: str,
        role: str,
        content: str,
        image_path: Optional[str] = None
    ) -> MessageModel:
        """Add a message to a session."""
        message = MessageModel(
            session_id=session_id,
            role=role,
            content=content,
            image_path=image_path
        )
        db.add(message)
        
        # Update session's updated_at timestamp
        session = self.get_session(db, session_id)
        if session:
            session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        return message
    
    def get_session_messages(self, db: Session, session_id: str) -> List[MessageModel]:
        """Get all messages for a session."""
        return db.query(MessageModel).filter(
            MessageModel.session_id == session_id
        ).order_by(MessageModel.timestamp).all()
    
    def get_conversation_history(self, db: Session, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history in a format suitable for the model.
        
        Returns a list of dicts with 'role' and 'content' keys.
        """
        messages = self.get_session_messages(db, session_id)
        history = []
        
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return history


# Global session manager instance
session_manager = SessionManager()
