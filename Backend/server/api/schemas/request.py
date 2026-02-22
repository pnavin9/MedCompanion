"""Request schemas for API endpoints."""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class ChatDomain(str, Enum):
    """Medical domain for specialized AI behavior."""
    GENERAL = "general"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    DERMATOLOGY = "dermatology"


class ChatMode(str, Enum):
    """Interaction mode for AI behavior."""
    CONSULT = "consult"
    PLAN = "plan"
    DIAGNOSE = "diagnose"
    SUMMARIZE = "summarize"
    AGENT = "agent"


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    session_id: str = Field(..., description="Session ID for the conversation")
    message: str = Field(..., description="User message text")
    image_path: Optional[str] = Field(None, description="Path to image file (optional)")
    domain: ChatDomain = Field(default=ChatDomain.GENERAL, description="Medical domain for specialized behavior")
    mode: ChatMode = Field(default=ChatMode.CONSULT, description="Interaction mode")
    stream: bool = Field(False, description="Whether to stream the response")
    workspace_path: Optional[str] = Field(None, description="Workspace path for reading medical files (used in summarize mode)")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="Optional list of tool schemas from MCP server to inject into prompt")
    
    @validator('mode')
    def validate_agent_mode(cls, v, values):
        """Reject Agent mode as it's not yet supported."""
        if v == ChatMode.AGENT:
            raise ValueError("Agent mode is not yet supported")
        return v


class SessionCreateRequest(BaseModel):
    """Request model for creating a new session."""
    title: Optional[str] = Field(None, description="Optional title for the session")


class SessionUpdateRequest(BaseModel):
    """Request model for updating a session."""
    title: str = Field(..., description="New title for the session")
