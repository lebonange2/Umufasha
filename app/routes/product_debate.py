"""API routes for product debate system."""
import uuid
import csv
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import structlog

from app.product_debate.debate import DebateOrchestrator
from app.product_debate.storage import SessionStorage
from app.product_debate.exporter import SessionExporter
from app.product_debate.data import KNOWN_PRODUCTS, get_products_by_category, load_products_from_csv
from app.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/product-debate", tags=["product-debate"])

storage = SessionStorage()
exporter = SessionExporter()

# Store running debates for cancellation
running_debates: Dict[str, Any] = {}  # session_id -> orchestrator


class DebateRequest(BaseModel):
    """Request to start a debate session."""
    seed: int = 42
    temperature: float = 0.7
    max_rounds: int = 6
    core_market: Optional[str] = None
    category: Optional[str] = None
    agent_a_model: str = "qwen3:30b"  # Local model for Agent A
    agent_b_model: str = "qwen3:30b"  # Local model for Agent B


class DebateResponse(BaseModel):
    """Response from debate session."""
    session_id: str
    status: str
    message: str


@router.post("/start", response_model=DebateResponse)
async def start_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    """Start a new debate session."""
    # Check if Ollama is running (for local models)
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=2.0)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Ollama service is not responding. Make sure Ollama is running: ollama serve"
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=400,
            detail="Ollama service is not running. Start it with: ollama serve"
        )
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Determine core market and category
    core_market = request.core_market or "Consumer Electronics"
    category = request.category or "Portable Power"
    
    # Get known products
    known_products = get_products_by_category(category)
    if not known_products:
        known_products = KNOWN_PRODUCTS[:5]  # Use first 5 as default
    
    # Create orchestrator
    orchestrator = DebateOrchestrator(
        session_id=session_id,
        seed=request.seed,
        temperature=request.temperature,
        max_rounds=request.max_rounds,
        core_market=core_market,
        category=category,
        known_products=known_products,
        agent_a_model=request.agent_a_model,
        agent_b_model=request.agent_b_model
    )
    
    # Store orchestrator for potential cancellation
    running_debates[session_id] = orchestrator
    
    # Save initial session state immediately so UI can poll
    storage.save_session(orchestrator.session)
    
    # Run debate in background
    async def run_debate_task():
        try:
            session = await orchestrator.run_debate()
            
            # Final save
            storage.save_session(session)
            
            # Export results
            session_path = storage.get_session_path(session_id)
            exports = exporter.export_session(session, session_path)
            
            # Print taxonomy to stdout if available (exact format as required)
            if session.taxonomy:
                print("\n=== TAXONOMY ===\n")
                for level, items in session.taxonomy.items():
                    if items:
                        print(f"• {level}")
                        for item in items:
                            print(f"  • {item}")
        except Exception as e:
            logger.error("Debate task failed", error=str(e), session_id=session_id)
        finally:
            # Remove from running debates
            running_debates.pop(session_id, None)
    
    # Start background task
    background_tasks.add_task(run_debate_task)
    
    # Return immediately so UI can poll
    return DebateResponse(
        session_id=session_id,
        status="started",
        message="Debate started. Poll /sessions/{session_id}/status for updates."
    )


@router.post("/start-with-csv")
async def start_debate_with_csv(
    background_tasks: BackgroundTasks,
    seed: int = Form(42),
    temperature: float = Form(0.7),
    max_rounds: int = Form(6),
    core_market: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    agent_a_model: str = Form("qwen3:30b"),
    agent_b_model: str = Form("qwen3:30b"),
    csv_file: UploadFile = File(...)
):
    """Start a debate session with products from CSV."""
    # Check if Ollama is running (for local models)
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=2.0)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Ollama service is not responding. Make sure Ollama is running: ollama serve"
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=400,
            detail="Ollama service is not running. Start it with: ollama serve"
        )
    
    # Save uploaded file temporarily
    temp_path = Path(f"/tmp/{csv_file.filename}")
    with open(temp_path, "wb") as f:
        content = await csv_file.read()
        f.write(content)
    
    # Load products from CSV
    known_products = load_products_from_csv(str(temp_path))
    if not known_products:
        raise HTTPException(
            status_code=400,
            detail="No products loaded from CSV file"
        )
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Determine core market and category
    core_market = core_market or "Custom Market"
    category = category or "Custom Category"
    
    # Create orchestrator
    orchestrator = DebateOrchestrator(
        session_id=session_id,
        seed=seed,
        temperature=temperature,
        max_rounds=max_rounds,
        core_market=core_market,
        category=category,
        known_products=known_products,
        agent_a_model=agent_a_model,
        agent_b_model=agent_b_model
    )
    
    # Store orchestrator for potential cancellation
    running_debates[session_id] = orchestrator
    
    # Save initial session state immediately so UI can poll
    storage.save_session(orchestrator.session)
    
    # Run debate in background
    async def run_debate_task():
        try:
            session = await orchestrator.run_debate()
            
            # Final save
            storage.save_session(session)
            
            # Export results
            session_path = storage.get_session_path(session_id)
            exports = exporter.export_session(session, session_path)
            
            # Print taxonomy to stdout if available (exact format as required)
            if session.taxonomy:
                print("\n=== TAXONOMY ===\n")
                for level, items in session.taxonomy.items():
                    if items:
                        print(f"• {level}")
                        for item in items:
                            print(f"  • {item}")
        except Exception as e:
            logger.error("Debate task failed", error=str(e), session_id=session_id)
        finally:
            # Remove from running debates
            running_debates.pop(session_id, None)
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
    
    # Start background task
    background_tasks.add_task(run_debate_task)
    
    # Return immediately so UI can poll
    return DebateResponse(
        session_id=session_id,
        status="started",
        message="Debate started. Poll /sessions/{session_id}/status for updates."
    )


@router.get("/sessions")
async def list_sessions():
    """List all debate sessions with metadata."""
    session_ids = storage.list_sessions()
    sessions_data = []
    
    for session_id in session_ids:
        session = storage.load_session(session_id)
        if session:
            sessions_data.append({
                "session_id": session_id,
                "created_at": session.created_at.isoformat() if hasattr(session.created_at, 'isoformat') else str(session.created_at),
                "rounds_completed": len(session.rounds),
                "max_rounds": session.max_rounds,
                "core_market": session.core_market,
                "category": session.category,
                "go_threshold_met": session.go_threshold_met,
                "has_final_concept": session.final_concept is not None
            })
    
    return {"sessions": sessions_data}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a debate session."""
    session = storage.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Return session with all rounds
    session_dict = session.to_dict()
    return session_dict


@router.get("/sessions/{session_id}/export/{export_type}")
async def download_export(session_id: str, export_type: str):
    """Download an export file."""
    session = storage.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_path = storage.get_session_path(session_id)
    exports = exporter.export_session(session, session_path)
    
    if export_type not in exports:
        raise HTTPException(status_code=404, detail=f"Export type '{export_type}' not found")
    
    file_path = exports[export_type]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@router.get("/sessions/{session_id}/export-conversation")
async def export_conversation(session_id: str, format: str = "text"):
    """Export conversation in various formats (text, markdown, json)."""
    session = storage.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    from app.product_debate.exporter import export_conversation_text, export_conversation_markdown
    from fastapi.responses import Response
    
    if format == "markdown":
        content = export_conversation_markdown(session)
        media_type = "text/markdown"
        filename = f"conversation_{session_id}.md"
    elif format == "json":
        import json
        content = json.dumps(session.to_dict(), indent=2)
        media_type = "application/json"
        filename = f"conversation_{session_id}.json"
    else:  # text
        content = export_conversation_text(session)
        media_type = "text/plain"
        filename = f"conversation_{session_id}.txt"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/known-products")
async def get_known_products(category: Optional[str] = None):
    """Get known products, optionally filtered by category."""
    if category:
        products = get_products_by_category(category)
    else:
        products = KNOWN_PRODUCTS
    return {"products": products}


@router.get("/sessions/{session_id}/status")
async def get_debate_status(session_id: str):
    """Get current debate status and latest round."""
    session = storage.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if debate is still running
    is_running = session_id in running_debates
    
    # Get latest round
    latest_round = session.rounds[-1] if session.rounds else None
    
    # Determine status
    if not is_running and (session.go_threshold_met or len(session.rounds) >= session.max_rounds):
        status = "completed"
    elif not is_running:
        status = "stopped"
    else:
        status = "in_progress"
    
    return {
        "session_id": session_id,
        "rounds_completed": len(session.rounds),
        "max_rounds": session.max_rounds,
        "go_threshold_met": session.go_threshold_met,
        "latest_round": latest_round.to_dict() if latest_round else None,
        "final_concept": session.final_concept.to_dict() if session.final_concept else None,
        "status": status,
        "is_running": is_running
    }


@router.get("/available-models")
async def get_available_models():
    """Get list of available local models (Ollama)."""
    # Try to get list from Ollama
    import httpx
    local_models = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                local_models = [
                    {"value": model["name"], "label": f"{model['name']} (Local)", "provider": "local"}
                    for model in data.get("models", [])
                ]
    except:
        pass
    
    # Default models if Ollama not available or empty
    if not local_models:
        local_models = [
            {"value": "qwen3:30b", "label": "Qwen3 30B (Local)", "provider": "local"},
            {"value": "llama3:latest", "label": "Llama 3 (Local)", "provider": "local"},
            {"value": "llama3.2", "label": "Llama 3.2 (Local)", "provider": "local"},
            {"value": "mistral", "label": "Mistral (Local)", "provider": "local"},
            {"value": "codellama", "label": "CodeLlama (Local)", "provider": "local"},
        ]
    
    return {
        "all_models": local_models,
        "local": local_models
    }


@router.post("/sessions/{session_id}/stop")
async def stop_debate(session_id: str):
    """Stop a running debate session."""
    if session_id not in running_debates:
        raise HTTPException(status_code=404, detail="Debate session not found or not running")
    
    orchestrator = running_debates[session_id]
    orchestrator.cancelled = True
    
    # Save current state
    storage.save_session(orchestrator.session)
    
    # Remove from running debates
    running_debates.pop(session_id, None)
    
    logger.info("Debate stopped", session_id=session_id)
    
    return {
        "session_id": session_id,
        "status": "stopped",
        "message": "Debate stopped successfully"
    }

