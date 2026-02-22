"""Chat API routes."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from pathlib import Path
import logging
import asyncio
import time

from server.api.schemas import ChatRequest, ChatResponse
from server.db import get_db
from server.services import medgemma_service, session_manager
from server.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message and get a response from MedGemma.
    
    Parameters:
    - session_id: Session identifier
    - message: User's text message
    - image_path: Optional path to medical image
    - domain: Medical domain (general, radiology, pathology, dermatology)
    - mode: Interaction mode (consult, plan, diagnose)
    
    The domain and mode determine the AI's specialized behavior and system prompt.
    """
    # Log incoming message
    request_start = time.time()
    logger.info(f"[CHAT] User Message: {request.message}")
    
    # Verify session exists
    t1 = time.time()
    session = session_manager.get_session(db, request.session_id)
    logger.info(f"[CHAT] Session lookup: {time.time()-t1:.3f}s")
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get conversation history
    t2 = time.time()
    history = session_manager.get_conversation_history(db, request.session_id)
    logger.info(f"[CHAT] History retrieval ({len(history)} msgs): {time.time()-t2:.3f}s")
    
    # Save user message
    t3 = time.time()
    user_msg = session_manager.add_message(
        db,
        request.session_id,
        role="user",
        content=request.message,
        image_path=request.image_path
    )
    logger.info(f"[CHAT] Save user message: {time.time()-t3:.3f}s")
    
    try:
        # Generate response WITH domain/mode (run in thread to avoid MPS deadlock)
        t4 = time.time()
        logger.info(f"[CHAT] Starting model generation (domain={request.domain.value}, mode={request.mode.value})...")
        response_text = await asyncio.to_thread(
            medgemma_service.generate_response,
            user_message=request.message,
            conversation_history=history,
            image_path=request.image_path,
            domain=request.domain,
            mode=request.mode,
            tools=request.tools
        )
        logger.info(f"[CHAT] Model generation complete: {time.time()-t4:.2f}s")
        
        # Save assistant response
        t5 = time.time()
        assistant_msg = session_manager.add_message(
            db,
            request.session_id,
            role="assistant",
            content=response_text
        )
        logger.info(f"[CHAT] Save assistant message: {time.time()-t5:.3f}s")
        
        logger.info(f"[CHAT] Total request time: {time.time()-request_start:.2f}s")
        
        return ChatResponse(
            message_id=assistant_msg.id,
            response=response_text,
            timestamp=assistant_msg.timestamp
        )
        
    except Exception as e:
        logger.error(f"[CHAT] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message and get a streaming response from MedGemma.
    
    Parameters:
    - session_id: Session identifier
    - message: User's text message
    - image_path: Optional path to medical image
    - domain: Medical domain (general, radiology, pathology, dermatology)
    - mode: Interaction mode (consult, plan, diagnose, summarize)
    - workspace_path: Optional workspace path for summarize mode
    
    The domain and mode determine the AI's specialized behavior and system prompt.
    """
    # Log incoming message
    logger.info(f"User Message: {request.message}")
    
    # Verify session exists
    session = session_manager.get_session(db, request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get conversation history
    history = session_manager.get_conversation_history(db, request.session_id)
    
    # If workspace_path provided (for summary mode), scan and read all files
    user_message = request.message
    if request.workspace_path and request.mode.value == "summarize":
        from server.services.document_scanner import scan_and_read_workspace
        
        # Backend scans workspace and reads everything
        documents_content = scan_and_read_workspace(request.workspace_path)
        
        # Prepend to user message
        user_message = f"{documents_content}\n\nUser request: {request.message}"
    
    # Save user message (original message, not with documents)
    user_msg = session_manager.add_message(
        db,
        request.session_id,
        role="user",
        content=request.message,
        image_path=request.image_path
    )
    
    async def generate():
        try:
            full_response = []
            async for chunk in medgemma_service.generate_response_stream(
                user_message=user_message,  # Use potentially modified message
                conversation_history=history,
                image_path=request.image_path,
                domain=request.domain,
                mode=request.mode,
                tools=request.tools
            ):
                full_response.append(chunk)
                yield f"data: {chunk}\n\n"
            
            # Save the complete response
            response_text = "".join(full_response)
            session_manager.add_message(
                db,
                request.session_id,
                role="assistant",
                content=response_text
            )
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: [ERROR: {str(e)}]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/images")
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload an image file."""
    # Generate unique filename
    file_ext = Path(file.filename).suffix
    image_id = str(uuid.uuid4())
    filename = f"{image_id}{file_ext}"
    file_path = settings.storage_path / filename
    
    # Save file
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        return {
            "image_id": image_id,
            "path": str(file_path),
            "url": f"/api/v1/images/{image_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
