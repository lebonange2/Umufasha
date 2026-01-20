"""Exam Generator API routes for web UI."""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, UploadFile, File
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import structlog
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.book_writer.exam_generator import (
    ExamGeneratorCompany, ExamProject, ExamProblem
)
from app.database import get_db
from app.models import ExamGeneratorProject as EGProject

logger = structlog.get_logger(__name__)

router = APIRouter()

# Store active projects in memory (loaded from database)
active_projects: Dict[str, Dict[str, Any]] = {}

# Store generation status for background tasks
generation_status: Dict[str, Dict[str, Any]] = {}

# Store phase logs for detailed tracking
phase_logs: Dict[str, List[Dict[str, Any]]] = {}


async def save_project_to_db(project_id: str, project_data: Dict[str, Any], db: AsyncSession) -> None:
    """Save project state to database."""
    try:
        # Check if project exists
        result = await db.execute(
            select(EGProject).where(EGProject.id == project_id)
        )
        db_project = result.scalar_one_or_none()
        
        if db_project:
            # Update existing project
            db_project.input_file_path = project_data.get("input_file_path", "")
            db_project.input_content = project_data.get("input_content", "")
            db_project.output_directory = project_data.get("output_directory", "exam_outputs")
            db_project.model = project_data.get("model", "qwen3:30b")
            db_project.current_phase = project_data.get("current_phase", "content_analysis")
            db_project.status = project_data.get("status", "in_progress")
            db_project.num_problems = project_data.get("num_problems", 10)
            db_project.validation_iterations = project_data.get("validation_iterations", 3)
            db_project.project_data = project_data.get("project_data", {})
            db_project.problems = project_data.get("problems", [])
            db_project.validation_results = project_data.get("validation_results", [])
            db_project.final_review = project_data.get("final_review", {})
            db_project.output_files = project_data.get("output_files", {})
            db_project.last_activity_at = datetime.utcnow()
            db_project.updated_at = datetime.utcnow()
        else:
            # Create new project
            db_project = EGProject(
                id=project_id,
                input_file_path=project_data.get("input_file_path", ""),
                input_content=project_data.get("input_content", ""),
                output_directory=project_data.get("output_directory", "exam_outputs"),
                model=project_data.get("model", "qwen3:30b"),
                current_phase=project_data.get("current_phase", "content_analysis"),
                status=project_data.get("status", "in_progress"),
                num_problems=project_data.get("num_problems", 10),
                validation_iterations=project_data.get("validation_iterations", 3),
                project_data=project_data.get("project_data", {}),
                problems=project_data.get("problems", []),
                validation_results=project_data.get("validation_results", []),
                final_review=project_data.get("final_review", {}),
                output_files=project_data.get("output_files", {})
            )
            db.add(db_project)
        
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save project {project_id} to database", error=str(e), exc_info=True)
        raise


class ExamGeneratorProjectCreate(BaseModel):
    """Create Exam Generator project request."""
    input_content: str
    output_directory: str = "exam_outputs"
    num_problems: int = 10
    validation_iterations: int = 3
    model: Optional[str] = "qwen3:30b"


class ExamGeneratorProjectResponse(BaseModel):
    """Exam Generator project response."""
    project_id: str
    input_file_path: str
    output_directory: str
    current_phase: str
    status: str
    num_problems: int
    validation_iterations: int
    model: Optional[str] = "qwen3:30b"
    problems: List[Dict[str, Any]] = []
    validation_results: List[Dict[str, Any]] = []
    final_review: Optional[Dict[str, Any]] = None
    output_files: Dict[str, str] = {}


@router.post("/api/exam-generator/projects", response_model=ExamGeneratorProjectResponse)
async def create_exam_generator_project(
    project: ExamGeneratorProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new Exam Generator project."""
    try:
        # Validate input
        if not project.input_content or not project.input_content.strip():
            raise HTTPException(status_code=400, detail="Input content is required")
        
        if project.num_problems < 1 or project.num_problems > 100:
            raise HTTPException(status_code=400, detail="Number of problems must be between 1 and 100")
        
        project_id = str(uuid.uuid4())
        
        # Create company instance
        try:
            model = project.model or "qwen3:30b"
            if model not in ["llama3:latest", "qwen3:30b"]:
                model = "qwen3:30b"
            
            company = ExamGeneratorCompany(model=model)
        except Exception as e:
            logger.error("Failed to initialize ExamGeneratorCompany", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to initialize exam generator: {str(e)}")
        
        # Initialize project
        exam_project = ExamProject(
            project_id=project_id,
            input_file_path="",  # Will be set if file uploaded
            input_content=project.input_content,
            output_directory=project.output_directory,
            num_problems=project.num_problems,
            validation_iterations=project.validation_iterations
        )
        
        # Store project in memory
        active_projects[project_id] = {
            "company": company,
            "project": exam_project,
            "model": model,
            "input_content": project.input_content,
            "output_directory": project.output_directory,
            "num_problems": project.num_problems,
            "validation_iterations": project.validation_iterations,
            "current_phase": "content_analysis",
            "status": "in_progress"
        }
        
        # Save to database
        project_data = {
            "input_file_path": "",
            "input_content": project.input_content,
            "output_directory": project.output_directory,
            "model": model,
            "current_phase": "content_analysis",
            "status": "in_progress",
            "num_problems": project.num_problems,
            "validation_iterations": project.validation_iterations,
            "project_data": {},
            "problems": [],
            "validation_results": [],
            "final_review": None,
            "output_files": {}
        }
        
        await save_project_to_db(project_id, project_data, db)
        
        return ExamGeneratorProjectResponse(
            project_id=project_id,
            input_file_path="",
            output_directory=project.output_directory,
            current_phase="content_analysis",
            status="in_progress",
            num_problems=project.num_problems,
            validation_iterations=project.validation_iterations,
            model=model
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create exam generator project", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.post("/api/exam-generator/projects/upload")
async def upload_input_file(
    file: UploadFile = File(...),
    output_directory: str = "exam_outputs",
    num_problems: int = 10,
    validation_iterations: int = 3,
    model: Optional[str] = "qwen3:30b",
    db: AsyncSession = Depends(get_db)
):
    """Upload a text file and create an exam generator project."""
    try:
        # Validate file type
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="Only .txt files are supported")
        
        # Read file content
        content = await file.read()
        input_content = content.decode('utf-8')
        
        if not input_content.strip():
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Create project
        project_create = ExamGeneratorProjectCreate(
            input_content=input_content,
            output_directory=output_directory,
            num_problems=num_problems,
            validation_iterations=validation_iterations,
            model=model
        )
        
        response = await create_exam_generator_project(project_create, db)
        
        # Update with file path
        project_id = response.project_id
        if project_id in active_projects:
            active_projects[project_id]["input_file_path"] = file.filename
        
        # Update database
        project_data = {
            "input_file_path": file.filename,
            "input_content": input_content,
            "output_directory": output_directory,
            "model": model or "qwen3:30b",
            "current_phase": "content_analysis",
            "status": "in_progress",
            "num_problems": num_problems,
            "validation_iterations": validation_iterations,
            "project_data": {},
            "problems": [],
            "validation_results": [],
            "final_review": None,
            "output_files": {}
        }
        await save_project_to_db(project_id, project_data, db)
        
        response.input_file_path = file.filename
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload file", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


async def generate_exam_background(project_id: str, db: AsyncSession):
    """Background task to generate exam."""
    try:
        if project_id not in active_projects:
            logger.error(f"Project {project_id} not found in active projects")
            return
        
        project_data = active_projects[project_id]
        company = project_data["company"]
        project = project_data["project"]
        
        # Initialize phase logs
        if project_id not in phase_logs:
            phase_logs[project_id] = []
        
        # Progress callback function
        def update_progress(phase: str, progress: int, message: str = ""):
            """Update generation status with progress."""
            generation_status[project_id] = {
                "status": "generating",
                "phase": phase,
                "progress": progress,
                "message": message
            }
            
            # Log phase activity
            phase_logs[project_id].append({
                "phase": phase,
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Progress update for {project_id}", phase=phase, progress=progress, message=message)
        
        # Update initial status
        update_progress("content_analysis", 0, "Starting exam generation...")
        
        # Generate exam with progress callback
        problems, review = await company.generate_exam(
            project,
            max_iterations=project_data["validation_iterations"],
            progress_callback=update_progress
        )
        
        # Final progress update
        update_progress("complete", 100, f"Generated {len(problems)} problems successfully")
        
        # Validate problems were generated
        if not problems:
            error_msg = "No problems were generated. Please check the input content and try again."
            logger.error(error_msg)
            generation_status[project_id] = {
                "status": "error",
                "phase": "error",
                "progress": 0,
                "error": error_msg
            }
            if project_id in active_projects:
                active_projects[project_id]["status"] = "error"
            return
        
        # Save exam files
        logger.info(f"Saving {len(problems)} problems to files")
        output_files = await company.save_exam_files(project, problems)
        
        # Update project data
        project_data["problems"] = [p.to_dict() for p in problems]
        project_data["final_review"] = review
        project_data["output_files"] = output_files
        project_data["status"] = "complete"
        project_data["current_phase"] = "complete"
        
        logger.info(f"Exam generation complete", 
                   problems_count=len(problems),
                   review_status=review.get("approval_status"))
        
        # Save to database
        db_project_data = {
            "input_file_path": project_data.get("input_file_path", ""),
            "input_content": project_data.get("input_content", ""),
            "output_directory": project_data.get("output_directory", "exam_outputs"),
            "model": project_data.get("model", "qwen3:30b"),
            "current_phase": "complete",
            "status": "complete",
            "num_problems": project_data.get("num_problems", 10),
            "validation_iterations": project_data.get("validation_iterations", 3),
            "project_data": {},
            "problems": [p.to_dict() for p in problems],
            "validation_results": project.validation_results,
            "final_review": review,
            "output_files": output_files
        }
        await save_project_to_db(project_id, db_project_data, db)
        
        generation_status[project_id] = {
            "status": "complete",
            "phase": "complete",
            "progress": 100,
            "message": f"Successfully generated {len(problems)} problems"
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating exam for project {project_id}", error=error_msg, exc_info=True)
        
        # Check if it's a connection error
        if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "failed" in error_msg.lower():
            error_msg = f"Connection error: Could not connect to LLM service. Please ensure Ollama is running at http://localhost:11434"
        
        generation_status[project_id] = {
            "status": "error",
            "phase": "error",
            "progress": 0,
            "error": error_msg,
            "message": f"Error: {error_msg}"
        }
        if project_id in active_projects:
            active_projects[project_id]["status"] = "error"
        
        # Also save error to database
        try:
            db_project_data = {
                "input_file_path": project_data.get("input_file_path", ""),
                "input_content": project_data.get("input_content", ""),
                "output_directory": project_data.get("output_directory", "exam_outputs"),
                "model": project_data.get("model", "qwen3:30b"),
                "current_phase": "error",
                "status": "error",
                "num_problems": project_data.get("num_problems", 10),
                "validation_iterations": project_data.get("validation_iterations", 3),
                "project_data": {"error": error_msg},
                "problems": [],
                "validation_results": [],
                "final_review": None,
                "output_files": {}
            }
            await save_project_to_db(project_id, db_project_data, db)
        except Exception as db_error:
            logger.error(f"Failed to save error to database: {db_error}")


@router.get("/api/exam-generator/health")
async def check_llm_health():
    """Check if LLM service is available."""
    try:
        from app.llm.client import LLMClient
        from app.book_writer.config import get_config
        
        agent_config = get_config()
        test_client = LLMClient(
            api_key=None,
            base_url=agent_config.get("base_url", "http://localhost:11434/v1"),
            model=agent_config.get("model", "qwen3:30b"),
            provider=agent_config.get("provider", "local")
        )
        
        # Try a simple test call
        await test_client.complete(
            system="You are a test assistant.",
            user="Say 'OK' if you can hear me."
        )
        
        return {"status": "ok", "message": "LLM service is available"}
    except Exception as e:
        error_msg = str(e)
        if "connection" in error_msg.lower() or "refused" in error_msg.lower():
            return {
                "status": "error",
                "message": "Cannot connect to LLM service. Please ensure Ollama is running at http://localhost:11434",
                "error": error_msg
            }
        return {"status": "error", "message": f"LLM service error: {error_msg}", "error": error_msg}


@router.post("/api/exam-generator/projects/{project_id}/generate")
async def generate_exam(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start exam generation for a project."""
    try:
        if project_id not in active_projects:
            # Try to load from database
            result = await db.execute(
                select(EGProject).where(EGProject.id == project_id)
            )
            db_project = result.scalar_one_or_none()
            
            if not db_project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Reconstruct project
            model = db_project.model or "qwen3:30b"
            company = ExamGeneratorCompany(model=model)
            
            exam_project = ExamProject(
                project_id=project_id,
                input_file_path=db_project.input_file_path or "",
                input_content=db_project.input_content or "",
                output_directory=db_project.output_directory or "exam_outputs",
                num_problems=db_project.num_problems or 10,
                validation_iterations=db_project.validation_iterations or 3
            )
            
            active_projects[project_id] = {
                "company": company,
                "project": exam_project,
                "model": model,
                "input_content": db_project.input_content or "",
                "output_directory": db_project.output_directory or "exam_outputs",
                "num_problems": db_project.num_problems or 10,
                "validation_iterations": db_project.validation_iterations or 3,
                "current_phase": db_project.current_phase or "content_analysis",
                "status": db_project.status or "in_progress",
                "input_file_path": db_project.input_file_path or ""
            }
        
        project_data = active_projects[project_id]
        
        if project_data["status"] == "generating":
            raise HTTPException(status_code=400, detail="Generation already in progress")
        
        if project_data["status"] == "complete":
            raise HTTPException(status_code=400, detail="Exam already generated")
        
        # Start background generation
        background_tasks.add_task(generate_exam_background, project_id, db)
        
        project_data["status"] = "generating"
        
        return {"status": "started", "project_id": project_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start exam generation", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")


@router.get("/api/exam-generator/projects/{project_id}", response_model=ExamGeneratorProjectResponse)
async def get_exam_generator_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get exam generator project by ID."""
    try:
        # Check active projects first
        if project_id in active_projects:
            project_data = active_projects[project_id]
            project = project_data["project"]
            
            return ExamGeneratorProjectResponse(
                project_id=project_id,
                input_file_path=project_data.get("input_file_path", ""),
                output_directory=project.output_directory,
                current_phase=project_data.get("current_phase", project.current_phase.value),
                status=project_data.get("status", project.status),
                num_problems=project.num_problems,
                validation_iterations=project.validation_iterations,
                model=project_data.get("model", "qwen3:30b"),
                problems=project_data.get("problems", [p.to_dict() for p in project.problems]),
                validation_results=project.validation_results,
                final_review=project.final_review,
                output_files=project_data.get("output_files", {})
            )
        
        # Load from database
        result = await db.execute(
            select(EGProject).where(EGProject.id == project_id)
        )
        db_project = result.scalar_one_or_none()
        
        if not db_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ExamGeneratorProjectResponse(
            project_id=db_project.id,
            input_file_path=db_project.input_file_path or "",
            output_directory=db_project.output_directory or "exam_outputs",
            current_phase=db_project.current_phase or "content_analysis",
            status=db_project.status or "in_progress",
            num_problems=db_project.num_problems or 10,
            validation_iterations=db_project.validation_iterations or 3,
            model=db_project.model or "qwen3:30b",
            problems=db_project.problems or [],
            validation_results=db_project.validation_results or [],
            final_review=db_project.final_review,
            output_files=db_project.output_files or {}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project {project_id}", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")


@router.get("/api/exam-generator/projects/{project_id}/status")
async def get_generation_status(project_id: str):
    """Get current generation status."""
    status = generation_status.get(project_id, {
        "status": "unknown",
        "phase": "unknown",
        "progress": 0,
        "message": ""
    })
    
    if project_id in active_projects:
        project_data = active_projects[project_id]
        status["current_phase"] = project_data.get("current_phase", status.get("phase", "unknown"))
        status["status"] = project_data.get("status", status.get("status", "unknown"))
    
    # Ensure all fields are present
    if "message" not in status:
        status["message"] = ""
    if "progress" not in status:
        status["progress"] = 0
    if "phase" not in status:
        status["phase"] = status.get("current_phase", "unknown")
    
    return status


@router.get("/api/exam-generator/projects/{project_id}/download/{file_type}")
async def download_exam_file(
    project_id: str,
    file_type: str,
    db: AsyncSession = Depends(get_db)
):
    """Download generated exam file."""
    try:
        # Validate file type
        if file_type not in ["problems", "solutions", "combined"]:
            raise HTTPException(status_code=400, detail="Invalid file type. Must be 'problems', 'solutions', or 'combined'")
        
        # Get project
        if project_id in active_projects:
            output_files = active_projects[project_id].get("output_files", {})
        else:
            result = await db.execute(
                select(EGProject).where(EGProject.id == project_id)
            )
            db_project = result.scalar_one_or_none()
            if not db_project:
                raise HTTPException(status_code=404, detail="Project not found")
            output_files = db_project.output_files or {}
        
        # Map file type to key
        file_key_map = {
            "problems": "problems",
            "solutions": "solutions",
            "combined": "combined"
        }
        
        file_path = output_files.get(file_key_map[file_type])
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            file_path,
            media_type="text/plain",
            filename=Path(file_path).name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@router.get("/api/exam-generator/projects")
async def list_exam_generator_projects(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """List all exam generator projects."""
    try:
        result = await db.execute(
            select(EGProject)
            .order_by(EGProject.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        projects = result.scalars().all()
        
        return [
            {
                "project_id": p.id,
                "input_file_path": p.input_file_path or "",
                "output_directory": p.output_directory or "exam_outputs",
                "current_phase": p.current_phase or "content_analysis",
                "status": p.status or "in_progress",
                "num_problems": p.num_problems or 10,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in projects
        ]
    
    except Exception as e:
        logger.error("Failed to list projects", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")
