import os
import logging
import shutil
from typing import Dict, List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Import our refactored modules
from services.stt_service import STTService
from services.llm_service import LLMService
from services.tts_service import TTSService
from schemas import (
    TTSRequest, TTSResponse, LLMQueryResponse, ChatResponse, 
    UploadResponse, EchoResponse
)
from utils import (
    create_temp_audio_file, cleanup_temp_file, create_error_response,
    validate_audio_file, validate_speech_detected
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Conversational Voice Agent",
    description="A non-streaming, session-aware conversational voice agent",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create uploads directory if it doesn't exist
uploads_dir = "uploads"
os.makedirs(uploads_dir, exist_ok=True)

# In-memory chat session store: { session_id: [ {"role": "user"|"assistant", "content": str}, ... ] }
chat_sessions: Dict[str, List[Dict[str, str]]] = {}

# Initialize services
try:
    stt_service = STTService()
    llm_service = LLMService()
    tts_service = TTSService()
    logger.info("All services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    raise

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI"""
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Failed to serve index.html: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve UI")

@app.post("/upload-audio", response_model=UploadResponse)
async def upload_audio(file: UploadFile = File(...)):
    """Upload an audio file for storage"""
    validate_audio_file(file.content_type)
    
    try:
        # Save the uploaded file to the uploads directory
        file_location = f"{uploads_dir}/{file.filename}"
        
        # Get file size before saving
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Audio file uploaded: {file.filename}, size: {file_size}")
        
        return UploadResponse(
            fileName=file.filename,
            contentType=file.content_type,
            size=file_size
        )
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@app.post("/tts/echo", response_model=EchoResponse)
async def echo_audio(file: UploadFile = File(...)):
    """Echo endpoint: transcribe audio and convert back to speech"""
    validate_audio_file(file.content_type)
    
    try:
        # Read the file content
        file_content = await file.read()
        
        # Create temporary file for transcription
        temp_file = create_temp_audio_file(file_content, uploads_dir)
        
        try:
            # Step 1: Transcribe the audio
            transcript_text = stt_service.transcribe_audio_file(temp_file)
            validate_speech_detected(transcript_text)
            
            # Step 2: Generate TTS using Murf
            audio_urls = tts_service.generate_speech(transcript_text)
            
            return EchoResponse(
                audioUrl=audio_urls[0],
                transcript=transcript_text
            )
        finally:
            cleanup_temp_file(temp_file)
            
    except Exception as e:
        logger.error(f"Echo processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")

@app.post("/tts", response_model=TTSResponse)
def generate_tts(req: TTSRequest):
    """Generate speech from text"""
    try:
        logger.info(f"Generating TTS for text: {req.text[:100]}...")
        audio_urls = tts_service.generate_speech(req.text)
        
        return TTSResponse(audioUrl=audio_urls[0])
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.post("/llm/query", response_model=LLMQueryResponse)
async def query_llm(file: UploadFile = File(...)):
    """Single-turn LLM query with audio input"""
    validate_audio_file(file.content_type)
    
    try:
        # Read uploaded audio
        file_content = await file.read()
        
        # Create temporary file for transcription
        temp_file = create_temp_audio_file(file_content, uploads_dir)
        
        try:
            # Step 1: Transcribe the audio
            user_text = stt_service.transcribe_audio_file(temp_file)
            validate_speech_detected(user_text)
            
            # Step 2: Generate response from LLM
            llm_text = llm_service.generate_response(user_text)
            
            # Step 3: Generate TTS
            audio_urls = tts_service.generate_speech(llm_text)
            
            return LLMQueryResponse(
                audioUrl=audio_urls[0],
                audioUrls=audio_urls,
                transcript=user_text,
                llmText=llm_text
            )
        finally:
            cleanup_temp_file(temp_file)
            
    except Exception as e:
        logger.error(f"LLM query failed: {e}")
        return create_error_response("unknown", str(e), 500)

@app.post("/agent/chat/{session_id}", response_model=ChatResponse)
async def chat_with_agent(session_id: str, file: UploadFile = File(...)):
    """Main conversational endpoint with session history"""
    validate_audio_file(file.content_type)
    
    try:
        # Read uploaded audio
        file_content = await file.read()
        
        # Create temporary file for transcription
        temp_file = create_temp_audio_file(file_content, uploads_dir)
        
        try:
            # Step 1: Transcribe the audio
            user_text = stt_service.transcribe_audio_file(temp_file)
            validate_speech_detected(user_text)
            
            # Initialize or get existing history for session
            history = chat_sessions.get(session_id, [])
            
            # Append user message to history
            history.append({"role": "user", "content": user_text})
            
            # Step 2: Generate response from LLM with history
            llm_text = llm_service.generate_chat_response(user_text, history)
            
            # Append assistant message to history and save
            history.append({"role": "assistant", "content": llm_text})
            chat_sessions[session_id] = history
            
            # Step 3: Generate TTS
            audio_urls = tts_service.generate_speech(llm_text)
            
            logger.info(f"Chat response generated for session {session_id}. History length: {len(history)}")
            
            return ChatResponse(
                audioUrl=audio_urls[0],
                audioUrls=audio_urls,
                transcript=user_text,
                llmText=llm_text,
                sessionId=session_id,
                historyLength=len(history)
            )
        finally:
            cleanup_temp_file(temp_file)
            
    except Exception as e:
        logger.error(f"Chat processing failed for session {session_id}: {e}")
        return create_error_response("unknown", str(e), 500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    