"""Core Devices Company API routes for web UI."""
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

from app.product_company.core_devices_company import (
    CoreDevicesCompany, OwnerDecision, Phase, ProductProject, PrimaryNeed
)
from app.database import get_db
from app.models import CoreDevicesProject as CDCProject

logger = structlog.get_logger(__name__)

router = APIRouter()

# Store active projects in memory (loaded from database)
active_projects: Dict[str, Dict[str, Any]] = {}

# Store phase execution status for background tasks
phase_execution_status: Dict[str, Dict[str, Any]] = {}


async def save_project_to_db(project_id: str, project_data: Dict[str, Any], db: AsyncSession) -> None:
    """Save project state to database."""
    try:
        # Convert ProductProject dataclass to dict if needed
        company = project_data.get("company")
        project_state = None
        if company and hasattr(company, 'project') and company.project:
            pp = company.project
            project_state = {
                "product_idea": pp.product_idea,
                "primary_need": pp.primary_need.value if pp.primary_need else None,
                "category": pp.category.value if pp.category else None,
                "constraints": pp.constraints,
                "idea_dossier": pp.idea_dossier,
                "concept_pack": pp.concept_pack,
                "benchmark_data": pp.benchmark_data,
                "user_journeys": pp.user_journeys,
                "interaction_blueprint": pp.interaction_blueprint,
                "system_architecture": pp.system_architecture,
                "friction_budget": pp.friction_budget,
                "detailed_design": pp.detailed_design,
                "prototype_plan": pp.prototype_plan,
                "usability_metrics": pp.usability_metrics,
                "validation_plan": pp.validation_plan,
                "manufacturing_plan": pp.manufacturing_plan,
                "serviceability_plan": pp.serviceability_plan,
                "positioning": pp.positioning,
                "launch_package": pp.launch_package,
                "current_phase": pp.current_phase.value if hasattr(pp.current_phase, 'value') else str(pp.current_phase),
                "status": pp.status,
                "owner_edits": pp.owner_edits,
            }
        
        # Check if project exists
        result = await db.execute(
            select(CDCProject).where(CDCProject.id == project_id)
        )
        db_project = result.scalar_one_or_none()
        
        if db_project:
            # Update existing project
            db_project.product_idea = project_data.get("product_idea")
            db_project.primary_need = project_data.get("primary_need")
            db_project.research_mode = project_data.get("research_mode", False)
            db_project.research_scope = project_data.get("research_scope")
            db_project.constraints = project_data.get("constraints", {})
            db_project.output_directory = project_data.get("output_directory", "product_outputs")
            db_project.model = project_data.get("model", "qwen3:30b")
            db_project.ceo_model = project_data.get("ceo_model")
            db_project.current_phase = project_data.get("current_phase")
            db_project.status = project_data.get("status", "in_progress")
            db_project.project_data = project_state
            db_project.artifacts = project_data.get("artifacts", {})
            db_project.owner_decisions = project_data.get("owner_decisions", {})
            db_project.chat_log = project_data.get("chat_log", [])
            db_project.pdf_report = project_data.get("pdf_report")  # Store PDF bytes
            db_project.last_activity_at = datetime.utcnow()
            db_project.updated_at = datetime.utcnow()
        else:
            # Create new project
            db_project = CDCProject(
                id=project_id,
                product_idea=project_data.get("product_idea"),
                primary_need=project_data.get("primary_need"),
                research_mode=project_data.get("research_mode", False),
                research_scope=project_data.get("research_scope"),
                constraints=project_data.get("constraints", {}),
                output_directory=project_data.get("output_directory", "product_outputs"),
                model=project_data.get("model", "qwen3:30b"),
                ceo_model=project_data.get("ceo_model"),
                current_phase=project_data.get("current_phase", "strategy_idea_intake"),
                status=project_data.get("status", "in_progress"),
                project_data=project_state,
                artifacts=project_data.get("artifacts", {}),
                owner_decisions=project_data.get("owner_decisions", {}),
                chat_log=project_data.get("chat_log", []),
                pdf_report=project_data.get("pdf_report"),
                progress_log=[],
                error_log=[],
            )
            db.add(db_project)
        
        await db.commit()
        logger.info(f"Saved Core Devices project {project_id} to database")
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save project {project_id} to database", error=str(e), exc_info=True)
        raise


async def load_project_from_db(project_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """Load project from database and recreate company instance."""
    try:
        result = await db.execute(
            select(CDCProject).where(CDCProject.id == project_id)
        )
        db_project = result.scalar_one_or_none()
        
        if not db_project:
            return None
        
        # Recreate company with saved models
        model = db_project.model or "gemma2:2b"
        company = CoreDevicesCompany(model=model)
        
        # Restore project state
        if db_project.project_data:
            pp_data = db_project.project_data
            
            # Parse primary need
            primary_need = None
            if pp_data.get("primary_need"):
                try:
                    primary_need = PrimaryNeed(pp_data["primary_need"])
                except:
                    primary_need = None
            
            # Parse category
            from app.product_company.core_devices_company import ProductCategory
            category = None
            if pp_data.get("category"):
                try:
                    category = ProductCategory(pp_data["category"])
                except:
                    category = None
            
            company.project = ProductProject(
                product_idea=pp_data.get("product_idea", ""),
                primary_need=primary_need,
                category=category,
                constraints=pp_data.get("constraints", {}),
                idea_dossier=pp_data.get("idea_dossier"),
                concept_pack=pp_data.get("concept_pack"),
                benchmark_data=pp_data.get("benchmark_data"),
                user_journeys=pp_data.get("user_journeys"),
                interaction_blueprint=pp_data.get("interaction_blueprint"),
                system_architecture=pp_data.get("system_architecture"),
                friction_budget=pp_data.get("friction_budget"),
                detailed_design=pp_data.get("detailed_design"),
                prototype_plan=pp_data.get("prototype_plan"),
                usability_metrics=pp_data.get("usability_metrics"),
                validation_plan=pp_data.get("validation_plan"),
                manufacturing_plan=pp_data.get("manufacturing_plan"),
                serviceability_plan=pp_data.get("serviceability_plan"),
                positioning=pp_data.get("positioning"),
                launch_package=pp_data.get("launch_package"),
                current_phase=Phase(pp_data.get("current_phase", "strategy_idea_intake")),
                status=pp_data.get("status", "in_progress"),
                owner_edits=pp_data.get("owner_edits", {}),
            )
        else:
            # Create new project if no saved state
            primary_need = None
            if db_project.primary_need:
                try:
                    primary_need = PrimaryNeed(db_project.primary_need)
                except:
                    primary_need = None
                    
            company.project = ProductProject(
                product_idea=db_project.product_idea,
                primary_need=primary_need,
                constraints=db_project.constraints or {},
            )
        
        # Reconstruct project data dict
        project_data = {
            "company": company,
            "product_idea": db_project.product_idea or "",
            "primary_need": db_project.primary_need or "",
            "research_mode": db_project.research_mode or False,
            "research_scope": db_project.research_scope or "",
            "constraints": db_project.constraints or {},
            "output_directory": db_project.output_directory,
            "model": db_project.model,
            "ceo_model": db_project.ceo_model,
            "current_phase": db_project.current_phase,
            "status": db_project.status,
            "owner_decisions": db_project.owner_decisions or {},
            "artifacts": db_project.artifacts or {},
            "chat_log": db_project.chat_log or [],
            "pdf_report": db_project.pdf_report,  # Restore PDF bytes
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
            "message": message,
            "phase": phase
        })


async def log_error(project_id: str, error: str, phase: Optional[str] = None, db: AsyncSession = None) -> None:
    """Log error for a project."""
    if project_id in active_projects:
        if "error_log" not in active_projects[project_id]:
            active_projects[project_id]["error_log"] = []
        
        active_projects[project_id]["error_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "phase": phase
        })


# Pydantic models for API
class CoreDevicesProjectCreate(BaseModel):
    """Create Core Devices project request."""
    product_idea: Optional[str] = ""  # Optional - Research Team will discover if empty
    primary_need: Optional[str] = ""  # Optional - Research Team will identify if empty
    research_mode: bool = False  # If True, start with Research Phase (Phase 0)
    research_scope: Optional[str] = ""  # Scope for research (e.g., "health devices", "energy solutions")
    constraints: Optional[Dict[str, Any]] = {}
    model: str = "gemma2:2b"  # Use small model by default (low memory requirements)
    ceo_model: Optional[str] = None
    output_directory: str = "product_outputs"


class CoreDevicesProjectResponse(BaseModel):
    """Core Devices project response."""
    id: str
    product_idea: str
    primary_need: Optional[str]
    research_mode: bool = False
    research_scope: Optional[str] = ""
    current_phase: str
    status: str
    created_at: str
    updated_at: str
    artifacts: Optional[Dict[str, Any]]
    chat_log: Optional[List[Dict[str, Any]]]


class OwnerDecisionRequest(BaseModel):
    """Owner decision request."""
    decision: str  # approve, request_changes, stop
    feedback: Optional[str] = None


@router.post("/api/core-devices/projects", response_model=CoreDevicesProjectResponse)
async def create_core_devices_project(project: CoreDevicesProjectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new Core Devices project."""
    try:
        # Create unique ID
        project_id = str(uuid.uuid4())
        
        # Create company instance
        model = project.model or "gemma2:2b"
        ceo_model = project.ceo_model or model
        company = CoreDevicesCompany(model=model)
        
        # Initialize project (can be with or without idea)
        await company.initialize_project(
            idea=project.product_idea or "",
            primary_need=project.primary_need or "",
            constraints=project.constraints
        )
        
        # Determine starting phase
        starting_phase = "research_discovery" if project.research_mode or not project.product_idea else "strategy_idea_intake"
        
        # Create project data
        project_data = {
            "company": company,
            "product_idea": project.product_idea or "",
            "primary_need": project.primary_need or "",
            "research_mode": project.research_mode,
            "research_scope": project.research_scope or "",
            "constraints": project.constraints,
            "output_directory": project.output_directory,
            "model": model,
            "ceo_model": ceo_model,
            "current_phase": starting_phase,
            "status": "in_progress",
            "owner_decisions": {},
            "artifacts": {},
            "chat_log": [],
            "progress_log": [],
            "error_log": [],
        }
        
        # Store in memory
        active_projects[project_id] = project_data
        
        # Save to database
        await save_project_to_db(project_id, project_data, db)
        
        # Get CEO greeting
        greeting = await company.ceo.greet_owner()
        project_data["chat_log"].append({
            "from_agent": "CEO_Agent",
            "to_agent": "OWNER",
            "phase": "initialization",
            "content": greeting,
            "timestamp": datetime.utcnow().isoformat(),
            "message_type": "owner_request"
        })
        
        await save_project_to_db(project_id, project_data, db)
        
        return CoreDevicesProjectResponse(
            id=project_id,
            product_idea=project.product_idea or "",
            primary_need=project.primary_need or "",
            research_mode=project.research_mode,
            research_scope=project.research_scope or "",
            current_phase=starting_phase,  # Use actual starting phase (research_discovery or strategy_idea_intake)
            status="in_progress",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            artifacts={},
            chat_log=project_data["chat_log"]
        )
    except Exception as e:
        logger.error("Failed to create Core Devices project", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/api/core-devices/projects/{project_id}", response_model=CoreDevicesProjectResponse)
async def get_core_devices_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get Core Devices project status."""
    # Load from memory or database
    if project_id not in active_projects:
        project_data = await load_project_from_db(project_id, db)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        active_projects[project_id] = project_data
    
    project_data = active_projects[project_id]
    
    return CoreDevicesProjectResponse(
        id=project_id,
        product_idea=project_data.get("product_idea", ""),
        primary_need=project_data.get("primary_need"),
        research_mode=project_data.get("research_mode", False),
        research_scope=project_data.get("research_scope", ""),
        current_phase=project_data.get("current_phase", "strategy_idea_intake"),
        status=project_data.get("status", "in_progress"),
        created_at=project_data.get("created_at", datetime.utcnow().isoformat()),
        updated_at=project_data.get("updated_at", datetime.utcnow().isoformat()),
        artifacts=project_data.get("artifacts", {}),
        chat_log=project_data.get("chat_log", [])
    )


async def _execute_phase_background(project_id: str, current_phase: Phase, db: AsyncSession):
    """Execute phase in background with real-time chat transparency."""
    logger.info(f"Background: Executing phase {current_phase.value} for project {project_id}")
    
    status_key = f"{project_id}_{current_phase.value}"
    phase_execution_status[status_key] = {
        "status": "running",
        "phase": current_phase.value,
        "started_at": datetime.utcnow().isoformat(),
        "error": None
    }
    
    try:
        # Get project data
        project_data = active_projects.get(project_id)
        if not project_data:
            raise ValueError(f"Project {project_id} not found in active projects")
        
        company: CoreDevicesCompany = project_data["company"]
        
        await log_progress(project_id, f"Starting phase: {current_phase.value}", current_phase.value, db)
        
        # Get initial chat log count to track new messages
        initial_chat_count = len(project_data["chat_log"])
        
        # Create a callback to save messages in real-time
        async def save_new_messages():
            """Periodically check and save new messages from message bus."""
            if company and company.bus:
                new_messages = company.bus.get_messages_since(initial_chat_count)
                if new_messages:
                    for msg in new_messages:
                        project_data["chat_log"].append(msg.to_dict())
                    # Save to DB immediately for real-time updates
                    await save_project_to_db(project_id, project_data, db)
        
        # Start a background task to periodically save messages
        import asyncio
        
        async def message_saver():
            while phase_execution_status.get(status_key, {}).get("status") == "running":
                await save_new_messages()
                await asyncio.sleep(2)  # Check every 2 seconds
        
        saver_task = asyncio.create_task(message_saver())
        
        try:
            # Execute the appropriate phase
            result = None
            if current_phase == Phase.STRATEGY_IDEA_INTAKE:
                result = await company.execute_phase_1()
            elif current_phase == Phase.CONCEPT_DIFFERENTIATION:
                result = await company.execute_phase_2()
            elif current_phase == Phase.UX_SYSTEM_DESIGN:
                result = await company.execute_phase_3()
            elif current_phase == Phase.DETAILED_ENGINEERING:
                result = await company.execute_phase_4()
            elif current_phase == Phase.VALIDATION_INDUSTRIALIZATION:
                result = await company.execute_phase_5()
            elif current_phase == Phase.POSITIONING_LAUNCH:
                result = await company.execute_phase_6()
            else:
                raise ValueError(f"Unknown phase: {current_phase}")
        finally:
            # Ensure final messages are saved
            await save_new_messages()
            saver_task.cancel()
            try:
                await saver_task
            except asyncio.CancelledError:
                pass
        
        # Update project data with final results
        project_data["artifacts"][current_phase.value] = result.get("artifacts", {})
        # Add any remaining messages not yet saved
        final_messages = result.get("chat_log", [])
        existing_timestamps = {msg.get("timestamp") for msg in project_data["chat_log"]}
        for msg in final_messages:
            if msg.get("timestamp") not in existing_timestamps:
                project_data["chat_log"].append(msg)
        
        # Save to database
        await save_project_to_db(project_id, project_data, db)
        
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


@router.post("/api/core-devices/projects/{project_id}/execute-phase")
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
        
        # Start background task
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


@router.get("/api/core-devices/projects/{project_id}/phase-status")
async def get_phase_status(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get status of phase execution."""
    # Load from database if not in memory
    if project_id not in active_projects:
        project_data = await load_project_from_db(project_id, db)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        active_projects[project_id] = project_data
    
    project_data = active_projects[project_id]
    current_phase = project_data.get("current_phase", "strategy_idea_intake")
    status_key = f"{project_id}_{current_phase}"
    
    if status_key in phase_execution_status:
        return phase_execution_status[status_key]
    
    return {
        "status": "idle",
        "phase": current_phase,
        "error": None
    }


@router.post("/api/core-devices/projects/{project_id}/owner-decision")
async def submit_owner_decision(
    project_id: str,
    decision: OwnerDecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit Owner decision on current phase."""
    # Load from database if not in memory
    if project_id not in active_projects:
        project_data = await load_project_from_db(project_id, db)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        active_projects[project_id] = project_data
    
    project_data = active_projects[project_id]
    current_phase = project_data.get("current_phase")
    
    try:
        decision_enum = OwnerDecision(decision.decision.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid decision: {decision.decision}")
    
    # Store decision
    if "owner_decisions" not in project_data:
        project_data["owner_decisions"] = {}
    
    project_data["owner_decisions"][current_phase] = {
        "decision": decision_enum.value,
        "feedback": decision.feedback,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add to chat log
    project_data["chat_log"].append({
        "from_agent": "OWNER",
        "to_agent": "CEO_Agent",
        "phase": current_phase,
        "content": f"Decision: {decision_enum.value}" + (f"\nFeedback: {decision.feedback}" if decision.feedback else ""),
        "timestamp": datetime.utcnow().isoformat(),
        "message_type": "owner_response"
    })
    
    if decision_enum == OwnerDecision.APPROVE:
        # Move to next phase
        phase_order = [
            "strategy_idea_intake",
            "concept_differentiation",
            "ux_system_design",
            "detailed_engineering",
            "validation_industrialization",
            "positioning_launch",
            "complete"
        ]
        
        current_idx = phase_order.index(current_phase) if current_phase in phase_order else 0
        if current_idx < len(phase_order) - 1:
            project_data["current_phase"] = phase_order[current_idx + 1]
            if project_data["current_phase"] == "complete":
                project_data["status"] = "complete"
        else:
            project_data["status"] = "complete"
    
    elif decision_enum == OwnerDecision.STOP:
        project_data["status"] = "stopped"
    
    # Save to database
    await save_project_to_db(project_id, project_data, db)
    
    return {
        "success": True,
        "decision": decision_enum.value,
        "new_phase": project_data.get("current_phase"),
        "status": project_data.get("status")
    }


@router.get("/api/core-devices/projects/{project_id}/chat-log")
async def get_chat_log(project_id: str, phase: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Get chat log for project."""
    # Load from database if not in memory
    if project_id not in active_projects:
        project_data = await load_project_from_db(project_id, db)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        active_projects[project_id] = project_data
    
    project_data = active_projects[project_id]
    chat_log = project_data.get("chat_log", [])
    
    # Filter by phase if specified
    if phase:
        chat_log = [msg for msg in chat_log if msg.get("phase") == phase]
    
    return {"chat_log": chat_log}


@router.get("/api/core-devices/projects")
async def list_core_devices_projects(db: AsyncSession = Depends(get_db)):
    """List all Core Devices projects from database."""
    try:
        result = await db.execute(
            select(CDCProject).order_by(CDCProject.updated_at.desc())
        )
        projects = result.scalars().all()
        
        return {
            "projects": [
                {
                    "id": p.id,
                    "product_idea": p.product_idea,
                    "primary_need": p.primary_need,
                    "current_phase": p.current_phase,
                    "status": p.status,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                }
                for p in projects
            ]
        }
    except Exception as e:
        logger.error("Failed to list projects", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/core-devices/projects/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a Core Devices project."""
    try:
        # Remove from memory
        if project_id in active_projects:
            del active_projects[project_id]
        
        # Delete from database
        result = await db.execute(
            select(CDCProject).where(CDCProject.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if project:
            await db.delete(project)
            await db.commit()
            return {"success": True, "message": "Project deleted"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete project", error=str(e), exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/core-devices/projects/{project_id}/execute-research")
async def execute_research_phase(project_id: str, db: AsyncSession = Depends(get_db)):
    """Execute Phase 0: Research & Discovery.
    
    Research Team discovers product opportunities and generates PDF report.
    """
    try:
        # Check if project exists
        if project_id not in active_projects:
            # Try loading from database
            loaded_data = await load_project_from_db(project_id, db)
            if loaded_data:
                active_projects[project_id] = loaded_data
            else:
                raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = active_projects[project_id]
        company = project_data.get("company")
        
        if not company:
            raise HTTPException(status_code=500, detail="Company instance not found")
        
        # Execute research phase in background with live chat updates
        async def execute_research_bg():
            try:
                phase_execution_status[project_id] = {"status": "running", "phase": "research_discovery"}
                
                # Get initial chat log count to track new messages
                initial_chat_count = len(project_data["chat_log"])
                
                # Create a callback to save messages in real-time
                async def save_new_messages():
                    """Periodically check and save new messages from message bus."""
                    if company and company.bus:
                        new_messages = company.bus.get_messages_since(initial_chat_count)
                        if new_messages:
                            for msg in new_messages:
                                project_data["chat_log"].append(msg.to_dict())
                            # Save to DB immediately for real-time updates
                            await save_project_to_db(project_id, project_data, db)
                
                research_scope = project_data.get("research_scope", "")
                
                # Execute research with periodic message saves
                import asyncio
                
                # Start a background task to periodically save messages
                async def message_saver():
                    while phase_execution_status.get(project_id, {}).get("status") == "running":
                        await save_new_messages()
                        await asyncio.sleep(2)  # Check every 2 seconds
                
                saver_task = asyncio.create_task(message_saver())
                
                try:
                    result = await company.execute_phase_0(research_scope=research_scope)
                finally:
                    # Ensure final messages are saved
                    await save_new_messages()
                    saver_task.cancel()
                    try:
                        await saver_task
                    except asyncio.CancelledError:
                        pass
                
                # Store PDF report
                if "pdf_report" in result:
                    project_data["pdf_report"] = result["pdf_report"]
                
                # Update project data with final results
                project_data["artifacts"]["research_discovery"] = result.get("artifacts", {})
                # Add any remaining messages not yet saved
                final_messages = result.get("chat_log", [])
                existing_timestamps = {msg.get("timestamp") for msg in project_data["chat_log"]}
                for msg in final_messages:
                    if msg.get("timestamp") not in existing_timestamps:
                        project_data["chat_log"].append(msg)
                
                project_data["current_phase"] = "research_discovery"
                
                # Final save with all data
                await save_project_to_db(project_id, project_data, db)
                
                logger.info(f"Research phase completed for project {project_id}, artifacts saved: {len(result.get('artifacts', {}))}")
                
                phase_execution_status[project_id] = {
                    "status": "completed",
                    "phase": "research_discovery",
                    "artifacts": result.get("artifacts", {}),
                    "completed_at": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                phase_execution_status[project_id] = {
                    "status": "failed",
                    "phase": "research_discovery",
                    "error": str(e)
                }
                await log_error(project_id, str(e), "research_discovery", db)
        
        # Run in background
        asyncio.create_task(execute_research_bg())
        
        return {"message": "Research phase started", "project_id": project_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute research phase for project {project_id}", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/core-devices/projects/{project_id}/research-report")
async def download_research_report(project_id: str, db: AsyncSession = Depends(get_db)):
    """Download the PDF research report."""
    from fastapi.responses import Response
    
    try:
        # Check if project exists
        if project_id not in active_projects:
            # Try loading from database
            loaded_data = await load_project_from_db(project_id, db)
            if loaded_data:
                active_projects[project_id] = loaded_data
            else:
                raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = active_projects[project_id]
        
        # Get PDF report from artifacts
        pdf_report = project_data.get("pdf_report")
        
        if not pdf_report:
            # Try to get from artifacts
            research_artifacts = project_data.get("artifacts", {}).get("research_discovery", {})
            if "pdf_report" in research_artifacts:
                pdf_report = research_artifacts["pdf_report"]
        
        if not pdf_report:
            raise HTTPException(status_code=404, detail="Research report not found. Execute research phase first.")
        
        # Return PDF file
        return Response(
            content=pdf_report,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=research_report_{project_id[:8]}.pdf"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download research report for project {project_id}", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class ResearchApprovalRequest(BaseModel):
    """Research approval request."""
    approve: bool  # True to use recommendation, False to reject
    provide_own_idea: bool = False  # If rejecting, provide own idea
    product_idea: Optional[str] = None  # User's own idea
    primary_need: Optional[str] = None  # User's primary need


@router.post("/api/core-devices/projects/{project_id}/approve-research")
async def approve_research_recommendation(
    project_id: str,
    request: ResearchApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """Approve or reject the Research Team's recommendation."""
    try:
        # Check if project exists
        if project_id not in active_projects:
            loaded_data = await load_project_from_db(project_id, db)
            if loaded_data:
                active_projects[project_id] = loaded_data
            else:
                raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = active_projects[project_id]
        company = project_data.get("company")
        
        if not company:
            raise HTTPException(status_code=500, detail="Company instance not found")
        
        if request.approve:
            # Apply research recommendation
            research_artifacts = project_data.get("artifacts", {}).get("research_discovery", {})
            recommendation = research_artifacts.get("recommendation", {})
            
            if not recommendation:
                raise HTTPException(status_code=400, detail="No research recommendation found")
            
            company.apply_research_recommendation(recommendation)
            
            # Update project data
            recommended_product = recommendation.get("recommended_product", {})
            project_data["product_idea"] = recommended_product.get("product_concept", "")
            project_data["primary_need"] = recommended_product.get("primary_need", "")
            project_data["current_phase"] = "strategy_idea_intake"
            
            # Log owner decision
            project_data["owner_decisions"]["research_discovery"] = {
                "decision": "approve",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            message = "Research recommendation approved. Proceeding to Phase 1."
            
        elif request.provide_own_idea and request.product_idea:
            # Owner provided their own idea
            await company.initialize_project(
                idea=request.product_idea,
                primary_need=request.primary_need or "",
                constraints=project_data.get("constraints", {})
            )
            
            project_data["product_idea"] = request.product_idea
            project_data["primary_need"] = request.primary_need or ""
            project_data["current_phase"] = "strategy_idea_intake"
            
            # Log owner decision
            project_data["owner_decisions"]["research_discovery"] = {
                "decision": "provide_own_idea",
                "product_idea": request.product_idea,
                "primary_need": request.primary_need,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            message = "Owner provided own product idea. Proceeding to Phase 1."
        
        else:
            # Rejected without providing idea
            project_data["status"] = "stopped"
            project_data["owner_decisions"]["research_discovery"] = {
                "decision": "reject",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            message = "Research recommendation rejected. Project stopped."
        
        await save_project_to_db(project_id, project_data, db)
        
        return {
            "message": message,
            "project_id": project_id,
            "current_phase": project_data["current_phase"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve research for project {project_id}", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
