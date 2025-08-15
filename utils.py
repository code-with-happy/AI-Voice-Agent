import os
import logging
from uuid import uuid4
from typing import List, Dict
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from schemas import ErrorResponse

logger = logging.getLogger(__name__)

# Fallback phrase used when upstream APIs fail
FALLBACK_TROUBLE_TEXT = "I'm having trouble connecting right now. Please try again."

def create_temp_audio_file(audio_bytes: bytes, uploads_dir: str) -> str:
    """
    Create a temporary audio file from bytes
    
    Args:
        audio_bytes: Audio data as bytes
        uploads_dir: Directory to store the file
        
    Returns:
        Path to the created temporary file
    """
    temp_name = f"{uploads_dir}/tmp_{uuid4().hex}.webm"
    try:
        with open(temp_name, "wb") as f:
            f.write(audio_bytes)
        logger.info(f"Created temporary audio file: {temp_name}")
        return temp_name
    except Exception as e:
        logger.error(f"Failed to create temporary file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create temporary file: {str(e)}")

def cleanup_temp_file(file_path: str) -> None:
    """
    Clean up a temporary file
    
    Args:
        file_path: Path to the file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary file {file_path}: {e}")

def create_error_response(stage: str, message: str, status_code: int = 502) -> JSONResponse:
    """
    Create a standardized error response
    
    Args:
        stage: Stage where error occurred (stt, llm, tts, unknown)
        message: Error message
        status_code: HTTP status code
        
    Returns:
        JSONResponse with error details
    """
    error_data = ErrorResponse(
        success=False,
        errorStage=stage,
        message=message,
        fallbackText=FALLBACK_TROUBLE_TEXT
    )
    
    logger.error(f"Error at stage '{stage}': {message}")
    return JSONResponse(
        status_code=status_code,
        content=error_data.model_dump()
    )

def validate_audio_file(content_type: str) -> None:
    """
    Validate that the uploaded file is an audio file
    
    Args:
        content_type: MIME type of the file
        
    Raises:
        HTTPException: If file is not an audio file
    """
    if not content_type or not content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")

def validate_speech_detected(text: str) -> None:
    """
    Validate that speech was detected in the audio
    
    Args:
        text: Transcribed text
        
    Raises:
        HTTPException: If no speech was detected
    """
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="No speech detected in the audio")
