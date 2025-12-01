"""Book writer API routes."""
import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.database import get_db
from app.models import BookProject, BookOutline, BookChapter
from app.book_writer.agents import BookAgents
from app.book_writer.outline_generator import OutlineGenerator
from app.book_writer.book_generator import BookGenerator
from app.book_writer.config import get_config

logger = structlog.get_logger(__name__)

router = APIRouter()


class BookProjectCreate(BaseModel):
    """Create book project request."""
    title: str
    initial_prompt: str
    num_chapters: int = 25


class BookProjectResponse(BaseModel):
    """Book project response."""
    id: str
    title: str
    initial_prompt: Optional[str]
    num_chapters: int
    status: str
    created_at: str
    updated_at: str


class ChapterOutline(BaseModel):
    """Chapter outline model."""
    chapter_number: int
    title: str
    prompt: str
    sections: Optional[List[Dict[str, Any]]] = []


class BookOutlineResponse(BaseModel):
    """Book outline response."""
    id: str
    project_id: str
    outline_data: List[ChapterOutline]
    created_at: str
    updated_at: str


class BookChapterResponse(BaseModel):
    """Book chapter response."""
    id: str
    project_id: str
    chapter_number: int
    title: str
    content: Optional[str]
    prompt: Optional[str]
    status: str
    word_count: int
    created_at: str
    updated_at: str


@router.post("/api/book-writer/projects", response_model=BookProjectResponse)
async def create_project(project: BookProjectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new book project."""
    try:
        db_project = BookProject(
            title=project.title,
            initial_prompt=project.initial_prompt,
            num_chapters=project.num_chapters,
            status="draft"
        )
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        
        return BookProjectResponse(
            id=db_project.id,
            title=db_project.title,
            initial_prompt=db_project.initial_prompt,
            num_chapters=db_project.num_chapters,
            status=db_project.status,
            created_at=db_project.created_at.isoformat(),
            updated_at=db_project.updated_at.isoformat()
        )
    except Exception as e:
        logger.error("Failed to create project", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/api/book-writer/projects", response_model=List[BookProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all book projects."""
    try:
        result = await db.execute(select(BookProject).order_by(BookProject.updated_at.desc()))
        projects = result.scalars().all()
        
        return [
            BookProjectResponse(
                id=p.id,
                title=p.title,
                initial_prompt=p.initial_prompt,
                num_chapters=p.num_chapters,
                status=p.status,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat()
            )
            for p in projects
        ]
    except Exception as e:
        logger.error("Failed to list projects", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")


@router.get("/api/book-writer/projects/{project_id}", response_model=BookProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get a book project."""
    try:
        result = await db.execute(select(BookProject).where(BookProject.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return BookProjectResponse(
            id=project.id,
            title=project.title,
            initial_prompt=project.initial_prompt,
            num_chapters=project.num_chapters,
            status=project.status,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get project", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")


@router.post("/api/book-writer/projects/{project_id}/generate-outline", response_model=BookOutlineResponse)
async def generate_outline(project_id: str, db: AsyncSession = Depends(get_db)):
    """Generate outline for a book project."""
    try:
        # Get project
        result = await db.execute(select(BookProject).where(BookProject.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.initial_prompt:
            raise HTTPException(status_code=400, detail="Project missing initial prompt")
        
        # Update status
        project.status = "outline_generating"
        await db.commit()
        
        try:
            # Generate outline
            agent_config = get_config()
            agents = BookAgents(agent_config)
            outline_gen = OutlineGenerator(agents, agent_config)
            
            outline = await outline_gen.generate_outline(project.initial_prompt, project.num_chapters)
            
            # Ensure all chapters have sections - add defaults if missing
            for ch in outline:
                if not ch.get("sections") or len(ch.get("sections", [])) == 0:
                    logger.warning(f"Chapter {ch['chapter_number']} missing sections, adding defaults")
                    ch["sections"] = [
                        {
                            "title": f"Section {j+1}",
                            "subsections": [
                                {
                                    "title": f"Subsection {j+1}.{k+1}",
                                    "main_points": [
                                        {"text": f"Main point for paragraph {m+1}"} for m in range(3)
                                    ]
                                } for k in range(2)
                            ]
                        } for j in range(3)
                    ]
                    # Update prompt to include sections
                    if "- Sections:" not in ch.get("prompt", ""):
                        sections_text = "\n".join([
                            f"  Section {j+1}: {sec['title']}" + 
                            "\n    " + "\n    ".join([
                                f"- Subsection {j+1}.{k+1}: {sub['title']}\n      Main Points:\n        " +
                                "\n        ".join([f"* {mp.get('text', mp) if isinstance(mp, dict) else mp}" for mp in sub['main_points']])
                                for k, sub in enumerate(sec['subsections'])
                            ])
                            for j, sec in enumerate(ch["sections"])
                        ])
                        ch["prompt"] = ch.get("prompt", "") + f"\n- Sections:\n{sections_text}"
            
            # Save outline
            outline_data = [
                {
                    "chapter_number": ch["chapter_number"],
                    "title": ch["title"],
                    "prompt": ch["prompt"],
                    "sections": ch.get("sections", [])
                }
                for ch in outline
            ]
            
            # Check if outline already exists
            result = await db.execute(select(BookOutline).where(BookOutline.project_id == project_id))
            existing_outline = result.scalar_one_or_none()
            
            if existing_outline:
                existing_outline.outline_data = outline_data
                db_outline = existing_outline
            else:
                db_outline = BookOutline(
                    project_id=project_id,
                    outline_data=outline_data
                )
                db.add(db_outline)
            
            project.status = "outline_complete"
            await db.commit()
            await db.refresh(db_outline)
            
            return BookOutlineResponse(
                id=db_outline.id,
                project_id=db_outline.project_id,
                outline_data=[ChapterOutline(**ch) for ch in outline_data],
                created_at=db_outline.created_at.isoformat(),
                updated_at=db_outline.updated_at.isoformat()
            )
        except Exception as e:
            project.status = "error"
            await db.commit()
            logger.error("Failed to generate outline", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to generate outline: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate outline", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate outline: {str(e)}")


@router.get("/api/book-writer/projects/{project_id}/outline", response_model=BookOutlineResponse)
async def get_outline(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get outline for a book project."""
    try:
        result = await db.execute(select(BookOutline).where(BookOutline.project_id == project_id))
        outline = result.scalar_one_or_none()
        
        if not outline:
            raise HTTPException(status_code=404, detail="Outline not found")
        
        return BookOutlineResponse(
            id=outline.id,
            project_id=outline.project_id,
            outline_data=[ChapterOutline(**ch) for ch in outline.outline_data],
            created_at=outline.created_at.isoformat(),
            updated_at=outline.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get outline", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get outline: {str(e)}")


@router.put("/api/book-writer/projects/{project_id}/outline", response_model=BookOutlineResponse)
async def update_outline(
    project_id: str,
    outline_data: List[ChapterOutline],
    db: AsyncSession = Depends(get_db)
):
    """Update outline for a book project."""
    try:
        result = await db.execute(select(BookOutline).where(BookOutline.project_id == project_id))
        outline = result.scalar_one_or_none()
        
        if not outline:
            raise HTTPException(status_code=404, detail="Outline not found")
        
        # Convert to dict format for storage and regenerate prompt from sections
        outline_dict = []
        for ch in outline_data:
            sections = ch.sections if hasattr(ch, 'sections') and ch.sections else []
            
            # Regenerate prompt to include updated sections
            prompt_parts = [ch.prompt.split('\n- Sections:')[0]] if '- Sections:' in ch.prompt else [ch.prompt]
            
            if sections:
                sections_text_parts = []
                for sec_idx, sec in enumerate(sections, 1):
                    section_text = f"  Section {sec_idx}: {sec.get('title', '')}"
                    if sec.get('subsections'):
                        for sub_idx, sub in enumerate(sec['subsections'], 1):
                            section_text += f"\n    - Subsection {sec_idx}.{sub_idx}: {sub.get('title', '')}"
                            if sub.get('main_points'):
                                section_text += "\n      Main Points:"
                                for mp_idx, mp in enumerate(sub['main_points'], 1):
                                    mp_text = mp.get('text', '') if isinstance(mp, dict) else str(mp)
                                    section_text += f"\n        * {mp_text}"
                    sections_text_parts.append(section_text)
                
                if sections_text_parts:
                    prompt_parts.append(f"- Sections:\n" + "\n".join(sections_text_parts))
            
            outline_dict.append({
                "chapter_number": ch.chapter_number,
                "title": ch.title,
                "prompt": "\n".join(prompt_parts),
                "sections": sections
            })
        
        outline.outline_data = outline_dict
        await db.commit()
        await db.refresh(outline)
        
        return BookOutlineResponse(
            id=outline.id,
            project_id=outline.project_id,
            outline_data=[ChapterOutline(**ch) for ch in outline.outline_data],
            created_at=outline.created_at.isoformat(),
            updated_at=outline.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update outline", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update outline: {str(e)}")


class BookGenerationResponse(BaseModel):
    """Book generation response."""
    success: bool
    total_chapters: int
    completed_chapters: int
    message: Optional[str] = None


@router.post("/api/book-writer/projects/{project_id}/generate-book", response_model=BookGenerationResponse)
async def generate_book(project_id: str, db: AsyncSession = Depends(get_db)):
    """Generate full book for a project."""
    try:
        # Get project
        result = await db.execute(select(BookProject).where(BookProject.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get outline
        result = await db.execute(select(BookOutline).where(BookOutline.project_id == project_id))
        outline = result.scalar_one_or_none()
        
        if not outline:
            raise HTTPException(status_code=404, detail="Outline not found. Generate outline first.")
        
        # Update status
        project.status = "generating"
        await db.commit()
        
        try:
            # Generate book
            agent_config = get_config()
            agents = BookAgents(agent_config, outline.outline_data)
            book_gen = BookGenerator(agents, agent_config, outline.outline_data)
            
            book_result = await book_gen.generate_book(outline.outline_data)
            
            # Save chapters
            for chapter_num, chapter_data in book_result["chapters"].items():
                # Check if chapter exists
                result = await db.execute(
                    select(BookChapter).where(
                        BookChapter.project_id == project_id,
                        BookChapter.chapter_number == chapter_data["number"]
                    )
                )
                existing_chapter = result.scalar_one_or_none()
                
                word_count = len(chapter_data["content"].split()) if chapter_data["content"] else 0
                
                if existing_chapter:
                    existing_chapter.title = chapter_data["title"]
                    existing_chapter.content = chapter_data["content"]
                    existing_chapter.prompt = chapter_data["prompt"]
                    existing_chapter.status = "error" if chapter_data.get("error") else "complete"
                    existing_chapter.word_count = word_count
                else:
                    new_chapter = BookChapter(
                        project_id=project_id,
                        chapter_number=chapter_data["number"],
                        title=chapter_data["title"],
                        content=chapter_data["content"],
                        prompt=chapter_data["prompt"],
                        status="error" if chapter_data.get("error") else "complete",
                        word_count=word_count
                    )
                    db.add(new_chapter)
            
            project.status = "complete" if book_result["completed_chapters"] == book_result["total_chapters"] else "generating"
            await db.commit()
            
            return BookGenerationResponse(
                success=True,
                total_chapters=book_result["total_chapters"],
                completed_chapters=book_result["completed_chapters"],
                message=f"Generated {book_result['completed_chapters']} out of {book_result['total_chapters']} chapters"
            )
        except Exception as e:
            project.status = "error"
            await db.commit()
            logger.error("Failed to generate book", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to generate book: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate book", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate book: {str(e)}")


@router.get("/api/book-writer/projects/{project_id}/chapters", response_model=List[BookChapterResponse])
async def list_chapters(project_id: str, db: AsyncSession = Depends(get_db)):
    """List all chapters for a project."""
    try:
        result = await db.execute(
            select(BookChapter)
            .where(BookChapter.project_id == project_id)
            .order_by(BookChapter.chapter_number)
        )
        chapters = result.scalars().all()
        
        return [
            BookChapterResponse(
                id=ch.id,
                project_id=ch.project_id,
                chapter_number=ch.chapter_number,
                title=ch.title,
                content=ch.content,
                prompt=ch.prompt,
                status=ch.status,
                word_count=ch.word_count,
                created_at=ch.created_at.isoformat(),
                updated_at=ch.updated_at.isoformat()
            )
            for ch in chapters
        ]
    except Exception as e:
        logger.error("Failed to list chapters", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list chapters: {str(e)}")


@router.get("/api/book-writer/projects/{project_id}/chapters/{chapter_number}", response_model=BookChapterResponse)
async def get_chapter(project_id: str, chapter_number: int, db: AsyncSession = Depends(get_db)):
    """Get a specific chapter."""
    try:
        result = await db.execute(
            select(BookChapter).where(
                BookChapter.project_id == project_id,
                BookChapter.chapter_number == chapter_number
            )
        )
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        return BookChapterResponse(
            id=chapter.id,
            project_id=chapter.project_id,
            chapter_number=chapter.chapter_number,
            title=chapter.title,
            content=chapter.content,
            prompt=chapter.prompt,
            status=chapter.status,
            word_count=chapter.word_count,
            created_at=chapter.created_at.isoformat(),
            updated_at=chapter.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get chapter", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get chapter: {str(e)}")


class ChapterUpdate(BaseModel):
    """Chapter update request."""
    content: str


@router.put("/api/book-writer/projects/{project_id}/chapters/{chapter_number}")
async def update_chapter(
    project_id: str,
    chapter_number: int,
    update: ChapterUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a chapter's content."""
    try:
        result = await db.execute(
            select(BookChapter).where(
                BookChapter.project_id == project_id,
                BookChapter.chapter_number == chapter_number
            )
        )
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        chapter.content = update.content
        chapter.word_count = len(update.content.split()) if update.content else 0
        await db.commit()
        await db.refresh(chapter)
        
        return BookChapterResponse(
            id=chapter.id,
            project_id=chapter.project_id,
            chapter_number=chapter.chapter_number,
            title=chapter.title,
            content=chapter.content,
            prompt=chapter.prompt,
            status=chapter.status,
            word_count=chapter.word_count,
            created_at=chapter.created_at.isoformat(),
            updated_at=chapter.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update chapter", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update chapter: {str(e)}")


@router.delete("/api/book-writer/projects/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a book project and all its data."""
    try:
        result = await db.execute(select(BookProject).where(BookProject.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        await db.delete(project)
        await db.commit()
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete project", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

