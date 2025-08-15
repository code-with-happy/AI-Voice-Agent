from pydantic import BaseModel, Field
from typing import List, Optional

# Request schemas
class TTSRequest(BaseModel):
    """Request schema for text-to-speech endpoint"""
    text: str = Field(..., description="Text to convert to speech", min_length=1)

class LLMQueryRequest(BaseModel):
    """Request schema for LLM query endpoint"""
    text: str = Field(..., description="Text to send to LLM", min_length=1)

# Response schemas
class TTSResponse(BaseModel):
    """Response schema for text-to-speech endpoint"""
    audioUrl: str = Field(..., description="URL of the generated audio file")

class ErrorResponse(BaseModel):
    """Response schema for error cases"""
    success: bool = Field(False, description="Always false for error responses")
    errorStage: str = Field(..., description="Stage where error occurred: stt, llm, tts, or unknown")
    message: str = Field(..., description="Error message")
    fallbackText: str = Field(..., description="Text to speak as fallback")

class LLMQueryResponse(BaseModel):
    """Response schema for LLM query endpoint"""
    success: bool = Field(True, description="Always true for successful responses")
    audioUrl: str = Field(..., description="URL of the first audio file")
    audioUrls: List[str] = Field(..., description="List of all audio URLs (for chunked responses)")
    transcript: str = Field(..., description="Transcribed user input")
    llmText: str = Field(..., description="Generated LLM response text")

class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""
    success: bool = Field(True, description="Always true for successful responses")
    audioUrl: str = Field(..., description="URL of the first audio file")
    audioUrls: List[str] = Field(..., description="List of all audio URLs (for chunked responses)")
    transcript: str = Field(..., description="Transcribed user input")
    llmText: str = Field(..., description="Generated LLM response text")
    sessionId: str = Field(..., description="Session ID for this conversation")
    historyLength: int = Field(..., description="Number of messages in conversation history")

class UploadResponse(BaseModel):
    """Response schema for file upload endpoint"""
    fileName: str = Field(..., description="Name of the uploaded file")
    contentType: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="Size of the file in bytes")

class EchoResponse(BaseModel):
    """Response schema for echo endpoint"""
    audioUrl: str = Field(..., description="URL of the generated audio file")
    transcript: str = Field(..., description="Transcribed input audio")
