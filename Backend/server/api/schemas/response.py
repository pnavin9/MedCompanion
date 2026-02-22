"""Response schemas for API endpoints."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Response model for a single message."""
    id: str
    role: str
    content: str
    image_path: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message_id: str = Field(..., description="ID of the generated message")
    response: str = Field(..., description="Assistant's response")
    timestamp: datetime = Field(..., description="Timestamp of the response")


class SessionResponse(BaseModel):
    """Response model for session metadata."""
    session_id: str = Field(..., description="Unique session identifier")
    title: Optional[str] = Field(None, description="Session title")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: Optional[int] = Field(None, description="Number of messages in session")


class SessionDetailResponse(BaseModel):
    """Response model for session with full message history."""
    session_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Server status")
    model_loaded: bool = Field(..., description="Whether the MedGemma model is loaded")
    version: str = Field(..., description="API version")
    medasr_loaded: bool = Field(False, description="Whether the MedASR model is loaded")


class ImageUploadResponse(BaseModel):
    """Response model for image upload."""
    image_id: str = Field(..., description="Unique image identifier")
    path: str = Field(..., description="Storage path")
    url: str = Field(..., description="Access URL for the image")
