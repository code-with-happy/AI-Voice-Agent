import os
import logging
import requests
from typing import List
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class TTSService:
    """Text-to-Speech service using Murf API"""
    
    def __init__(self):
        self.api_key = os.getenv("MURF_API_KEY")
        if not self.api_key:
            raise ValueError("MURF_API_KEY environment variable not set")
        
        self.api_url = "https://api.murf.ai/v1/speech/generate-with-key"
        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        self.voice_id = "en-US-marcus"
        self.format = "mp3"
        self.max_chars = 3000
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split text into chunks that respect word boundaries and max character limit
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        current = []
        current_len = 0
        
        for word in words:
            word_len = len(word)
            
            # If a single word exceeds max_chars, hard-split it
            if word_len > self.max_chars:
                if current:
                    chunks.append(" ".join(current))
                    current = []
                    current_len = 0
                
                start = 0
                while start < word_len:
                    end = min(start + self.max_chars, word_len)
                    chunks.append(word[start:end])
                    start = end
                continue
            
            # If adding this word would exceed limit, flush current
            if current_len + (1 if current else 0) + word_len > self.max_chars:
                if current:
                    chunks.append(" ".join(current))
                current = [word]
                current_len = word_len
            else:
                current.append(word)
                current_len += (1 if current_len > 0 else 0) + word_len
        
        if current:
            chunks.append(" ".join(current))
        
        return chunks
    
    def generate_speech(self, text: str) -> List[str]:
        """
        Generate speech from text, automatically chunking if needed
        
        Args:
            text: Text to convert to speech
            
        Returns:
            List of audio URLs
            
        Raises:
            HTTPException: If TTS generation fails
        """
        try:
            logger.info(f"Generating TTS for text: {text[:100]}...")
            
            # Split text into chunks if needed
            chunks = self._split_text_into_chunks(text)
            logger.info(f"Text split into {len(chunks)} chunks")
            
            audio_urls = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Generating TTS for chunk {i+1}/{len(chunks)}")
                
                payload = {
                    "voiceId": self.voice_id,
                    "text": chunk,
                    "format": self.format
                }
                
                response = requests.post(self.api_url, json=payload, headers=self.headers)
                
                if response.status_code != 200:
                    error_msg = f"TTS API Error: {response.text}"
                    logger.error(error_msg)
                    raise HTTPException(status_code=response.status_code, detail=error_msg)
                
                data = response.json()
                if "audioFile" not in data:
                    error_msg = f"Could not find audioFile in TTS response. Response structure: {data}"
                    logger.error(error_msg)
                    raise HTTPException(status_code=502, detail=error_msg)
                
                audio_url = data["audioFile"]
                audio_urls.append(audio_url)
                logger.info(f"Generated audio URL for chunk {i+1}: {audio_url}")
            
            logger.info(f"TTS generation completed. Total audio URLs: {len(audio_urls)}")
            return audio_urls
            
        except Exception as e:
            error_msg = f"TTS service error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
