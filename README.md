# Conversational Voice Agent

A non-streaming, session-aware conversational voice agent built with FastAPI. Users speak to the agent in the browser; the server transcribes audio, calls an LLM, converts the response to speech, and streams back playable audio. Conversations are remembered by session, enabling multi-turn context.

## Features

- Session-based chat history (in-memory store keyed by `session` query param)
- Single-button voice UI with animated record state (record → process → respond → auto-listen)
- STT via AssemblyAI
- LLM via Google Generative AI (Gemini 1.5 Flash)
- TTS via Murf with automatic 3000-character chunking
- Robust error handling with structured server errors and client-side fallback speech
- Static frontend (HTML/CSS/JS), served by FastAPI

## Tech Stack

- Backend: FastAPI, `uvicorn`, `python-dotenv`
- STT: `assemblyai`
- LLM: `google-generativeai` (Gemini 1.5 Flash)
- TTS: Murf API
- Frontend: Vanilla HTML/CSS/JS

## Architecture

High-level flow (non-streaming, per user turn):

1. Browser records audio (Web Audio/MediaRecorder)
2. POST `multipart/form-data` with `file` to `POST /agent/chat/{session_id}`
3. Server:
   - Transcribe audio with AssemblyAI
   - Append user message to `chat_sessions[session_id]`
   - Call Gemini with history to produce response
   - Append assistant message to history
   - Split response into ≤ 3000-char chunks and generate Murf TTS for each
   - Return `{ audioUrls: string[], transcript, llmText, sessionId }`
4. Browser plays returned audio chunks sequentially
5. After playback ends, auto-starts recording again for the next turn

### Endpoints

- `POST /agent/chat/{session_id}`: Main conversational endpoint. Accepts audio. Returns audio URLs and metadata. Maintains in-memory history per session.
- `POST /llm/query`: Single-turn, audio-in → STT → LLM → TTS, without chat history. Accepts audio.
- `POST /tts`: Text-to-speech helper (Murf) for plain text.
- `POST /tts/echo`: Transcribe uploaded audio, then TTS the transcript (legacy/diagnostic).
- `POST /upload-audio`: Saves an uploaded audio file (diagnostic).
- `GET /`: Serves the conversational UI.
- `GET /docs`: FastAPI’s interactive API docs.

### Error Handling

Server returns structured errors like:
```json
{
  "success": false,
  "errorStage": "stt|llm|tts|unknown",
  "message": "...",
  "fallbackText": "I'm having trouble connecting right now. Please try again."
}
```
Client uses `SpeechSynthesisUtterance` to speak the fallback text and shows a brief status.

## UI

- Single prominent record button with pulse animation
- Status indicator (Idle, Listening…, Processing…, Responding…)
- Audio element is hidden; responses auto-play
- Session ID stored as `?session=...` in the URL for history separation

## Setup

### 1) Requirements

- Python 3.10+
- Murf, AssemblyAI, and Google Generative AI API keys
- Windows, macOS, or Linux (instructions below include Windows PowerShell examples)

### 2) Create a virtual environment and install deps

PowerShell (Windows):
```powershell
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3) Environment Variables

Create a `.env` file in the project root (loaded automatically via `python-dotenv`):
```ini
ASSEMBLYAI_API_KEY=your_assemblyai_api_key
GOOGLE_AI_KEY=your_google_generative_ai_key
MURF_API_KEY=your_murf_api_key
```
Alternatively, set in your shell environment.

### 4) Run the API server

Use a single worker so that in-memory chat history is consistent:

PowerShell (Windows):
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --workers 1
```

macOS/Linux:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --workers 1
```

Open the app at `http://localhost:8000`.

## Usage

1. Open the UI, ensure your browser allows microphone permissions
2. Click Record and speak
3. The agent replies with generated audio
4. After playback, the app automatically listens again for the next user turn

Use separate tabs with different `?session=` IDs to keep separate conversations.

## Simulating Failures (for testing error handling)

Temporarily unset API keys and restart the server:
//
PowerShell:
```powershell
Remove-Item Env:ASSEMBLYAI_API_KEY
# or
Remove-Item Env:GOOGLE_AI_KEY
# or
Remove-Item Env:MURF_API_KEY
```

Expected behavior: server returns structured error JSON; client speaks the fallback phrase: “I’m having trouble connecting right now. Please try again.”

## Notes & Troubleshooting

- Murf TTS has a max of 3000 characters per request; responses are chunked automatically
- AssemblyAI transcription is performed by writing the uploaded bytes to a temp `.webm` file and calling the SDK with a file path (more reliable)
- Keep `--workers 1` unless you replace the in-memory store with Redis/DB
- Check `http://localhost:8000/docs` to interact with the API
- If audio playback fails due to CORS/CDN, the client attempts `window.open(url)` as a fallback

## Project Structure

```
30 days of voice agents/
├─ main.py                # FastAPI app and endpoints
├─ static/
│  ├─ index.html          # UI
│  ├─ main.js             # UI logic (record, send, play, auto-loop)
│  └─ style.css           # (optional)
├─ requirements.txt
└─ uploads/               # temp uploads & transcription temp files
```

## Screenshots

You can add your own screenshots to `static/` and embed them here, for example:
```md
![App UI](static/screenshot-ui.png)
```

---

Made with FastAPI, AssemblyAI, Google Generative AI, and Murf.
