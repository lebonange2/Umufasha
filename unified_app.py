#!/usr/bin/env python3
"""
Unified Assistant Application
Combines Voice-Driven Brainstorming Assistant and LLM-Powered Personal Assistant
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import structlog

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import existing brainstorming components
from utils.config import Config
from utils.logging import setup_logging, get_logger
from brain.model import BrainstormSession, IdeaSource
from brain.organizer import Organizer
from brain.assistant import BrainstormAssistant
# Audio components not needed for web mode (browser handles recording)
# from audio.mic import MicrophoneRecorder
# from audio.vad import SilenceDetector
from stt.base import STTBackend
from stt.whisper_local import WhisperLocalSTT
from stt.vosk_local import VoskSTT
from stt.whisper_cloud import WhisperAPISTT
from llm.base import LLMBackend
from llm.openai_client import OpenAIClient
from llm.http_client import HTTPClient
from llm.ollama_client import OllamaClient
from storage.files import FileStorage
from storage.autosave import AutoSaver
from storage.exporters import export_session

# Import new personal assistant components
from app.deps import get_db, get_redis, get_llm_client, get_scheduler
from app.models import Base
from app.database import engine
from app.routes import (
    users, events, notifications, calendar, telephony, 
    email, admin, webhooks, rsvp, testing
)
from app.core.config import settings

logger = get_logger('unified_app')

# ============================================
# LIFESPAN MANAGER
# ============================================

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up Unified Assistant")
    
    # Initialize brainstorming backends
    init_backends()
    
    # Initialize personal assistant database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize scheduler
    scheduler = get_scheduler()
    if scheduler:
        scheduler.start()
        logger.info("Scheduler started")
    
    logger.info("Unified Assistant startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Unified Assistant")
    
    # Stop scheduler
    if scheduler:
        try:
            if hasattr(scheduler, 'shutdown'):
                scheduler.shutdown(wait=False)
            else:
                scheduler.stop()
        except Exception as e:
            logger.warning(f"Error shutting down scheduler: {e}")
    
    logger.info("Unified Assistant shutdown complete")

# Initialize FastAPI app
app = FastAPI(
    title="Unified Assistant",
    description="Voice-Driven Brainstorming + LLM-Powered Personal Assistant",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/web-static", StaticFiles(directory="web/static"), name="web-static")
templates = Jinja2Templates(directory="app/templates")

# Include all personal assistant routes
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(telephony.router, prefix="/twilio", tags=["telephony"])
app.include_router(email.router, prefix="/email", tags=["email"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(webhooks.router, prefix="/hooks", tags=["webhooks"])
app.include_router(rsvp.router, prefix="/rsvp", tags=["rsvp"])
app.include_router(testing.router, prefix="/testing", tags=["testing"])

# Global state for brainstorming
brainstorm_sessions = {}  # session_id -> BrainstormSession
brainstorm_organizers = {}  # session_id -> Organizer
brainstorm_assistants = {}  # session_id -> BrainstormAssistant
brainstorm_storages = {}  # session_id -> FileStorage

# Initialize backends
config = Config()
stt_backend = None
llm_backend = None
llm_backends = {}  # Store multiple LLM backends
current_llm_type = "openai"  # Default to OpenAI

def init_backends():
    """Initialize STT and LLM backends."""
    global stt_backend, llm_backend, llm_backends, current_llm_type
    
    # Initialize STT
    try:
        stt_backend = WhisperLocalSTT(
            model_size=config.get('stt.whisper_model', 'base'),
            sample_rate=16000
        )
        logger.info("STT backend initialized")
    except Exception as e:
        logger.error(f"Failed to initialize STT: {e}")
    
    # Initialize OpenAI LLM
    try:
        if config.openai_api_key and config.openai_api_key != "your_openai_api_key_here":
            openai_client = OpenAIClient(
                api_key=config.openai_api_key,
                model=config.openai_model
            )
            llm_backends['openai'] = openai_client
            logger.info("OpenAI LLM backend initialized")
        else:
            logger.warning("No OpenAI API key configured")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI LLM: {e}")
    
    # Initialize Ollama LLM (local models)
    try:
        ollama_client = OllamaClient(
            model=config.get('llm.ollama_model', 'gemma3:latest'),
            base_url=config.get('llm.ollama_url', 'http://localhost:11434')
        )
        if ollama_client.is_available():
            llm_backends['ollama'] = ollama_client
            logger.info("Ollama LLM backend initialized")
        else:
            logger.warning("Ollama service not available")
    except Exception as e:
        logger.warning(f"Failed to initialize Ollama LLM: {e}")
    
    # Set default backend
    if 'openai' in llm_backends:
        llm_backend = llm_backends['openai']
        current_llm_type = 'openai'
        logger.info("Using OpenAI as default LLM")
    elif 'ollama' in llm_backends:
        llm_backend = llm_backends['ollama']
        current_llm_type = 'ollama'
        logger.info("Using Ollama as default LLM")
    else:
        logger.warning("No LLM backend available")

def switch_llm_backend(backend_type: str) -> bool:
    """Switch to a different LLM backend.
    
    Args:
        backend_type: Either 'openai' or 'ollama'
        
    Returns:
        True if switched successfully
    """
    global llm_backend, current_llm_type
    
    if backend_type not in llm_backends:
        logger.error(f"LLM backend '{backend_type}' not available")
        return False
    
    llm_backend = llm_backends[backend_type]
    current_llm_type = backend_type
    logger.info(f"Switched to {backend_type} LLM backend")
    return True

def get_or_create_brainstorm_session(session_id: str, project_name: str = "default"):
    """Get or create a brainstorming session."""
    if session_id not in brainstorm_sessions:
        # Create storage
        storage = FileStorage(Path("brainstorm") / project_name)
        
        # Load or create session
        if storage.exists():
            brainstorm_session = storage.load_session()
        else:
            brainstorm_session = BrainstormSession(project_name=project_name)
        
        # Create organizer
        organizer = Organizer(brainstorm_session)
        
        # Create assistant with current LLM backend
        assistant = None
        if llm_backend:
            assistant = BrainstormAssistant(llm_backend, organizer)
            logger.info(f"Created assistant for session {session_id} using {current_llm_type}")
        else:
            logger.warning(f"No LLM backend available for session {session_id}")
        
        # Store
        brainstorm_sessions[session_id] = brainstorm_session
        brainstorm_organizers[session_id] = organizer
        brainstorm_assistants[session_id] = assistant
        brainstorm_storages[session_id] = storage
        
        logger.info(f"Created brainstorm session: {session_id} for project: {project_name}")
    else:
        # Update assistant if LLM backend has changed
        if brainstorm_assistants.get(session_id):
            current_assistant_llm = brainstorm_assistants[session_id].llm
            if current_assistant_llm != llm_backend:
                logger.info(f"Updating assistant for session {session_id} to use {current_llm_type}")
                organizer = brainstorm_organizers[session_id]
                brainstorm_assistants[session_id] = BrainstormAssistant(llm_backend, organizer)
    
    return (
        brainstorm_sessions[session_id], 
        brainstorm_organizers[session_id], 
        brainstorm_assistants.get(session_id), 
        brainstorm_storages[session_id]
    )

# ============================================
# UNIFIED ROUTES
# ============================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - show unified dashboard."""
    return templates.TemplateResponse("unified_dashboard.html", {
        "request": request,
        "title": "Unified Assistant Dashboard"
    })

@app.get("/brainstorm", response_class=HTMLResponse)
async def brainstorm_mode(request: Request):
    """Brainstorming mode interface."""
    return templates.TemplateResponse("brainstorm_mode.html", {
        "request": request,
        "title": "Voice-Driven Brainstorming"
    })

@app.get("/personal", response_class=HTMLResponse)
async def personal_mode(request: Request):
    """Personal Assistant mode interface."""
    return RedirectResponse(url="/admin")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "modes": ["brainstorm", "personal"],
        "services": {
            "stt": stt_backend is not None and stt_backend.is_available(),
            "llm": llm_backend is not None and llm_backend.is_available(),
            "database": True,  # Assuming database is always available
            "scheduler": True  # Assuming scheduler is always available
        },
        "llm_backends": list(llm_backends.keys()),
        "current_llm": current_llm_type
    }

@app.get("/api/llm/backends")
async def get_llm_backends():
    """Get available LLM backends and current selection."""
    backends_info = {}
    for name, backend in llm_backends.items():
        backends_info[name] = {
            "available": backend.is_available(),
            "model": backend.model,
            "active": name == current_llm_type
        }
    
    return {
        "success": True,
        "backends": backends_info,
        "current": current_llm_type
    }

@app.post("/api/llm/switch")
async def switch_llm(request: Request):
    """Switch LLM backend."""
    data = await request.json()
    backend_type = data.get('backend_type')
    
    if not backend_type:
        return {'success': False, 'error': 'No backend_type provided'}
    
    if backend_type not in ['openai', 'ollama']:
        return {'success': False, 'error': f'Invalid backend type: {backend_type}'}
    
    success = switch_llm_backend(backend_type)
    
    if success:
        return {
            'success': True,
            'current': current_llm_type,
            'model': llm_backend.model if llm_backend else None
        }
    else:
        return {
            'success': False,
            'error': f'Backend {backend_type} not available'
        }

# ============================================
# BRAINSTORMING API ENDPOINTS
# ============================================

@app.post("/api/brainstorm/session/create")
async def create_brainstorm_session(request: Request):
    """Create a new brainstorming session."""
    data = await request.json()
    project_name = data.get('project_name', 'default')
    
    # Generate session ID
    import secrets
    session_id = secrets.token_hex(16)
    
    # Create session
    brainstorm_session, organizer, assistant, storage = get_or_create_brainstorm_session(session_id, project_name)
    
    return {
        'success': True,
        'session_id': session_id,
        'project_name': brainstorm_session.project_name
    }

@app.get("/api/brainstorm/session/data")
async def get_brainstorm_session_data(session_id: str):
    """Get brainstorming session data."""
    if session_id not in brainstorm_sessions:
        return {'success': False, 'error': 'Session not found'}
    
    brainstorm_session = brainstorm_sessions[session_id]
    organizer = brainstorm_organizers[session_id]
    
    # Get active ideas
    active_ideas = brainstorm_session.get_active_ideas()
    
    return {
        'success': True,
        'project_name': brainstorm_session.project_name,
        'ideas': [idea.to_dict() for idea in active_ideas],
        'clusters': [cluster.to_dict() for cluster in brainstorm_session.clusters],
        'actions': [action.to_dict() for action in brainstorm_session.actions],
        'transcript': [entry.to_dict() for entry in brainstorm_session.transcript[-20:]],
        'stats': {
            'total_ideas': len(active_ideas),
            'total_clusters': len(brainstorm_session.clusters),
            'total_actions': len([a for a in brainstorm_session.actions if not a.completed]),
            'key_ideas': len([i for i in active_ideas if i.promoted])
        }
    }

@app.post("/api/brainstorm/transcribe")
async def transcribe_audio(request: Request):
    """Transcribe audio data."""
    data = await request.json()
    session_id = data.get('session_id')
    audio_base64 = data.get('audio')
    
    if not session_id or session_id not in brainstorm_sessions:
        return {'success': False, 'error': 'Invalid session'}
    
    if not stt_backend:
        return {'success': False, 'error': 'STT backend not available'}
    
    if not audio_base64:
        return {'success': False, 'error': 'No audio data'}
    
    try:
        import base64
        import numpy as np
        import io
        import wave
        
        # Decode audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Try to parse as WAV file first
        try:
            with io.BytesIO(audio_bytes) as audio_buffer:
                with wave.open(audio_buffer, 'rb') as wav_file:
                    # Read audio data from WAV file
                    frames = wav_file.readframes(wav_file.getnframes())
                    audio_array = np.frombuffer(frames, dtype=np.int16)
                    sample_rate = wav_file.getframerate()
                    
                    logger.info(f"Received WAV audio: {len(audio_array)} samples, {sample_rate}Hz, duration: {len(audio_array)/sample_rate:.2f}s")
        except Exception as wav_error:
            # If not a valid WAV, try raw PCM
            logger.debug(f"Not a WAV file, trying raw PCM: {wav_error}")
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            logger.info(f"Received raw audio: {len(audio_array)} samples, duration: {len(audio_array)/16000:.2f}s")
        
        # Check if audio is too short
        if len(audio_array) < 1600:  # Less than 0.1 seconds
            return {'success': False, 'error': 'Audio too short'}
        
        # Transcribe
        text = stt_backend.transcribe(audio_array)
        
        if not text:
            logger.warning("Transcription returned empty")
            return {'success': False, 'error': 'No speech detected'}
        
        # Add to session
        brainstorm_session, organizer, assistant, storage = get_or_create_brainstorm_session(session_id)
        
        # Add transcript
        organizer.add_transcript(text, "user")
        
        # Add idea
        idea = organizer.add_idea(text, source=IdeaSource.USER)
        
        # Get assistant response
        assistant_response = None
        if assistant:
            assistant_response = assistant.process_user_input(text)
            if assistant_response:
                organizer.add_transcript(assistant_response, "assistant")
        
        # Save
        storage.save_session(brainstorm_session)
        
        return {
            'success': True,
            'text': text,
            'idea': idea.to_dict(),
            'assistant_response': assistant_response
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return {'success': False, 'error': str(e)}

@app.post("/api/brainstorm/idea/add")
async def add_text_idea(request: Request):
    """Add a text-based idea (without audio transcription)."""
    data = await request.json()
    session_id = data.get('session_id')
    text = data.get('text')
    with_assistant = data.get('with_assistant', False)  # Optional assistant response
    
    if not session_id or session_id not in brainstorm_sessions:
        return {'success': False, 'error': 'Invalid session'}
    
    if not text or not text.strip():
        return {'success': False, 'error': 'No text provided'}
    
    try:
        # Get session components
        brainstorm_session, organizer, assistant, storage = get_or_create_brainstorm_session(session_id)
        
        # Add transcript
        organizer.add_transcript(text, "user")
        
        # Add idea
        idea = organizer.add_idea(text, source=IdeaSource.USER)
        
        # Save immediately (fast response)
        storage.save_session(brainstorm_session)
        
        logger.info(f"Added text idea: {text[:50]}...")
        
        # Get assistant response only if requested (slow, optional)
        assistant_response = None
        if with_assistant and assistant:
            try:
                assistant_response = assistant.process_user_input(text)
                if assistant_response:
                    organizer.add_transcript(assistant_response, "assistant")
                    storage.save_session(brainstorm_session)
            except Exception as e:
                logger.error(f"Assistant error: {e}")
                # Don't fail the whole request if assistant fails
        
        return {
            'success': True,
            'text': text,
            'idea': idea.to_dict(),
            'assistant_response': assistant_response
        }
        
    except Exception as e:
        logger.error(f"Error adding text idea: {e}")
        return {'success': False, 'error': str(e)}

@app.post("/api/brainstorm/idea/analyze")
async def analyze_brainstorm_idea(request: Request):
    """Get AI analysis for a specific idea."""
    data = await request.json()
    session_id = data.get('session_id')
    idea_id = data.get('idea_id')
    text = data.get('text')
    
    if not session_id or session_id not in brainstorm_sessions:
        return {'success': False, 'error': 'Invalid session'}
    
    if not text:
        return {'success': False, 'error': 'No text provided'}
    
    try:
        # Get session components
        brainstorm_session, organizer, assistant, storage = get_or_create_brainstorm_session(session_id)
        
        # Check if assistant exists
        if not assistant:
            logger.error("No AI assistant available for session")
            return {
                'success': False,
                'error': 'No AI assistant configured. Please check LLM backend.'
            }
        
        # Get AI analysis
        logger.info(f"Analyzing idea with {current_llm_type}: {text[:50]}...")
        assistant_response = assistant.process_user_input(text)
        
        if not assistant_response:
            logger.warning(f"AI assistant returned empty response for: {text[:50]}")
            return {
                'success': False,
                'error': 'AI assistant returned no response. Check LLM backend logs.'
            }
        
        # Save transcript
        organizer.add_transcript(f"[Analyzing idea: {text}]", "user")
        organizer.add_transcript(assistant_response, "assistant")
        storage.save_session(brainstorm_session)
        
        logger.info(f"Successfully analyzed idea {idea_id} with {current_llm_type}")
        
        return {
            'success': True,
            'idea_id': idea_id,
            'assistant_response': assistant_response
        }
        
    except Exception as e:
        logger.error(f"Error analyzing idea with {current_llm_type}: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}

@app.post("/api/brainstorm/idea/tag")
async def tag_brainstorm_idea(request: Request):
    """Tag a brainstorming idea."""
    data = await request.json()
    session_id = data.get('session_id')
    idea_id = data.get('idea_id')
    tags = data.get('tags', [])
    
    if session_id not in brainstorm_sessions:
        return {'success': False, 'error': 'Session not found'}
    
    organizer = brainstorm_organizers[session_id]
    success = organizer.tag_idea(idea_id, tags)
    
    if success:
        storage = brainstorm_storages[session_id]
        storage.save_session(brainstorm_sessions[session_id])
    
    return {'success': success}

@app.post("/api/brainstorm/idea/promote")
async def promote_brainstorm_idea(request: Request):
    """Promote a brainstorming idea."""
    data = await request.json()
    session_id = data.get('session_id')
    idea_id = data.get('idea_id')
    
    if session_id not in brainstorm_sessions:
        return {'success': False, 'error': 'Session not found'}
    
    organizer = brainstorm_organizers[session_id]
    success = organizer.promote_idea(idea_id)
    
    if success:
        storage = brainstorm_storages[session_id]
        storage.save_session(brainstorm_sessions[session_id])
    
    return {'success': success}

@app.post("/api/brainstorm/idea/delete")
async def delete_brainstorm_idea(request: Request):
    """Delete a brainstorming idea."""
    data = await request.json()
    session_id = data.get('session_id')
    idea_id = data.get('idea_id')
    
    if session_id not in brainstorm_sessions:
        return {'success': False, 'error': 'Session not found'}
    
    organizer = brainstorm_organizers[session_id]
    success = organizer.delete_idea(idea_id, soft=True)
    
    if success:
        storage = brainstorm_storages[session_id]
        storage.save_session(brainstorm_sessions[session_id])
    
    return {'success': success}

@app.post("/api/brainstorm/action/add")
async def add_brainstorm_action(request: Request):
    """Add a brainstorming action item."""
    data = await request.json()
    session_id = data.get('session_id')
    text = data.get('text')
    
    if session_id not in brainstorm_sessions:
        return {'success': False, 'error': 'Session not found'}
    
    organizer = brainstorm_organizers[session_id]
    action = organizer.add_action(text)
    
    storage = brainstorm_storages[session_id]
    storage.save_session(brainstorm_sessions[session_id])
    
    return {'success': True, 'action': action.to_dict()}

@app.get("/api/brainstorm/export/{session_id}/{format}")
async def export_brainstorm_session(session_id: str, format: str):
    """Export brainstorming session."""
    if session_id not in brainstorm_sessions:
        return {'success': False, 'error': 'Session not found'}
    
    brainstorm_session = brainstorm_sessions[session_id]
    storage = brainstorm_storages[session_id]
    
    results = export_session(brainstorm_session, storage.base_dir, [format])
    
    if results and format in results:
        return {'success': True, 'file': str(results[format])}
    else:
        return {'success': False, 'error': 'Export failed'}

# ============================================
# STARTUP AND SHUTDOWN
# ============================================
# Lifespan manager is defined above with the FastAPI app initialization

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Unified Assistant")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(level=getattr(__import__('logging'), log_level))
    
    logger.info("Starting Unified Assistant")
    logger.info(f"Host: {args.host}, Port: {args.port}")
    
    # Run the application
    uvicorn.run(
        "unified_app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=log_level.lower()
    )

if __name__ == "__main__":
    main()
