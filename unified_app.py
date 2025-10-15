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
from audio.mic import MicrophoneRecorder
from audio.vad import SilenceDetector
from stt.base import STTBackend
from stt.whisper_local import WhisperLocalSTT
from stt.vosk_local import VoskSTT
from stt.whisper_cloud import WhisperAPISTT
from llm.base import LLMBackend
from llm.openai_client import OpenAIClient
from llm.http_client import HTTPClient
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

def init_backends():
    """Initialize STT and LLM backends."""
    global stt_backend, llm_backend
    
    # Initialize STT
    try:
        stt_backend = WhisperLocalSTT(
            model_size=config.get('stt.whisper_model', 'base'),
            sample_rate=16000
        )
        logger.info("STT backend initialized")
    except Exception as e:
        logger.error(f"Failed to initialize STT: {e}")
    
    # Initialize LLM
    try:
        if config.openai_api_key:
            llm_backend = OpenAIClient(
                api_key=config.openai_api_key,
                model=config.openai_model
            )
            logger.info("LLM backend initialized")
        else:
            logger.warning("No OpenAI API key configured")
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")

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
        
        # Create assistant
        assistant = None
        if llm_backend:
            assistant = BrainstormAssistant(llm_backend, organizer)
        
        # Store
        brainstorm_sessions[session_id] = brainstorm_session
        brainstorm_organizers[session_id] = organizer
        brainstorm_assistants[session_id] = assistant
        brainstorm_storages[session_id] = storage
        
        logger.info(f"Created brainstorm session: {session_id} for project: {project_name}")
    
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
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "modes": ["brainstorm", "personal"],
        "services": {
            "stt": stt_backend is not None,
            "llm": llm_backend is not None,
            "database": True,
            "scheduler": True
        }
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
        
        # Decode audio
        audio_bytes = base64.b64decode(audio_base64)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        
        logger.info(f"Received audio: {len(audio_array)} samples, duration: {len(audio_array)/16000:.2f}s")
        
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
