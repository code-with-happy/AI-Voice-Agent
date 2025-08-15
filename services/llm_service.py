import os
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class LLMService:
    """LLM service using Google Generative AI (Gemini)"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_AI_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_AI_KEY environment variable not set")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_response(self, text: str) -> str:
        """
        Generate a response for a single text input
        
        Args:
            text: Input text to generate response for
            
        Returns:
            Generated response text
            
        Raises:
            HTTPException: If generation fails
        """
        try:
            logger.info(f"Generating LLM response for text: {text[:100]}...")
            response = self.model.generate_content(text)
            
            if not response.text:
                error_msg = "No response generated from LLM"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
            
            result = response.text.strip()
            logger.info(f"LLM response generated. Length: {len(result)}")
            return result
            
        except Exception as e:
            error_msg = f"LLM service error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def generate_chat_response(self, user_message: str, history: List[Dict[str, str]]) -> str:
        """
        Generate a response in a chat context with history
        
        Args:
            user_message: Current user message
            history: List of previous messages with 'role' and 'content' keys
            
        Returns:
            Generated response text
            
        Raises:
            HTTPException: If generation fails
        """
        try:
            logger.info(f"Generating chat response. History length: {len(history)}")
            
            # Convert our history to Gemini chat format
            gemini_history = []
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg["content"]]})
            
            chat = self.model.start_chat(history=gemini_history)
            response = chat.send_message(user_message)
            
            if not response.text:
                error_msg = "No response generated from LLM"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
            
            result = response.text.strip()
            logger.info(f"Chat response generated. Length: {len(result)}")
            return result
            
        except Exception as e:
            error_msg = f"LLM chat service error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
