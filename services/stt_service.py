import os
import logging
from typing import Optional
import assemblyai as aai
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class STTService:
    """Speech-to-Text service using AssemblyAI"""
    
    def __init__(self):
        self.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not self.api_key:
            raise ValueError("ASSEMBLYAI_API_KEY environment variable not set")
        
        aai.settings.api_key = self.api_key
        self.transcriber = aai.Transcriber()
    
    def transcribe_audio_file(self, file_path: str) -> str:
        """
        Transcribe audio from a file path
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Transcribed text
            
        Raises:
            HTTPException: If transcription fails
        """
        try:
            logger.info(f"Starting transcription of file: {file_path}")
            transcript = self.transcriber.transcribe(file_path)
            
            if transcript.error:
                error_msg = f"Transcription failed: {transcript.error}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
            
            text = (transcript.text or "").strip()
            logger.info(f"Transcription completed. Text length: {len(text)}")
            return text
            
        except Exception as e:
            error_msg = f"STT service error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
