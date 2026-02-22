"""Database models for sessions and messages."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from server.db.database import Base


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Session(Base):
    """Chat session model."""
    
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to messages
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, title={self.title})>"


class Message(Base):
    """Chat message model."""
    
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)  # JSON string for complex content
    image_path = Column(String, nullable=True)  # Path to uploaded image if any
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to session
    session = relationship("Session", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, session_id={self.session_id})>"
