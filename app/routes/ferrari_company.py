"""Ferrari Company API routes for web UI."""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import structlog
import asyncio
import uuid

from app.book_writer.ferrari_company import (
    FerrariBookCompany, OwnerDecision, Phase, BookProject
)

logger = structlog.get_logger(__name__)

router = APIRouter()

# Store active projects in memory (in production, use Redis or database)
active_projects: Dict[str, Dict[str, Any]] = {}

# Store phase execution status for background tasks
phase_execution_status: Dict[str, Dict[str, Any]] = {}


class FerrariProjectCreate(BaseModel):
    """Create Ferrari project request."""
    title: Optional[str] = None
    premise: str
    target_word_count: Optional[int] = None
    audience: Optional[str] = None
    output_directory: str = "book_outputs"


class PhaseDecision(BaseModel):
    """Owner decision for a phase."""
    decision: str  # "approve", "request_changes", "stop"


class FerrariProjectResponse(BaseModel):
    """Ferrari project response."""
    project_id: str
    title: Optional[str]
    premise: str
    current_phase: str
    status: str
    output_directory: str


@router.post("/api/ferrari-company/projects", response_model=FerrariProjectResponse)
async def create_ferrari_project(project: FerrariProjectCreate):
    """Create a new Ferrari company project."""
    try:
        # Validate input
        if not project.premise or not project.premise.strip():
            raise HTTPException(status_code=400, detail="Premise is required")
        
        project_id = str(uuid.uuid4())
        
        # Create company instance
        try:
            company = FerrariBookCompany()
        except Exception as e:
            logger.error("Failed to initialize FerrariBookCompany", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to initialize book company: {str(e)}")
        
        # Initialize project
        try:
            company.project = BookProject(
                title=project.title,
                premise=project.premise,
                target_word_count=project.target_word_count,
                audience=project.audience
            )
        except Exception as e:
            logger.error("Failed to create BookProject", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")
        
        # Store project
        active_projects[project_id] = {
            "company": company,
            "title": project.title,
            "premise": project.premise,
            "target_word_count": project.target_word_count,
            "audience": project.audience,
            "output_directory": project.output_directory,
            "current_phase": Phase.STRATEGY_CONCEPT.value,
            "status": "in_progress",
            "owner_decisions": {},
            "artifacts": {},
            "chat_log": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created Ferrari project {project_id}")
        
        return FerrariProjectResponse(
            project_id=project_id,
            title=project.title,
            premise=project.premise,
            current_phase=Phase.STRATEGY_CONCEPT.value,
            status="in_progress",
            output_directory=project.output_directory
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create Ferrari project", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/api/ferrari-company/projects/{project_id}", response_model=FerrariProjectResponse)
async def get_ferrari_project(project_id: str):
    """Get Ferrari project status."""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = active_projects[project_id]
    
    return FerrariProjectResponse(
        project_id=project_id,
        title=project_data["title"],
        premise=project_data["premise"],
        current_phase=project_data["current_phase"],
        status=project_data["status"],
        output_directory=project_data["output_directory"]
    )


async def _execute_phase_background(project_id: str, current_phase: Phase):
    """Background task to execute phase without blocking HTTP request."""
    project_data = active_projects.get(project_id)
    if not project_data:
        logger.error(f"Project {project_id} not found in background task")
        return
    
    company = project_data["company"]
    status_key = f"{project_id}_{current_phase.value}"
    
    try:
        # Mark as running
        phase_execution_status[status_key] = {
            "status": "running",
            "phase": current_phase.value,
            "started_at": datetime.utcnow().isoformat(),
            "error": None
        }
        
        logger.info(f"Background: Executing phase {current_phase.value} for project {project_id}")
        
        # Execute phase (same as CLI) - no timeout in background
        await company._execute_phase(current_phase)
        
        # Update project state
        project_data["company"] = company
        project_data["current_phase"] = current_phase.value
        
        # Mark as completed
        phase_execution_status[status_key] = {
            "status": "completed",
            "phase": current_phase.value,
            "started_at": phase_execution_status[status_key]["started_at"],
            "completed_at": datetime.utcnow().isoformat(),
            "error": None
        }
        
        logger.info(f"Background: Phase {current_phase.value} completed for project {project_id}")
        
    except Exception as phase_error:
        logger.error(f"Background phase execution error: {str(phase_error)}", error=str(phase_error), exc_info=True)
        # Mark as failed
        phase_execution_status[status_key] = {
            "status": "failed",
            "phase": current_phase.value,
            "started_at": phase_execution_status.get(status_key, {}).get("started_at", datetime.utcnow().isoformat()),
            "error": str(phase_error)
        }


@router.post("/api/ferrari-company/projects/{project_id}/execute-phase")
async def execute_phase(project_id: str, background_tasks: BackgroundTasks):
    """Start phase execution in background and return immediately."""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
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
        background_tasks.add_task(_execute_phase_background, project_id, current_phase)
        
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
async def get_phase_status(project_id: str):
    """Get status of phase execution."""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
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
async def make_decision(project_id: str, decision: PhaseDecision):
    """Make owner decision on current phase."""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
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
            logger.info(f"Project {project_id} stopped by owner")
            return {
                "success": True,
                "decision": decision.decision,
                "status": "stopped",
                "message": "Project stopped by owner"
            }
        elif owner_decision == OwnerDecision.REQUEST_CHANGES:
            # Re-run phase
            try:
                await asyncio.wait_for(
                    company._execute_phase(current_phase),
                    timeout=1800.0  # 30 minutes
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=504,
                    detail="Phase re-execution timed out. Please try again."
                )
            except Exception as e:
                logger.error(f"Error re-executing phase: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to re-execute phase: {str(e)}"
                )
            
            project_data["company"] = company
            return {
                "success": True,
                "decision": decision.decision,
                "message": "Phase re-executed with changes",
                "ready_for_decision": True
            }
        else:  # APPROVE
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
                logger.info(f"Project {project_id} approved phase {current_phase.value}, moving to {next_phase.value}")
            else:
                # All phases complete
                project_data["status"] = "complete"
                project_data["current_phase"] = Phase.COMPLETE.value
                
                # Save final files
                try:
                    await save_final_files(project_id, company, project_data)
                except Exception as save_error:
                    logger.error(f"Error saving final files: {str(save_error)}", exc_info=True)
                    # Don't fail the request, but log the error
                    # Files can be regenerated if needed
            
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
                if pdf_dest_path and pdf_dest_path.exists():
                    zipf.write(pdf_dest_path, pdf_dest_path.name)
        except Exception as e:
            logger.warning(f"Could not create zip archive: {str(e)}", exc_info=True)
            # Continue without ZIP
        
        # Store file paths in project data
        project_data["files"] = {
            "json": str(json_filename.absolute()),
            "chat_log": str(chat_log_filename.absolute()),
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
async def get_chat_log(project_id: str, phase: Optional[str] = None):
    """Get chat log for project."""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = active_projects[project_id]
    company = project_data["company"]
    
    if phase:
        phase_enum = Phase(phase)
        chat_log = company.message_bus.get_chat_log(phase_enum)
    else:
        chat_log = company.message_bus.get_chat_log()
    
    return {"chat_log": chat_log}


@router.get("/api/ferrari-company/projects/{project_id}/download/{file_type}")
async def download_file(project_id: str, file_type: str):
    """Download generated files."""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
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


@router.get("/api/ferrari-company/projects/{project_id}/files")
async def get_file_info(project_id: str):
    """Get information about generated files."""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
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

