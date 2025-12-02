"""Ferrari Company API routes for web UI."""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
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
        project_id = str(uuid.uuid4())
        
        # Create company instance
        company = FerrariBookCompany()
        
        # Initialize project
        company.project = BookProject(
            title=project.title,
            premise=project.premise,
            target_word_count=project.target_word_count,
            audience=project.audience
        )
        
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
            "chat_log": []
        }
        
        return FerrariProjectResponse(
            project_id=project_id,
            title=project.title,
            premise=project.premise,
            current_phase=Phase.STRATEGY_CONCEPT.value,
            status="in_progress",
            output_directory=project.output_directory
        )
    except Exception as e:
        logger.error("Failed to create Ferrari project", error=str(e))
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


@router.post("/api/ferrari-company/projects/{project_id}/execute-phase")
async def execute_phase(project_id: str):
    """Execute the current phase."""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = active_projects[project_id]
    company = project_data["company"]
    
    try:
        # Get current phase
        current_phase = Phase(project_data["current_phase"])
        
        logger.info(f"Executing phase {current_phase.value} for project {project_id}")
        
        # Execute phase (same as CLI)
        try:
            await company._execute_phase(current_phase)
        except Exception as phase_error:
            logger.error(f"Phase execution error: {str(phase_error)}", error=str(phase_error), exc_info=True)
            # Provide more detailed error message
            error_msg = str(phase_error)
            if "timeout" in error_msg.lower():
                error_msg = "Phase execution timed out. The LLM may be slow or unavailable. Please try again."
            elif "connection" in error_msg.lower():
                error_msg = "Cannot connect to LLM service. Make sure Ollama is running."
            raise HTTPException(status_code=500, detail=f"Phase execution failed: {error_msg}")
        
        # Update project state
        project_data["company"] = company
        project_data["current_phase"] = current_phase.value
        
        # Get artifacts for presentation (same format as CLI)
        artifacts = {}
        summary_parts = []
        
        try:
            if current_phase == Phase.STRATEGY_CONCEPT:
                artifacts = {"book_brief": company.project.book_brief or {}}
                summary_parts.append("CPSO has created the initial book brief.")
            elif current_phase == Phase.EARLY_DESIGN:
                artifacts = {
                    "world_dossier": company.project.world_dossier or {},
                    "character_bible": company.project.character_bible or {},
                    "plot_arc": company.project.plot_arc or {}
                }
                summary_parts.append("Story Design Director has completed world and character design.")
            elif current_phase == Phase.DETAILED_ENGINEERING:
                artifacts = {"outline": company.project.outline or []}
                summary_parts.append("Narrative Engineering Director has created the full hierarchical outline.")
            elif current_phase == Phase.PROTOTYPES_TESTING:
                artifacts = {
                    "draft_chapters": company.project.draft_chapters,
                    "revision_report": company.project.revision_report or {}
                }
                summary_parts.append("Production and QA teams have completed draft and testing.")
            elif current_phase == Phase.INDUSTRIALIZATION_PACKAGING:
                artifacts = {"formatted_manuscript": company.project.formatted_manuscript or ""}
                summary_parts.append("Formatting and export agents have prepared the production-ready manuscript.")
            elif current_phase == Phase.MARKETING_LAUNCH:
                artifacts = {"launch_package": company.project.launch_package or {}}
                summary_parts.append("Launch Director has created the complete launch package.")
        except Exception as artifact_error:
            logger.warning(f"Error getting artifacts: {str(artifact_error)}")
            # Continue with empty artifacts rather than failing
        
        summary = " ".join(summary_parts) if summary_parts else f"Phase {current_phase.value.replace('_', ' ').title()} completed."
        
        # Get chat log for this phase
        try:
            phase_chat_log = company.message_bus.get_chat_log(current_phase)
        except Exception as log_error:
            logger.warning(f"Error getting chat log: {str(log_error)}")
            phase_chat_log = []
        
        return {
            "success": True,
            "phase": current_phase.value,
            "summary": summary,
            "artifacts": artifacts,
            "chat_log": phase_chat_log,
            "ready_for_decision": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute phase", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to execute phase: {str(e)}")


@router.post("/api/ferrari-company/projects/{project_id}/decide")
async def make_decision(project_id: str, decision: PhaseDecision):
    """Make owner decision on current phase."""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = active_projects[project_id]
    company = project_data["company"]
    
    try:
        current_phase = Phase(project_data["current_phase"])
        owner_decision = OwnerDecision(decision.decision)
        
        # Store decision
        project_data["owner_decisions"][current_phase.value] = decision.decision
        
        if owner_decision == OwnerDecision.STOP:
            project_data["status"] = "stopped"
            return {
                "success": True,
                "decision": decision.decision,
                "status": "stopped",
                "message": "Project stopped by owner"
            }
        elif owner_decision == OwnerDecision.REQUEST_CHANGES:
            # Re-run phase
            await company._execute_phase(current_phase)
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
            
            current_index = phases.index(current_phase)
            if current_index < len(phases) - 1:
                next_phase = phases[current_index + 1]
                project_data["current_phase"] = next_phase.value
            else:
                # All phases complete
                project_data["status"] = "complete"
                project_data["current_phase"] = Phase.COMPLETE.value
                
                # Save final files
                await save_final_files(project_id, company, project_data)
            
            return {
                "success": True,
                "decision": decision.decision,
                "next_phase": project_data["current_phase"],
                "status": project_data["status"],
                "message": f"Phase approved. Moving to {project_data['current_phase']}"
            }
    except Exception as e:
        logger.error("Failed to process decision", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process decision: {str(e)}")


async def save_final_files(project_id: str, company: FerrariBookCompany, project_data: Dict[str, Any]):
    """Save final files after completion."""
    try:
        from pathlib import Path
        import shutil
        
        output_dir = Path(project_data["output_directory"])
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Generate safe filename
        title = project_data["title"] or "Untitled"
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50] if safe_title else "Untitled"
        
        # Assemble final package
        final_package = company._assemble_final_package()
        chat_log = company.message_bus.get_chat_log()
        
        # Save JSON package
        json_filename = output_dir / f"{safe_title}_package.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(final_package, f, indent=2, ensure_ascii=False)
        
        # Save chat log
        chat_log_filename = output_dir / f"{safe_title}_chat_log.json"
        with open(chat_log_filename, "w", encoding="utf-8") as f:
            json.dump(chat_log, f, indent=2, ensure_ascii=False)
        
        # Copy PDF if exists
        pdf_dest_path = None
        if 'pdf_path' in final_package and final_package['pdf_path']:
            pdf_source_path = Path(final_package['pdf_path'])
            if pdf_source_path.exists():
                pdf_dest_path = output_dir / f"{safe_title}_book.pdf"
                shutil.copy2(pdf_source_path, pdf_dest_path)
        elif 'exports' in final_package and 'pdf_path' in final_package.get('exports', {}):
            pdf_source_path = Path(final_package['exports']['pdf_path'])
            if pdf_source_path.exists():
                pdf_dest_path = output_dir / f"{safe_title}_book.pdf"
                shutil.copy2(pdf_source_path, pdf_dest_path)
        
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
            logger.warning("Could not create zip archive", error=str(e))
        
        # Store file paths in project data
        project_data["files"] = {
            "json": str(json_filename.absolute()),
            "chat_log": str(chat_log_filename.absolute()),
            "pdf": str(pdf_dest_path.absolute()) if pdf_dest_path and pdf_dest_path.exists() else None,
            "zip": str(zip_filename.absolute()) if zip_filename else None
        }
        
        project_data["final_package"] = final_package
        project_data["chat_log"] = chat_log
        
    except Exception as e:
        logger.error("Failed to save final files", error=str(e))


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

