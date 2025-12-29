"""Book Publishing House API routes for web UI."""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import structlog
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.book_writer.ferrari_company import (
    FerrariBookCompany, OwnerDecision, Phase, BookProject
)
from app.database import get_db
from app.models import BookPublishingHouseProject as BPHProject

logger = structlog.get_logger(__name__)

router = APIRouter()

# Store active projects in memory (loaded from database)
active_projects: Dict[str, Dict[str, Any]] = {}

# Store phase execution status for background tasks
phase_execution_status: Dict[str, Dict[str, Any]] = {}


async def save_project_to_db(project_id: str, project_data: Dict[str, Any], db: AsyncSession) -> None:
    """Save project state to database."""
    try:
        # Convert BookProject dataclass to dict if needed
        company = project_data.get("company")
        project_state = None
        if company and hasattr(company, 'project') and company.project:
            bp = company.project
            project_state = {
                "title": bp.title,
                "premise": bp.premise,
                "target_word_count": bp.target_word_count,
                "audience": bp.audience,
                "genre": bp.genre,
                "reference_documents": bp.reference_documents,
                "book_brief": bp.book_brief,
                "world_dossier": bp.world_dossier,
                "character_bible": bp.character_bible,
                "plot_arc": bp.plot_arc,
                "outline": bp.outline,
                "draft_chapters": bp.draft_chapters,
                "full_draft": bp.full_draft,
                "revision_report": bp.revision_report,
                "formatted_manuscript": bp.formatted_manuscript,
                "launch_package": bp.launch_package,
                "current_phase": bp.current_phase.value if hasattr(bp.current_phase, 'value') else str(bp.current_phase),
                "status": bp.status,
                "owner_edits": bp.owner_edits,
            }
        
        # Check if project exists
        result = await db.execute(
            select(BPHProject).where(BPHProject.id == project_id)
        )
        db_project = result.scalar_one_or_none()
        
        if db_project:
            # Update existing project
            db_project.title = project_data.get("title")
            db_project.premise = project_data.get("premise")
            db_project.target_word_count = project_data.get("target_word_count")
            db_project.audience = project_data.get("audience")
            db_project.output_directory = project_data.get("output_directory", "book_outputs")
            db_project.model = project_data.get("model", "qwen3:30b")
            db_project.ceo_model = project_data.get("ceo_model")
            db_project.current_phase = project_data.get("current_phase")
            db_project.status = project_data.get("status", "in_progress")
            db_project.project_data = project_state
            db_project.artifacts = project_data.get("artifacts", {})
            db_project.owner_decisions = project_data.get("owner_decisions", {})
            db_project.chat_log = project_data.get("chat_log", [])
            db_project.reference_documents = project_data.get("reference_documents", [])
            db_project.last_activity_at = datetime.utcnow()
            db_project.updated_at = datetime.utcnow()
        else:
            # Create new project
            db_project = BPHProject(
                id=project_id,
                title=project_data.get("title"),
                premise=project_data.get("premise"),
                target_word_count=project_data.get("target_word_count"),
                audience=project_data.get("audience"),
                output_directory=project_data.get("output_directory", "book_outputs"),
                model=project_data.get("model", "qwen3:30b"),
                ceo_model=project_data.get("ceo_model"),
                current_phase=project_data.get("current_phase", "strategy_concept"),
                status=project_data.get("status", "in_progress"),
                project_data=project_state,
                artifacts=project_data.get("artifacts", {}),
                owner_decisions=project_data.get("owner_decisions", {}),
                chat_log=project_data.get("chat_log", []),
                reference_documents=project_data.get("reference_documents", []),
                progress_log=[],
                error_log=[],
            )
            db.add(db_project)
        
        await db.commit()
        logger.info(f"Saved project {project_id} to database")
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save project {project_id} to database", error=str(e), exc_info=True)
        raise


async def load_project_from_db(project_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """Load project from database and recreate company instance."""
    try:
        result = await db.execute(
            select(BPHProject).where(BPHProject.id == project_id)
        )
        db_project = result.scalar_one_or_none()
        
        if not db_project:
            return None
        
        # Recreate company with saved models
        model = db_project.model or "qwen3:30b"
        ceo_model = db_project.ceo_model or model
        company = FerrariBookCompany(model=model, ceo_model=ceo_model)
        
        # Restore project state
        if db_project.project_data:
            bp_data = db_project.project_data
            company.project = BookProject(
                title=bp_data.get("title"),
                premise=bp_data.get("premise", ""),
                target_word_count=bp_data.get("target_word_count"),
                audience=bp_data.get("audience"),
                genre=bp_data.get("genre"),
                reference_documents=bp_data.get("reference_documents", []),
                book_brief=bp_data.get("book_brief"),
                world_dossier=bp_data.get("world_dossier"),
                character_bible=bp_data.get("character_bible"),
                plot_arc=bp_data.get("plot_arc"),
                outline=bp_data.get("outline"),
                draft_chapters=bp_data.get("draft_chapters", {}),
                full_draft=bp_data.get("full_draft"),
                revision_report=bp_data.get("revision_report"),
                formatted_manuscript=bp_data.get("formatted_manuscript"),
                launch_package=bp_data.get("launch_package"),
                current_phase=Phase(bp_data.get("current_phase", "strategy_concept")),
                status=bp_data.get("status", "in_progress"),
                owner_edits=bp_data.get("owner_edits", {}),
            )
        else:
            # Create new project if no saved state
            company.project = BookProject(
                title=db_project.title,
                premise=db_project.premise,
                target_word_count=db_project.target_word_count,
                audience=db_project.audience,
                reference_documents=db_project.reference_documents or [],
            )
        
        # Reconstruct project data dict
        project_data = {
            "company": company,
            "title": db_project.title,
            "premise": db_project.premise,
            "target_word_count": db_project.target_word_count,
            "audience": db_project.audience,
            "output_directory": db_project.output_directory,
            "reference_documents": db_project.reference_documents or [],
            "model": db_project.model,
            "ceo_model": db_project.ceo_model,
            "current_phase": db_project.current_phase,
            "status": db_project.status,
            "owner_decisions": db_project.owner_decisions or {},
            "artifacts": db_project.artifacts or {},
            "chat_log": db_project.chat_log or [],
            "progress_log": db_project.progress_log or [],
            "error_log": db_project.error_log or [],
            "created_at": db_project.created_at.isoformat() if db_project.created_at else datetime.utcnow().isoformat(),
            "updated_at": db_project.updated_at.isoformat() if db_project.updated_at else datetime.utcnow().isoformat(),
        }
        
        return project_data
    except Exception as e:
        logger.error(f"Failed to load project {project_id} from database", error=str(e), exc_info=True)
        return None


async def log_progress(project_id: str, message: str, phase: Optional[str] = None, db: AsyncSession = None) -> None:
    """Log progress entry for a project."""
    if project_id in active_projects:
        if "progress_log" not in active_projects[project_id]:
            active_projects[project_id]["progress_log"] = []
        active_projects[project_id]["progress_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "phase": phase or active_projects[project_id].get("current_phase"),
            "message": message,
        })
    
    if db:
        try:
            result = await db.execute(
                select(BPHProject).where(BPHProject.id == project_id)
            )
            db_project = result.scalar_one_or_none()
            if db_project:
                progress_log = db_project.progress_log or []
                progress_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase": phase or db_project.current_phase,
                    "message": message,
                })
                db_project.progress_log = progress_log
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log progress for project {project_id}", error=str(e))


async def log_error(project_id: str, error: str, phase: Optional[str] = None, db: AsyncSession = None) -> None:
    """Log error entry for a project."""
    if project_id in active_projects:
        if "error_log" not in active_projects[project_id]:
            active_projects[project_id]["error_log"] = []
        active_projects[project_id]["error_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "phase": phase or active_projects[project_id].get("current_phase"),
            "error": str(error),
        })
    
    if db:
        try:
            result = await db.execute(
                select(BPHProject).where(BPHProject.id == project_id)
            )
            db_project = result.scalar_one_or_none()
            if db_project:
                error_log = db_project.error_log or []
                error_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase": phase or db_project.current_phase,
                    "error": str(error),
                })
                db_project.error_log = error_log
                db_project.status = "error"
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log error for project {project_id}", error=str(e))


class BookPublishingHouseProjectCreate(BaseModel):
    """Create Book Publishing House project request."""
    title: Optional[str] = None
    premise: str
    target_word_count: Optional[int] = None
    audience: Optional[str] = None
    output_directory: str = "book_outputs"
    reference_documents: Optional[List[str]] = None  # List of document IDs
    model: Optional[str] = "qwen3:30b"  # Model to use for worker agents: llama3:latest or qwen3:30b
    ceo_model: Optional[str] = None  # Model to use for CEO/manager agents: llama3:latest or qwen3:30b. If None, uses same as model.


class PhaseDecision(BaseModel):
    """Owner decision for a phase."""
    decision: str  # "approve", "request_changes", "stop"
    modified_artifacts: Optional[Dict[str, Any]] = None  # Optional edited artifacts from user


class BookPublishingHouseProjectResponse(BaseModel):
    """Book Publishing House project response."""
    project_id: str
    title: Optional[str]
    premise: str
    current_phase: str
    status: str
    output_directory: str
    reference_documents: Optional[List[str]] = None
    model: Optional[str] = "qwen3:30b"  # Model being used for worker agents
    ceo_model: Optional[str] = None  # Model being used for CEO/manager agents


@router.post("/api/ferrari-company/projects", response_model=BookPublishingHouseProjectResponse)
async def create_book_publishing_house_project(project: BookPublishingHouseProjectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new Book Publishing House project."""
    try:
        # Validate input
        if not project.premise or not project.premise.strip():
            raise HTTPException(status_code=400, detail="Premise is required")
        
        project_id = str(uuid.uuid4())
        
        # Create company instance with selected models
        try:
            model = project.model or "qwen3:30b"
            # Validate model
            if model not in ["llama3:latest", "qwen3:30b"]:
                model = "qwen3:30b"  # Fall back to default
            
            ceo_model = project.ceo_model
            # Validate CEO model if provided
            if ceo_model and ceo_model not in ["llama3:latest", "qwen3:30b"]:
                ceo_model = None  # Fall back to using worker model
            
            company = FerrariBookCompany(model=model, ceo_model=ceo_model)
        except Exception as e:
            logger.error("Failed to initialize FerrariBookCompany", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to initialize book company: {str(e)}")
        
        # Initialize project
        try:
            company.project = BookProject(
                title=project.title,
                premise=project.premise,
                target_word_count=project.target_word_count,
                audience=project.audience,
                reference_documents=project.reference_documents or []
            )
        except Exception as e:
            logger.error("Failed to create BookProject", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")
        
        # Store project
        model = project.model or "qwen3:30b"
        if model not in ["llama3:latest", "qwen3:30b"]:
            model = "qwen3:30b"
        
        ceo_model = project.ceo_model or model
        if ceo_model not in ["llama3:latest", "qwen3:30b"]:
            ceo_model = model
        
        project_data = {
            "company": company,
            "title": project.title,
            "premise": project.premise,
            "target_word_count": project.target_word_count,
            "audience": project.audience,
            "output_directory": project.output_directory,
            "reference_documents": project.reference_documents or [],
            "model": model,
            "ceo_model": ceo_model,
            "current_phase": Phase.STRATEGY_CONCEPT.value,
            "status": "in_progress",
            "owner_decisions": {},
            "artifacts": {},
            "chat_log": [],
            "progress_log": [],
            "error_log": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        active_projects[project_id] = project_data
        
        # Save to database
        await save_project_to_db(project_id, project_data, db)
        await log_progress(project_id, f"Project created: {project.title or 'Untitled'}", Phase.STRATEGY_CONCEPT.value, db)
        
        # Initialize Neo4j graph for this project
        # Do this in background to not block project creation
        try:
            from app.graph.repository import GraphRepository
            # Try to create project node - if it fails, it's non-critical
            try:
                GraphRepository.create_project(
                    project_id=project_id,
                    title=project.title or "Untitled",
                    genre=None
                )
                logger.info(f"Initialized Neo4j graph for project {project_id}")
            except Exception as graph_err:
                # Log but don't fail - graph will be initialized on first access
                logger.warning(
                    f"Failed to initialize Neo4j graph for project {project_id} (non-critical)", 
                    error=str(graph_err)
                )
        except ImportError:
            # Neo4j not installed - this is okay, graph features just won't work
            logger.info(f"Neo4j not available, skipping graph initialization for project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to initialize Neo4j graph for project {project_id}", error=str(e))
            # Don't fail project creation if graph init fails
        
        logger.info(f"Created Book Publishing House project {project_id}")
        
        return BookPublishingHouseProjectResponse(
            project_id=project_id,
            title=project.title,
            premise=project.premise,
            current_phase=Phase.STRATEGY_CONCEPT.value,
            status="in_progress",
            output_directory=project.output_directory,
            reference_documents=project.reference_documents,
            model=model,
            ceo_model=ceo_model
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create Book Publishing House project", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/api/ferrari-company/projects/{project_id}", response_model=BookPublishingHouseProjectResponse)
async def get_book_publishing_house_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get Book Publishing House project status."""
    # Load from memory or database
    if project_id not in active_projects:
        project_data = await load_project_from_db(project_id, db)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        active_projects[project_id] = project_data
    else:
        project_data = active_projects[project_id]
    
    return BookPublishingHouseProjectResponse(
        project_id=project_id,
        title=project_data["title"],
        premise=project_data["premise"],
        current_phase=project_data["current_phase"],
        status=project_data["status"],
        output_directory=project_data["output_directory"],
        reference_documents=project_data.get("reference_documents", []),
        model=project_data.get("model", "qwen3:30b"),
        ceo_model=project_data.get("ceo_model")
    )


async def _save_mid_phase_progress(project_id: str, project_data: Dict[str, Any], db: AsyncSession = None) -> None:
    """Save progress during phase execution (e.g., when a chapter is approved)."""
    try:
        if db:
            await save_project_to_db(project_id, project_data, db)
        # Also update in-memory cache
        active_projects[project_id] = project_data
    except Exception as e:
        logger.error(f"Failed to save mid-phase progress for project {project_id}", error=str(e), exc_info=True)


async def _execute_phase_background(project_id: str, current_phase: Phase, db: AsyncSession = None):
    """Background task to execute phase without blocking HTTP request."""
    # Load from database if not in memory
    if project_id not in active_projects and db:
        project_data = await load_project_from_db(project_id, db)
        if project_data:
            active_projects[project_id] = project_data
    
    project_data = active_projects.get(project_id)
    if not project_data:
        logger.error(f"Project {project_id} not found in background task")
        return
    
    company = project_data["company"]
    status_key = f"{project_id}_{current_phase.value}"
    
    # Create progress callback for mid-phase saves
    async def mid_phase_callback(message: str, sub_item: Optional[str] = None):
        """Callback to save progress during phase execution."""
        progress_msg = message
        if sub_item:
            progress_msg = f"{message} ({sub_item})"
        await log_progress(project_id, progress_msg, current_phase.value, db)
        # Save project state
        project_data["company"] = company
        await _save_mid_phase_progress(project_id, project_data, db)
    
    # Attach callback to company for mid-phase saves
    company._mid_phase_save_callback = mid_phase_callback
    
    try:
        # Mark as running
        phase_execution_status[status_key] = {
            "status": "running",
            "phase": current_phase.value,
            "started_at": datetime.utcnow().isoformat(),
            "error": None
        }
        
        await log_progress(project_id, f"Starting phase: {current_phase.value}", current_phase.value, db)
        logger.info(f"Background: Executing phase {current_phase.value} for project {project_id}")
        
        # Execute phase (same as CLI) - no timeout in background
        await company._execute_phase(current_phase)
        
        # Update project state
        project_data["company"] = company
        project_data["current_phase"] = current_phase.value
        
        # Save to database
        if db:
            await save_project_to_db(project_id, project_data, db)
        
        # Sync to Neo4j graph
        try:
            from app.graph.sync import GraphSyncer
            GraphSyncer.sync_project_to_graph(project_id, project_data)
        except Exception as e:
            logger.warning(f"Failed to sync to graph", error=str(e), project_id=project_id)
        
        # Mark as completed
        phase_execution_status[status_key] = {
            "status": "completed",
            "phase": current_phase.value,
            "started_at": phase_execution_status[status_key]["started_at"],
            "completed_at": datetime.utcnow().isoformat(),
            "error": None
        }
        
        await log_progress(project_id, f"Completed phase: {current_phase.value}", current_phase.value, db)
        logger.info(f"Background: Phase {current_phase.value} completed for project {project_id}")
        
    except Exception as phase_error:
        error_msg = str(phase_error)
        logger.error(f"Background phase execution error: {error_msg}", error=error_msg, exc_info=True)
        await log_error(project_id, error_msg, current_phase.value, db)
        # Mark as failed
        phase_execution_status[status_key] = {
            "status": "failed",
            "phase": current_phase.value,
            "started_at": phase_execution_status.get(status_key, {}).get("started_at", datetime.utcnow().isoformat()),
            "error": error_msg
        }
        # Save error state to database
        if db and project_id in active_projects:
            project_data["status"] = "error"
            await save_project_to_db(project_id, project_data, db)
    finally:
        # Clean up callback
        if hasattr(company, '_mid_phase_save_callback'):
            delattr(company, '_mid_phase_save_callback')


@router.post("/api/ferrari-company/projects/{project_id}/execute-phase")
async def execute_phase(project_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Start phase execution in background and return immediately."""
    # Load from database if not in memory
    if project_id not in active_projects:
        project_data = await load_project_from_db(project_id, db)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        active_projects[project_id] = project_data
    
    project_data = active_projects[project_id]
    
    # Validate project state
    if project_data["status"] == "complete":
        raise HTTPException(status_code=400, detail="Project is already complete")
    if project_data["status"] == "stopped":
        raise HTTPException(status_code=400, detail="Project has been stopped")
    
    try:
        # Get current phase
        try:
            current_phase = Phase(project_data["current_phase"])
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid phase: {project_data.get('current_phase')}", error=str(e))
            raise HTTPException(status_code=400, detail=f"Invalid phase: {project_data.get('current_phase')}")
        
        # Check if already running
        status_key = f"{project_id}_{current_phase.value}"
        if status_key in phase_execution_status:
            existing_status = phase_execution_status[status_key]
            if existing_status.get("status") == "running":
                return {
                    "success": True,
                    "status": "running",
                    "message": "Phase execution already in progress",
                    "phase": current_phase.value
                }
        
        # Start background task with db session
        background_tasks.add_task(_execute_phase_background, project_id, current_phase, db)
        
        logger.info(f"Started background phase execution for {current_phase.value} in project {project_id}")
        
        return {
            "success": True,
            "status": "started",
            "message": "Phase execution started in background",
            "phase": current_phase.value
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start phase execution", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start phase execution: {str(e)}")


@router.get("/api/ferrari-company/projects/{project_id}/phase-status")
async def get_phase_status(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get status of phase execution."""
    # Load from database if not in memory
    if project_id not in active_projects:
        project_data = await load_project_from_db(project_id, db)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        active_projects[project_id] = project_data
    
    project_data = active_projects[project_id]
    current_phase = project_data.get("current_phase")
    
    if not current_phase:
        return {
            "status": "unknown",
            "phase": None,
            "message": "No phase information available"
        }
    
    status_key = f"{project_id}_{current_phase}"
    execution_status = phase_execution_status.get(status_key, {})
    
    if execution_status.get("status") == "completed":
        # Phase completed, get artifacts
        company = project_data["company"]
        current_phase_enum = Phase(current_phase)
        
        # Get artifacts for presentation
        artifacts = {}
        summary_parts = []
        
        try:
            if current_phase_enum == Phase.STRATEGY_CONCEPT:
                artifacts = {"book_brief": company.project.book_brief or {}}
                summary_parts.append("CPSO has created the initial book brief.")
            elif current_phase_enum == Phase.EARLY_DESIGN:
                artifacts = {
                    "world_dossier": company.project.world_dossier or {},
                    "character_bible": company.project.character_bible or {},
                    "plot_arc": company.project.plot_arc or {}
                }
                summary_parts.append("Story Design Director has completed world and character design.")
            elif current_phase_enum == Phase.DETAILED_ENGINEERING:
                outline = company.project.outline or []
                if not isinstance(outline, list):
                    outline = []
                artifacts = {"outline": outline}
                summary_parts.append("Narrative Engineering Director has created the full hierarchical outline.")
            elif current_phase_enum == Phase.PROTOTYPES_TESTING:
                artifacts = {
                    "draft_chapters": company.project.draft_chapters or {},
                    "revision_report": company.project.revision_report or {}
                }
                summary_parts.append("Production and QA teams have completed draft and testing.")
            elif current_phase_enum == Phase.INDUSTRIALIZATION_PACKAGING:
                artifacts = {"formatted_manuscript": company.project.formatted_manuscript or ""}
                summary_parts.append("Formatting and export agents have prepared the production-ready manuscript.")
            elif current_phase_enum == Phase.MARKETING_LAUNCH:
                artifacts = {"launch_package": company.project.launch_package or {}}
                summary_parts.append("Launch Director has created the complete launch package.")
        except Exception as artifact_error:
            logger.warning(f"Error getting artifacts: {str(artifact_error)}", exc_info=True)
        
        summary = " ".join(summary_parts) if summary_parts else f"Phase {current_phase.replace('_', ' ').title()} completed."
        
        # Get chat log
        try:
            phase_chat_log = company.message_bus.get_chat_log(current_phase_enum)
            if not isinstance(phase_chat_log, list):
                phase_chat_log = []
        except Exception as log_error:
            logger.warning(f"Error getting chat log: {str(log_error)}", exc_info=True)
            phase_chat_log = []
        
        # Clear status after returning
        phase_execution_status.pop(status_key, None)
        
        return {
            "status": "completed",
            "phase": current_phase,
            "summary": summary,
            "artifacts": artifacts,
            "chat_log": phase_chat_log,
            "ready_for_decision": True
        }
    elif execution_status.get("status") == "failed":
        error_msg = execution_status.get("error", "Unknown error")
        # Clear status
        phase_execution_status.pop(status_key, None)
        raise HTTPException(status_code=500, detail=f"Phase execution failed: {error_msg}")
    elif execution_status.get("status") == "running":
        return {
            "status": "running",
            "phase": current_phase,
            "message": "Phase execution in progress",
            "started_at": execution_status.get("started_at")
        }
    else:
        return {
            "status": "not_started",
            "phase": current_phase,
            "message": "Phase execution not started"
        }


@router.post("/api/ferrari-company/projects/{project_id}/decide")
async def make_decision(project_id: str, decision: PhaseDecision, db: AsyncSession = Depends(get_db)):
    """Make owner decision on current phase."""
    # Load from database if not in memory
    if project_id not in active_projects:
        project_data = await load_project_from_db(project_id, db)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        active_projects[project_id] = project_data
    
    project_data = active_projects[project_id]
    
    # Validate project state
    if project_data["status"] == "complete":
        raise HTTPException(status_code=400, detail="Project is already complete")
    if project_data["status"] == "stopped":
        raise HTTPException(status_code=400, detail="Project has been stopped")
    
    company = project_data["company"]
    
    try:
        # Validate decision
        try:
            owner_decision = OwnerDecision(decision.decision)
        except (ValueError, KeyError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid decision: {decision.decision}")
        
        # Get current phase
        try:
            current_phase = Phase(project_data["current_phase"])
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid phase: {project_data.get('current_phase')}", error=str(e))
            raise HTTPException(status_code=400, detail=f"Invalid phase: {project_data.get('current_phase')}")
        
        # Store decision
        project_data["owner_decisions"][current_phase.value] = decision.decision
        
        if owner_decision == OwnerDecision.STOP:
            project_data["status"] = "stopped"
            await log_progress(project_id, f"Project stopped by owner at phase {current_phase.value}", current_phase.value, db)
            await save_project_to_db(project_id, project_data, db)
            logger.info(f"Project {project_id} stopped by owner")
            return {
                "success": True,
                "decision": decision.decision,
                "status": "stopped",
                "message": "Project stopped by owner"
            }
        elif owner_decision == OwnerDecision.REQUEST_CHANGES:
            # Re-run phase - no timeout, let it run until completion or user cancellation
            await log_progress(project_id, f"Requesting changes for phase {current_phase.value}, re-executing", current_phase.value, db)
            try:
                await company._execute_phase(current_phase)
            except Exception as e:
                error_msg = str(e)
                await log_error(project_id, f"Error re-executing phase: {error_msg}", current_phase.value, db)
                logger.error(f"Error re-executing phase: {error_msg}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to re-execute phase: {error_msg}"
                )
            
            project_data["company"] = company
            await log_progress(project_id, f"Phase {current_phase.value} re-executed with changes", current_phase.value, db)
            await save_project_to_db(project_id, project_data, db)
            return {
                "success": True,
                "decision": decision.decision,
                "message": "Phase re-executed with changes",
                "ready_for_decision": True
            }
        else:  # APPROVE
            # Apply modified artifacts if provided by user
            if decision.modified_artifacts:
                try:
                    # Update project artifacts based on current phase
                    if current_phase == Phase.STRATEGY_CONCEPT:
                        if 'book_brief' in decision.modified_artifacts:
                            company.project.book_brief = decision.modified_artifacts['book_brief']
                    elif current_phase == Phase.EARLY_DESIGN:
                        if 'world_dossier' in decision.modified_artifacts:
                            company.project.world_dossier = decision.modified_artifacts['world_dossier']
                        if 'character_bible' in decision.modified_artifacts:
                            company.project.character_bible = decision.modified_artifacts['character_bible']
                        if 'plot_arc' in decision.modified_artifacts:
                            company.project.plot_arc = decision.modified_artifacts['plot_arc']
                    elif current_phase == Phase.DETAILED_ENGINEERING:
                        if 'outline' in decision.modified_artifacts:
                            company.project.outline = decision.modified_artifacts['outline']
                    elif current_phase == Phase.PROTOTYPES_TESTING:
                        if 'draft_chapters' in decision.modified_artifacts:
                            company.project.draft_chapters = decision.modified_artifacts['draft_chapters']
                        if 'revision_report' in decision.modified_artifacts:
                            company.project.revision_report = decision.modified_artifacts['revision_report']
                    elif current_phase == Phase.INDUSTRIALIZATION_PACKAGING:
                        if 'formatted_manuscript' in decision.modified_artifacts:
                            company.project.formatted_manuscript = decision.modified_artifacts['formatted_manuscript']
                    elif current_phase == Phase.MARKETING_LAUNCH:
                        if 'launch_package' in decision.modified_artifacts:
                            company.project.launch_package = decision.modified_artifacts['launch_package']
                    
                    logger.info(f"Applied user-modified artifacts for phase {current_phase.value} in project {project_id}")
                except Exception as artifact_error:
                    logger.warning(f"Error applying modified artifacts: {str(artifact_error)}", exc_info=True)
                    # Continue anyway - user edits are optional
            
            # Move to next phase
            phases = [
                Phase.STRATEGY_CONCEPT,
                Phase.EARLY_DESIGN,
                Phase.DETAILED_ENGINEERING,
                Phase.PROTOTYPES_TESTING,
                Phase.INDUSTRIALIZATION_PACKAGING,
                Phase.MARKETING_LAUNCH
            ]
            
            try:
                current_index = phases.index(current_phase)
            except ValueError:
                logger.error(f"Current phase {current_phase.value} not in phases list")
                raise HTTPException(status_code=500, detail="Invalid phase state")
            
            if current_index < len(phases) - 1:
                next_phase = phases[current_index + 1]
                project_data["current_phase"] = next_phase.value
                await log_progress(project_id, f"Phase {current_phase.value} approved, moving to {next_phase.value}", next_phase.value, db)
                logger.info(f"Project {project_id} approved phase {current_phase.value}, moving to {next_phase.value}")
            else:
                # All phases complete
                project_data["status"] = "complete"
                project_data["current_phase"] = Phase.COMPLETE.value
                await log_progress(project_id, "All phases completed successfully", Phase.COMPLETE.value, db)
                
                # Save final files
                try:
                    await save_final_files(project_id, company, project_data)
                except Exception as save_error:
                    error_msg = str(save_error)
                    await log_error(project_id, f"Error saving final files: {error_msg}", Phase.COMPLETE.value, db)
                    logger.error(f"Error saving final files: {error_msg}", exc_info=True)
                    # Don't fail the request, but log the error
                    # Files can be regenerated if needed
            
            await save_project_to_db(project_id, project_data, db)
            return {
                "success": True,
                "decision": decision.decision,
                "next_phase": project_data["current_phase"],
                "status": project_data["status"],
                "message": f"Phase approved. Moving to {project_data['current_phase']}"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process decision", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process decision: {str(e)}")


def _generate_plain_text(final_package: Dict[str, Any]) -> str:
    """Generate well-structured plain text from final package for audio conversion.
    
    The text is structured with:
    - Clear chapter headings
    - Proper paragraph breaks
    - Clean formatting (no markdown)
    - Punctuation optimized for TTS
    """
    lines = []
    
    # Title
    title = final_package.get("title", "Untitled Book")
    lines.append(title.upper())
    lines.append("")
    lines.append("=" * len(title))
    lines.append("")
    
    # Premise (if available)
    premise = final_package.get("premise")
    if premise:
        lines.append("PREMISE")
        lines.append("-" * 40)
        lines.append("")
        lines.append(_clean_text_for_audio(premise))
        lines.append("")
        lines.append("")
    
    # Use formatted_manuscript if available, otherwise use full_draft
    manuscript = final_package.get("formatted_manuscript") or final_package.get("full_draft")
    
    if manuscript:
        # Convert markdown to plain text
        text = _convert_markdown_to_plain_text(manuscript)
        lines.append(text)
    elif final_package.get("outline"):
        # If no manuscript, use outline as fallback
        lines.append("OUTLINE")
        lines.append("-" * 40)
        lines.append("")
        outline = final_package.get("outline", [])
        for chapter in outline:
            chapter_num = chapter.get("chapter_number", 0)
            chapter_title = chapter.get("title", "Untitled")
            lines.append(f"Chapter {chapter_num}: {chapter_title}")
            lines.append("")
            
            # Add chapter content if available
            if chapter.get("content"):
                lines.append(_clean_text_for_audio(chapter["content"]))
                lines.append("")
            elif chapter.get("sections"):
                for section in chapter.get("sections", []):
                    section_title = section.get("title", "")
                    if section_title:
                        lines.append(f"  {section_title}")
                        lines.append("")
                    if section.get("content"):
                        lines.append(_clean_text_for_audio(section["content"]))
                        lines.append("")
            lines.append("")
    
    return "\n".join(lines)


def _clean_text_for_audio(text: str) -> str:
    """Clean text for optimal audio conversion.
    
    - Removes markdown formatting
    - Removes excessive whitespace
    - Ensures proper sentence endings
    - Normalizes punctuation for TTS
    """
    if not text:
        return ""
    
    import re
    
    # Remove markdown formatting (bold, italic, code, links)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Italic
    text = re.sub(r'__([^_]+)__', r'\1', text)  # Bold alt
    text = re.sub(r'_([^_]+)_', r'\1', text)  # Italic alt
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Code
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links
    
    # Remove markdown headers (already handled in conversion)
    text = text.replace("#", "").replace("##", "").replace("###", "")
    
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
    text = re.sub(r' {2,}', ' ', text)  # Max 1 space
    text = re.sub(r'\t+', ' ', text)  # Tabs to spaces
    
    # Normalize punctuation for better TTS
    text = re.sub(r'\.{3,}', '...', text)  # Multiple dots to ellipsis
    text = re.sub(r'!{2,}', '!', text)  # Multiple exclamations to one
    text = re.sub(r'\?{2,}', '?', text)  # Multiple questions to one
    
    # Ensure sentences end with punctuation (but don't add if already has it)
    text = text.strip()
    if text and text[-1] not in '.!?;:':
        # Check if it looks like a sentence (has some content)
        if len(text) > 10:
            text += '.'
    
    return text


def _convert_markdown_to_plain_text(markdown_text: str) -> str:
    """Convert markdown to plain text optimized for audio conversion.
    
    Structure:
    - Chapter headers are clearly marked and separated
    - Sections have clear breaks
    - Paragraphs are properly spaced
    - Text flows naturally for TTS reading
    """
    if not markdown_text:
        return ""
    
    lines = []
    current_paragraph = []
    in_list = False
    
    for line in markdown_text.split('\n'):
        original_line = line
        line = line.strip()
        
        if not line:
            # Empty line - end current paragraph and list
            if current_paragraph:
                lines.append(' '.join(current_paragraph))
                current_paragraph = []
            if in_list:
                in_list = False
            lines.append("")
            continue
        
        # Handle markdown headers
        if line.startswith('#'):
            # Header - end paragraph and add header
            if current_paragraph:
                lines.append(' '.join(current_paragraph))
                current_paragraph = []
            in_list = False
            
            # Remove # symbols and clean (but don't add period to headers)
            header_text = line.lstrip('#').strip()
            # Clean markdown but preserve header formatting
            import re
            header_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', header_text)
            header_text = re.sub(r'\*([^*]+)\*', r'\1', header_text)
            header_text = re.sub(r'__([^_]+)__', r'\1', header_text)
            header_text = re.sub(r'_([^_]+)_', r'\1', header_text)
            header_text = header_text.strip()
            
            if header_text:
                # Determine header level
                header_level = len(original_line) - len(original_line.lstrip('#'))
                
                # Make headers clear for audio
                lines.append("")
                if header_level == 1:
                    # Main chapter title
                    lines.append(header_text.upper())
                    lines.append("=" * min(len(header_text), 70))
                elif header_level == 2:
                    # Section title
                    lines.append(header_text.upper())
                    lines.append("-" * min(len(header_text), 60))
                else:
                    # Subsection
                    lines.append(header_text)
                lines.append("")
            continue
        
        # Handle lists (convert to natural text)
        if line.startswith('- ') or line.startswith('* ') or line.startswith('+ '):
            if current_paragraph:
                lines.append(' '.join(current_paragraph))
                current_paragraph = []
            
            list_item = line[2:].strip()
            list_item = _clean_text_for_audio(list_item)
            if list_item:
                # Format as natural sentence
                lines.append(f"  • {list_item}")
            in_list = True
            continue
        elif line[0].isdigit() and '. ' in line[:5]:
            # Numbered list
            if current_paragraph:
                lines.append(' '.join(current_paragraph))
                current_paragraph = []
            
            list_item = line.split('. ', 1)[1] if '. ' in line else line
            list_item = _clean_text_for_audio(list_item)
            if list_item:
                lines.append(f"  {list_item}")
            in_list = True
            continue
        
        # Regular paragraph text
        if in_list:
            in_list = False
        
        # Clean and add to paragraph
        cleaned_line = _clean_text_for_audio(line)
        if cleaned_line:
            current_paragraph.append(cleaned_line)
    
    # Add remaining paragraph
    if current_paragraph:
        lines.append(' '.join(current_paragraph))
    
    # Final cleanup - ensure proper spacing
    result = '\n'.join(lines)
    # Remove excessive blank lines (max 2 consecutive)
    import re
    result = re.sub(r'\n{4,}', '\n\n\n', result)
    
    return result


async def save_final_files(project_id: str, company: FerrariBookCompany, project_data: Dict[str, Any]):
    """Save final files after completion."""
    try:
        from pathlib import Path
        import shutil
        
        output_dir = Path(project_data.get("output_directory", "book_outputs"))
        try:
            output_dir.mkdir(exist_ok=True, parents=True)
        except Exception as e:
            logger.error(f"Failed to create output directory {output_dir}: {str(e)}")
            raise
        
        # Generate safe filename
        title = project_data.get("title") or "Untitled"
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50] if safe_title else "Untitled"
        
        # Assemble final package
        try:
            final_package = company._assemble_final_package()
        except Exception as e:
            logger.error(f"Failed to assemble final package: {str(e)}", exc_info=True)
            final_package = {}
        
        try:
            chat_log = company.message_bus.get_chat_log()
            if not isinstance(chat_log, list):
                chat_log = []
        except Exception as e:
            logger.error(f"Failed to get chat log: {str(e)}", exc_info=True)
            chat_log = []
        
        # Save JSON package
        json_filename = output_dir / f"{safe_title}_package.json"
        try:
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(final_package, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save JSON package: {str(e)}", exc_info=True)
            raise
        
        # Save chat log
        chat_log_filename = output_dir / f"{safe_title}_chat_log.json"
        try:
            with open(chat_log_filename, "w", encoding="utf-8") as f:
                json.dump(chat_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save chat log: {str(e)}", exc_info=True)
            raise
        
        # Generate plain text export (well-structured for audio conversion)
        txt_filename = None
        try:
            txt_content = _generate_plain_text(final_package)
            if txt_content:
                txt_filename = output_dir / f"{safe_title}_book.txt"
                with open(txt_filename, "w", encoding="utf-8") as f:
                    f.write(txt_content)
                logger.info(f"Generated plain text export: {txt_filename}")
        except Exception as e:
            logger.warning(f"Could not generate plain text export: {str(e)}", exc_info=True)
            # Continue without plain text
        
        # Copy PDF if exists
        pdf_dest_path = None
        try:
            if isinstance(final_package, dict):
                if 'pdf_path' in final_package and final_package['pdf_path']:
                    pdf_source_path = Path(final_package['pdf_path'])
                    if pdf_source_path.exists():
                        pdf_dest_path = output_dir / f"{safe_title}_book.pdf"
                        shutil.copy2(pdf_source_path, pdf_dest_path)
                elif 'exports' in final_package and isinstance(final_package.get('exports'), dict):
                    if 'pdf_path' in final_package['exports'] and final_package['exports']['pdf_path']:
                        pdf_source_path = Path(final_package['exports']['pdf_path'])
                        if pdf_source_path.exists():
                            pdf_dest_path = output_dir / f"{safe_title}_book.pdf"
                            shutil.copy2(pdf_source_path, pdf_dest_path)
        except Exception as e:
            logger.warning(f"Could not copy PDF: {str(e)}", exc_info=True)
            # Continue without PDF
        
        # Create ZIP archive
        zip_filename = None
        try:
            import zipfile
            zip_filename = output_dir / f"{safe_title}_complete.zip"
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(json_filename, json_filename.name)
                zipf.write(chat_log_filename, chat_log_filename.name)
                if txt_filename and txt_filename.exists():
                    zipf.write(txt_filename, txt_filename.name)
                if pdf_dest_path and pdf_dest_path.exists():
                    zipf.write(pdf_dest_path, pdf_dest_path.name)
        except Exception as e:
            logger.warning(f"Could not create zip archive: {str(e)}", exc_info=True)
            # Continue without ZIP
        
        # Store file paths in project data
        project_data["files"] = {
            "json": str(json_filename.absolute()),
            "chat_log": str(chat_log_filename.absolute()),
            "txt": str(txt_filename.absolute()) if txt_filename and txt_filename.exists() else None,
            "pdf": str(pdf_dest_path.absolute()) if pdf_dest_path and pdf_dest_path.exists() else None,
            "zip": str(zip_filename.absolute()) if zip_filename and zip_filename.exists() else None
        }
        
        project_data["final_package"] = final_package
        project_data["chat_log"] = chat_log
        
        logger.info(f"Saved final files for project {project_id} to {output_dir}")
        
    except Exception as e:
        logger.error(f"Failed to save final files for project {project_id}: {str(e)}", exc_info=True)
        raise


@router.get("/api/ferrari-company/projects/{project_id}/chat-log")
async def get_chat_log(project_id: str, phase: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Get chat log for project."""
    # Load from database if not in memory
    if project_id not in active_projects:
        project_data = await load_project_from_db(project_id, db)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        active_projects[project_id] = project_data
    
    project_data = active_projects[project_id]
    company = project_data["company"]
    
    if phase:
        phase_enum = Phase(phase)
        chat_log = company.message_bus.get_chat_log(phase_enum)
    else:
        chat_log = company.message_bus.get_chat_log()
    
    return {"chat_log": chat_log}


@router.get("/api/ferrari-company/projects/{project_id}/download/{file_type}")
async def download_file(project_id: str, file_type: str, db: AsyncSession = Depends(get_db)):
    """Download generated files."""
    # Load from database if not in memory
    if project_id not in active_projects:
        project_data = await load_project_from_db(project_id, db)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        active_projects[project_id] = project_data
    
    project_data = active_projects[project_id]
    
    if project_data["status"] != "complete":
        raise HTTPException(status_code=400, detail="Project not complete yet")
    
    files = project_data.get("files", {})
    
    if file_type == "json":
        file_path = files.get("json")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="JSON file not found")
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type="application/json"
        )
    elif file_type == "txt":
        file_path = files.get("txt")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Text file not found")
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type="text/plain"
        )
    elif file_type == "pdf":
        file_path = files.get("pdf")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type="application/pdf"
        )
    elif file_type == "zip":
        file_path = files.get("zip")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="ZIP file not found")
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type="application/zip"
        )
    elif file_type == "chat-log":
        file_path = files.get("chat_log")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Chat log file not found")
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type="application/json"
        )
    else:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file_type}")


@router.get("/api/ferrari-company/projects")
async def list_book_publishing_house_projects(db: AsyncSession = Depends(get_db)):
    """List all Book Publishing House projects from database."""
    try:
        result = await db.execute(
            select(BPHProject).order_by(BPHProject.updated_at.desc())
        )
        db_projects = result.scalars().all()
        
        projects = []
        for db_project in db_projects:
            # Check for PDF file
            output_dir = Path(db_project.output_directory) / db_project.id
            pdf_path = output_dir / "book.pdf" if output_dir.exists() else None
            has_pdf = pdf_path and pdf_path.exists()
            
            projects.append({
                "project_id": db_project.id,
                "title": db_project.title or "Untitled",
                "premise": db_project.premise[:100] + "..." if len(db_project.premise) > 100 else db_project.premise,
                "status": db_project.status,
                "current_phase": db_project.current_phase,
                "has_pdf": has_pdf,
                "pdf_path": str(pdf_path) if has_pdf else None,
                "pdf_filename": pdf_path.name if has_pdf else None,
                "created_at": db_project.created_at.isoformat() if db_project.created_at else "",
                "updated_at": db_project.updated_at.isoformat() if db_project.updated_at else "",
                "model": db_project.model,
                "ceo_model": db_project.ceo_model,
            })
        
        return {"success": True, "projects": projects}
    except Exception as e:
        logger.error("Failed to list Book Publishing House projects", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ferrari-company/projects/{project_id}/files")
async def get_file_info(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get information about generated files."""
    try:
        # Load from database if not in memory
        if project_id not in active_projects:
            project_data = await load_project_from_db(project_id, db)
            if not project_data:
                raise HTTPException(status_code=404, detail="Project not found")
            active_projects[project_id] = project_data
        
        project_data = active_projects[project_id]
        
        if project_data["status"] != "complete":
            return {
                "status": "in_progress",
                "files": None
            }
        
        files = project_data.get("files", {})
        
        return {
            "status": "complete",
            "files": {
                "json": {
                    "path": files.get("json"),
                    "exists": os.path.exists(files.get("json", "")) if files.get("json") else False
                },
                "pdf": {
                    "path": files.get("pdf"),
                    "exists": os.path.exists(files.get("pdf", "")) if files.get("pdf") else False
                },
                "zip": {
                    "path": files.get("zip"),
                    "exists": os.path.exists(files.get("zip", "")) if files.get("zip") else False
                },
                "chat_log": {
                    "path": files.get("chat_log"),
                    "exists": os.path.exists(files.get("chat_log", "")) if files.get("chat_log") else False
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get file info", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/ferrari-company/projects/{project_id}/sync-graph")
async def sync_project_graph(project_id: str, db: AsyncSession = Depends(get_db)):
    """Sync project data to Neo4j graph."""
    try:
        # Load project from database
        result = await db.execute(
            select(BPHProject).where(BPHProject.project_id == project_id)
        )
        db_project = result.scalar_one_or_none()
        
        if not db_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Convert to dict format
        project_data = {
            "title": db_project.title,
            "premise": db_project.premise,
            "company": None,  # Will be loaded if needed
        }
        
        # Load company instance if project_data exists
        if db_project.project_data:
            try:
                project_data_dict = json.loads(db_project.project_data) if isinstance(db_project.project_data, str) else db_project.project_data
                # Try to reconstruct company from project_data
                # For now, just sync what we have
                pass
            except Exception as e:
                logger.warning(f"Failed to load company from project_data", error=str(e))
        
        # Sync to graph - try to get artifacts from current phase
        try:
            from app.graph.sync import GraphSyncer
            
            # Get current artifacts if available
            project_data_dict = {}
            if db_project.project_data:
                project_data_dict = json.loads(db_project.project_data) if isinstance(db_project.project_data, str) else db_project.project_data
            
            # Try to sync from artifacts
            artifacts = project_data_dict.get("artifacts", {})
            if artifacts:
                GraphSyncer.sync_from_artifacts(project_id, artifacts)
            else:
                # Fallback to basic sync
                GraphSyncer.sync_project_to_graph(project_id, project_data)
            
            return {"success": True, "message": "Graph synced successfully"}
        except Exception as e:
            logger.error(f"Failed to sync graph", error=str(e), project_id=project_id)
            # Don't fail the request if graph sync fails
            return {"success": False, "message": f"Graph sync warning: {str(e)}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing graph", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ferrari-company/projects/{project_id}/progress-report")
async def get_progress_report(project_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and download a comprehensive progress report for a project."""
    # Load from database
    result = await db.execute(
        select(BPHProject).where(BPHProject.id == project_id)
    )
    db_project = result.scalar_one_or_none()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Generate report content
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("BOOK PUBLISHING HOUSE - PROGRESS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Project Information
        report_lines.append("PROJECT INFORMATION")
        report_lines.append("-" * 80)
        report_lines.append(f"Project ID: {db_project.id}")
        report_lines.append(f"Title: {db_project.title or 'Untitled'}")
        report_lines.append(f"Premise: {db_project.premise}")
        if db_project.target_word_count:
            report_lines.append(f"Target Word Count: {db_project.target_word_count:,}")
        if db_project.audience:
            report_lines.append(f"Target Audience: {db_project.audience}")
        report_lines.append(f"Status: {db_project.status.upper()}")
        report_lines.append(f"Current Phase: {db_project.current_phase}")
        report_lines.append(f"Worker Model: {db_project.model}")
        if db_project.ceo_model:
            report_lines.append(f"CEO/Manager Model: {db_project.ceo_model}")
        report_lines.append(f"Created: {db_project.created_at}")
        report_lines.append(f"Last Updated: {db_project.updated_at}")
        report_lines.append("")
        
        # Progress Log
        if db_project.progress_log:
            report_lines.append("PROGRESS LOG")
            report_lines.append("-" * 80)
            for entry in db_project.progress_log:
                timestamp = entry.get("timestamp", "Unknown")
                phase = entry.get("phase", "Unknown")
                message = entry.get("message", "")
                report_lines.append(f"[{timestamp}] [{phase}] {message}")
            report_lines.append("")
        
        # Error Log
        if db_project.error_log:
            report_lines.append("ERROR LOG")
            report_lines.append("-" * 80)
            for entry in db_project.error_log:
                timestamp = entry.get("timestamp", "Unknown")
                phase = entry.get("phase", "Unknown")
                error = entry.get("error", "")
                report_lines.append(f"[{timestamp}] [{phase}] ERROR: {error}")
            report_lines.append("")
        
        # Phase Artifacts Summary
        if db_project.artifacts:
            report_lines.append("PHASE ARTIFACTS SUMMARY")
            report_lines.append("-" * 80)
            for phase, artifact_data in db_project.artifacts.items():
                report_lines.append(f"\nPhase: {phase}")
                if isinstance(artifact_data, dict):
                    for key, value in artifact_data.items():
                        if isinstance(value, str):
                            preview = value[:200] + "..." if len(value) > 200 else value
                            report_lines.append(f"  {key}: {preview}")
                        elif isinstance(value, (dict, list)):
                            report_lines.append(f"  {key}: {type(value).__name__} ({len(value) if isinstance(value, list) else 'N/A'} items)")
                report_lines.append("")
        
        # Owner Decisions
        if db_project.owner_decisions:
            report_lines.append("OWNER DECISIONS")
            report_lines.append("-" * 80)
            for phase, decision in db_project.owner_decisions.items():
                report_lines.append(f"{phase}: {decision}")
            report_lines.append("")
        
        # Project Data Summary
        if db_project.project_data:
            report_lines.append("PROJECT DATA SUMMARY")
            report_lines.append("-" * 80)
            pd = db_project.project_data
            if pd.get("book_brief"):
                report_lines.append("✓ Book Brief: Completed")
            if pd.get("world_dossier"):
                report_lines.append("✓ World Dossier: Completed")
            if pd.get("character_bible"):
                report_lines.append("✓ Character Bible: Completed")
            if pd.get("plot_arc"):
                report_lines.append("✓ Plot Arc: Completed")
            if pd.get("outline"):
                outline_len = len(pd.get("outline", []))
                report_lines.append(f"✓ Outline: {outline_len} chapters")
                # Show detailed chapter progress if available
                if outline_len > 0:
                    approved_count = sum(1 for ch in pd.get("outline", []) if ch.get("approved") or ch.get("status") == "approved")
                    if approved_count > 0:
                        report_lines.append(f"  - Approved chapters: {approved_count} of {outline_len}")
            if pd.get("draft_chapters"):
                chapters_count = len(pd.get("draft_chapters", {}))
                report_lines.append(f"✓ Draft Chapters: {chapters_count} chapters completed")
                # Show which chapters are completed
                if chapters_count > 0:
                    chapter_nums = sorted(pd.get("draft_chapters", {}).keys())
                    if len(chapter_nums) <= 10:
                        report_lines.append(f"  - Completed: {', '.join(map(str, chapter_nums))}")
                    else:
                        report_lines.append(f"  - Completed: {', '.join(map(str, chapter_nums[:10]))} ... and {len(chapter_nums) - 10} more")
            if pd.get("full_draft"):
                report_lines.append("✓ Full Draft: Completed")
            if pd.get("revision_report"):
                report_lines.append("✓ Revision Report: Completed")
            if pd.get("formatted_manuscript"):
                report_lines.append("✓ Formatted Manuscript: Completed")
            if pd.get("launch_package"):
                report_lines.append("✓ Launch Package: Completed")
            report_lines.append("")
        
        # Chat Log Summary
        if db_project.chat_log:
            report_lines.append("CHAT LOG SUMMARY")
            report_lines.append("-" * 80)
            report_lines.append(f"Total Messages: {len(db_project.chat_log)}")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)
        
        report_content = "\n".join(report_lines)
        
        # Return as text file
        from fastapi.responses import Response
        return Response(
            content=report_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="progress_report_{project_id}.txt"'
            }
        )
    except Exception as e:
        logger.error(f"Failed to generate progress report for project {project_id}", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate progress report: {str(e)}")

