"""Book Publishing House API routes for web UI."""
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


class BookPublishingHouseProjectCreate(BaseModel):
    """Create Book Publishing House project request."""
    title: Optional[str] = None
    premise: str
    target_word_count: Optional[int] = None
    audience: Optional[str] = None
    output_directory: str = "book_outputs"
    reference_documents: Optional[List[str]] = None  # List of document IDs
    model: Optional[str] = "qwen3:30b"  # Model to use: llama3:latest or qwen3:30b


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
    model: Optional[str] = "qwen3:30b"  # Model being used


@router.post("/api/ferrari-company/projects", response_model=BookPublishingHouseProjectResponse)
async def create_book_publishing_house_project(project: BookPublishingHouseProjectCreate):
    """Create a new Book Publishing House project."""
    try:
        # Validate input
        if not project.premise or not project.premise.strip():
            raise HTTPException(status_code=400, detail="Premise is required")
        
        project_id = str(uuid.uuid4())
        
        # Create company instance with selected model
        try:
            model = project.model or "qwen3:30b"
            # Validate model
            if model not in ["llama3:latest", "qwen3:30b"]:
                model = "qwen3:30b"  # Fall back to default
            company = FerrariBookCompany(model=model)
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
        
        active_projects[project_id] = {
            "company": company,
            "title": project.title,
            "premise": project.premise,
            "target_word_count": project.target_word_count,
            "audience": project.audience,
            "output_directory": project.output_directory,
            "reference_documents": project.reference_documents or [],
            "model": model,
            "current_phase": Phase.STRATEGY_CONCEPT.value,
            "status": "in_progress",
            "owner_decisions": {},
            "artifacts": {},
            "chat_log": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created Book Publishing House project {project_id}")
        
        return BookPublishingHouseProjectResponse(
            project_id=project_id,
            title=project.title,
            premise=project.premise,
            current_phase=Phase.STRATEGY_CONCEPT.value,
            status="in_progress",
            output_directory=project.output_directory,
            reference_documents=project.reference_documents,
            model=model
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create Book Publishing House project", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/api/ferrari-company/projects/{project_id}", response_model=BookPublishingHouseProjectResponse)
async def get_book_publishing_house_project(project_id: str):
    """Get Book Publishing House project status."""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = active_projects[project_id]
    
    return BookPublishingHouseProjectResponse(
        project_id=project_id,
        title=project_data["title"],
        premise=project_data["premise"],
        current_phase=project_data["current_phase"],
        status=project_data["status"],
        output_directory=project_data["output_directory"],
        reference_documents=project_data.get("reference_documents", []),
        model=project_data.get("model", "qwen3:30b")
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
async def list_book_publishing_house_projects():
    """List all Book Publishing House projects with their PDF files."""
    try:
        projects = []
        for project_id, project_data in active_projects.items():
            files = project_data.get("files", {})
            pdf_path = files.get("pdf")
            
            projects.append({
                "project_id": project_id,
                "title": project_data.get("title", "Untitled"),
                "status": project_data.get("status", "unknown"),
                "has_pdf": pdf_path is not None and os.path.exists(pdf_path) if pdf_path else False,
                "pdf_path": pdf_path,
                "pdf_filename": Path(pdf_path).name if pdf_path and os.path.exists(pdf_path) else None,
                "created_at": project_data.get("created_at", "")
            })
        
        return {"success": True, "projects": projects}
    except Exception as e:
        logger.error("Failed to list Book Publishing House projects", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


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

