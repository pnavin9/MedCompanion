"""Speech-to-text API routes using MedASR for medical transcription."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
import logging
from pathlib import Path

from server.services import medasr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/speech", tags=["speech"])


@router.post("/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(...)
):
    """
    Transcribe audio file to text using MedASR model.
    
    Parameters:
    - audio: Audio file (wav, mp3, m4a, webm, etc.)
    
    Returns:
    - text: Transcribed text
    - success: Boolean indicating success
    - error: Error message if success is False
    """
    logger.info(f"Received audio file for transcription: {audio.filename}")
    
    # Validate file type
    allowed_extensions = {'.wav', '.mp3', '.m4a', '.webm', '.ogg', '.flac'}
    file_ext = Path(audio.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Supported formats: {', '.join(allowed_extensions)}"
        )
    
    # Create temporary file to store uploaded audio
    tmp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            # Write uploaded file to temp
            contents = await audio.read()
            tmp_file.write(contents)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Audio saved to temporary file: {tmp_file_path}")
        
        # Lazy load MedASR model if not already loaded
        if not medasr_service.model_loaded:
            logger.info("MedASR model not loaded, loading now...")
            medasr_service.load_model()
        
        # Transcribe the audio using MedASR
        result = medasr_service.transcribe_audio(tmp_file_path)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        logger.info("Temporary file cleaned up")
        
        if result["success"]:
            return JSONResponse(content={
                "text": result["text"],
                "success": True
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Transcription failed")
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up temp file if it exists
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        
        logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error transcribing audio: {str(e)}"
        )


@router.get("/health")
async def speech_health_check():
    """Check if MedASR speech service is ready."""
    return {
        "status": "ok",
        "model_loaded": medasr_service.model_loaded,
        "model_type": "medasr",
        "model_name": medasr_service.model_name
    }
