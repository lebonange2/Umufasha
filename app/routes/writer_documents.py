"""Document upload and processing for Writer Assistant."""
import os
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
import structlog
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db, AsyncSessionLocal
from app.models import BookProject, BookChapter

logger = structlog.get_logger(__name__)

router = APIRouter()

# Create uploads directory
UPLOADS_DIR = Path("app/static/writer/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Create audio output directory
AUDIO_DIR = Path("app/static/writer/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Thread pool for TTS operations
tts_executor = ThreadPoolExecutor(max_workers=1)


class DocumentInfo(BaseModel):
    """Document information model."""
    id: str
    name: str
    type: str
    size: int
    text_preview: str
    uploaded_at: str


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
        text = []
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text.append(page.extract_text())
        return '\n\n'.join(text)
    except Exception as e:
        logger.error("PDF extraction error", error=str(e))
        raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {str(e)}")


def extract_text_from_docx(file_path: Path) -> str:
    """Extract text from DOCX file."""
    try:
        from docx import Document
        doc = Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="python-docx not installed. Install with: pip install python-docx"
        )
    except Exception as e:
        logger.error("DOCX extraction error", error=str(e))
        raise HTTPException(status_code=400, detail=f"Failed to extract text from DOCX: {str(e)}")


def extract_text_from_txt(file_path: Path) -> str:
    """Extract text from TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            logger.error("TXT extraction error", error=str(e))
            raise HTTPException(status_code=400, detail=f"Failed to extract text from TXT: {str(e)}")


def extract_text_from_file(file_path: Path, file_type: str) -> str:
    """Extract text from file based on type."""
    file_type_lower = file_type.lower()
    
    if file_type_lower == 'application/pdf' or file_path.suffix.lower() == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_type_lower in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'] or file_path.suffix.lower() in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif file_type_lower == 'text/plain' or file_path.suffix.lower() == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")


@router.post("/api/writer/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document (PDF, DOCX, TXT).
    
    Returns document ID and extracted text.
    """
    try:
        # Check file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # Generate unique ID
        doc_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        saved_path = UPLOADS_DIR / f"{doc_id}{file_extension}"
        
        # Save file
        with open(saved_path, 'wb') as f:
            f.write(file_content)
        
        # Extract text
        try:
            extracted_text = extract_text_from_file(saved_path, file.content_type or '')
        except HTTPException:
            # Clean up file if extraction fails
            if saved_path.exists():
                saved_path.unlink()
            raise
        
        # Store metadata and text
        metadata_path = UPLOADS_DIR / f"{doc_id}.meta.json"
        import json
        from datetime import datetime
        metadata = {
            "id": doc_id,
            "name": file.filename,
            "type": file.content_type or "unknown",
            "size": len(file_content),
            "uploaded_at": datetime.now().isoformat(),
            "file_path": str(saved_path),
            "text_preview": extracted_text[:500]  # First 500 chars
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        # Store full text separately
        text_path = UPLOADS_DIR / f"{doc_id}.txt"
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        logger.info("Document uploaded", doc_id=doc_id, filename=file.filename, size=len(file_content))
        
        return {
            "success": True,
            "document": {
                "id": doc_id,
                "name": file.filename,
                "type": file.content_type or "unknown",
                "size": len(file_content),
                "text_preview": extracted_text[:500],
                "uploaded_at": metadata["uploaded_at"]
            },
            "text_length": len(extracted_text)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/api/writer/documents")
async def list_documents():
    """List all uploaded documents."""
    try:
        documents = []
        for meta_file in UPLOADS_DIR.glob("*.meta.json"):
            import json
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
                documents.append({
                    "id": metadata["id"],
                    "name": metadata["name"],
                    "type": metadata["type"],
                    "size": metadata["size"],
                    "text_preview": metadata.get("text_preview", ""),
                    "uploaded_at": metadata["uploaded_at"]
                })
        
        # Sort by upload time (newest first)
        documents.sort(key=lambda x: x["uploaded_at"], reverse=True)
        
        return {"success": True, "documents": documents}
    
    except Exception as e:
        logger.error("List documents error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/writer/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document text by ID."""
    try:
        text_path = UPLOADS_DIR / f"{doc_id}.txt"
        if not text_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")
        
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Get metadata
        metadata_path = UPLOADS_DIR / f"{doc_id}.meta.json"
        metadata = {}
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        return {
            "success": True,
            "document": {
                "id": doc_id,
                "name": metadata.get("name", "Unknown"),
                "text": text,
                "text_length": len(text)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get document error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/writer/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and its associated files."""
    try:
        # Delete all files with this doc_id
        deleted = []
        for file_path in UPLOADS_DIR.glob(f"{doc_id}.*"):
            file_path.unlink()
            deleted.append(str(file_path))
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info("Document deleted", doc_id=doc_id, files=deleted)
        
        return {"success": True, "deleted_files": deleted}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Delete document error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/writer/documents/{doc_id}/text")
async def add_text_context(doc_id: str, request: Request):
    """Add custom text context (not from a file)."""
    try:
        # Get text from request body
        body = await request.json()
        if isinstance(body, str):
            text = body
        elif isinstance(body, dict):
            text = body.get("text", "")
        else:
            text = str(body)
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Store as a special document
        text_id = doc_id if doc_id.startswith("text_") else f"text_{doc_id}"
        text_path = UPLOADS_DIR / f"{text_id}.txt"
        
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Store metadata
        metadata_path = UPLOADS_DIR / f"{text_id}.meta.json"
        import json
        from datetime import datetime
        metadata = {
            "id": text_id,
            "name": "Custom Text Context",
            "type": "text/plain",
            "size": len(text.encode('utf-8')),
            "uploaded_at": datetime.now().isoformat(),
            "text_preview": text[:500]
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        return {
            "success": True,
            "document": {
                "id": text_id,
                "name": "Custom Text Context",
                "text_preview": text[:500],
                "uploaded_at": metadata["uploaded_at"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Add text context error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def _init_tts_model():
    """Initialize Bark TTS model (lazy loading)."""
    try:
        from bark import generate_audio, preload_models, SAMPLE_RATE
        
        # Preload models on first initialization (this downloads models if needed)
        logger.info("Preloading Bark models (this may take a while on first run)...")
        preload_models()
        
        logger.info("Initialized Bark TTS model")
        return {
            "generate_audio": generate_audio,
            "SAMPLE_RATE": SAMPLE_RATE
        }, "bark"
    except ImportError as e:
        logger.error(f"Bark not installed: {e}")
        raise Exception(
            "Bark TTS not available. Install with: pip install git+https://github.com/suno-ai/bark.git"
        )
    except Exception as e:
        logger.error(f"Bark initialization failed: {e}")
        raise Exception(
            f"Failed to initialize Bark TTS: {str(e)}. "
            f"Install with: pip install git+https://github.com/suno-ai/bark.git"
        )


# Global TTS model instance (lazy loaded)
_tts_model = None
_tts_type = None


def get_tts_model():
    """Get or initialize Bark TTS model."""
    global _tts_model, _tts_type
    if _tts_model is None:
        try:
            _tts_model, _tts_type = _init_tts_model()
        except Exception as e:
            logger.error(f"Failed to initialize Bark TTS model: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Bark TTS not available: {str(e)}. "
                f"Install with: pip install git+https://github.com/suno-ai/bark.git"
            )
    return _tts_model, _tts_type


def text_to_speech_sync(text: str, output_path: Path, speaker_wav: Optional[str] = None):
    """Convert text to speech synchronously using Bark (runs in thread pool)."""
    try:
        # Get Bark TTS model
        try:
            bark_model, tts_type = get_tts_model()
            if tts_type != "bark":
                raise Exception("Expected Bark TTS model")
        except HTTPException as e:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Bark TTS model initialization failed: {error_msg}")
            raise Exception(
                f"Bark TTS not available: {error_msg}. "
                f"Install with: pip install git+https://github.com/suno-ai/bark.git"
            )
        
        generate_audio = bark_model["generate_audio"]
        sample_rate = bark_model["SAMPLE_RATE"]
        
        # Clean and prepare text
        # Bark works well with ~13 seconds of spoken text per chunk
        # Split text into sentences and group them into reasonable chunks
        max_chunk_length = 250  # characters per chunk (conservative for Bark)
        chunks = []
        current_chunk = ""
        
        # Split by sentences first
        sentences = text.replace('!', '.').replace('?', '.').split('. ')
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Add period back if it was removed
            if not sentence.endswith('.'):
                sentence += '.'
            
            if len(current_chunk) + len(sentence) < max_chunk_length:
                current_chunk += sentence + ' '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ' '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        if not chunks:
            chunks = [text[:max_chunk_length]]
        
        # Generate audio for each chunk and concatenate
        import soundfile as sf
        import numpy as np
        
        audio_segments = []
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            
            try:
                logger.info(f"Generating audio for chunk {i+1}/{len(chunks)} (length: {len(chunk)})")
                
                # Use voice preset if speaker_wav is provided (Bark supports history_prompt)
                # Otherwise use default voice
                history_prompt = None
                if speaker_wav:
                    # Bark can use history prompts for voice cloning, but we'll use a default for now
                    # You can extend this to support custom voice prompts
                    history_prompt = "v2/en_speaker_1"  # Default English speaker
                
                # Generate audio with Bark
                audio_array = generate_audio(
                    chunk,
                    history_prompt=history_prompt,
                    text_temp=0.7,
                    waveform_temp=0.7,
                    silent=True  # Disable progress bar
                )
                
                # Bark returns numpy array at 24kHz sample rate
                if audio_array is not None and len(audio_array) > 0:
                    audio_segments.append(audio_array)
                    logger.info(f"Generated audio chunk {i+1}, length: {len(audio_array)} samples")
                else:
                    logger.warning(f"Empty audio generated for chunk {i+1}")
                    
            except Exception as e:
                logger.warning(f"Bark chunk {i+1} failed: {e}, trying next chunk")
                continue
        
        if not audio_segments:
            raise ValueError("No audio generated from any chunks")
        
        # Concatenate all audio segments
        final_audio = np.concatenate(audio_segments)
        
        # Save final audio file
        sf.write(str(output_path), final_audio, sample_rate)
        
        logger.info("Bark TTS conversion completed", output_path=str(output_path), chunks=len(chunks), 
                   audio_length=len(final_audio), sample_rate=sample_rate)
        return str(output_path)
        
    except Exception as e:
        logger.error("Bark TTS conversion error", error=str(e), exc_info=True)
        raise


@router.post("/api/writer/documents/{doc_id}/convert-to-audio")
async def convert_pdf_to_audio(
    doc_id: str,
    speaker_wav: Optional[str] = None,
    language: str = "en"
):
    """Convert PDF document to audio using local TTS model.
    
    Args:
        doc_id: Document ID (can be uploaded doc ID, ferrari project ID, or book-writer project ID)
        speaker_wav: Optional path to speaker reference audio (for voice cloning with XTTS)
        language: Language code (default: en)
    """
    try:
        text = None
        doc_name = "document"
        
        # Check if it's an uploaded document
        text_path = UPLOADS_DIR / f"{doc_id}.txt"
        if text_path.exists():
            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.read()
            # Get metadata
            metadata_path = UPLOADS_DIR / f"{doc_id}.meta.json"
            if metadata_path.exists():
                import json
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    doc_name = metadata.get("name", "document")
        else:
            # Check if it's a ferrari-company project
            from app.routes.ferrari_company import active_projects
            if doc_id in active_projects:
                project_data = active_projects[doc_id]
                files = project_data.get("files", {})
                pdf_path = files.get("pdf")
                if pdf_path and os.path.exists(pdf_path):
                    # Extract text from PDF
                    text = extract_text_from_pdf(Path(pdf_path))
                    doc_name = project_data.get("title", "Ferrari Book")
            else:
                # Check if it's a book-writer project - fetch text directly from database
                try:
                    async with AsyncSessionLocal() as db:
                        result = await db.execute(select(BookProject).where(BookProject.id == doc_id))
                        project = result.scalar_one_or_none()
                        
                        if project:
                            # Get chapters
                            chapters_result = await db.execute(
                                select(BookChapter).where(BookChapter.project_id == doc_id).order_by(BookChapter.chapter_number)
                            )
                            chapters = chapters_result.scalars().all()
                            
                            if chapters:
                                # Create formatted text
                                text = f"# {project.title}\n\n"
                                if project.initial_prompt:
                                    text += f"**Premise:** {project.initial_prompt}\n\n"
                                
                                for chapter in chapters:
                                    text += f"## Chapter {chapter.chapter_number}: {chapter.title}\n\n"
                                    if chapter.content:
                                        text += f"{chapter.content}\n\n"
                                
                                doc_name = project.title or "Book"
                except Exception as e:
                    logger.warning(f"Could not process as book-writer project: {e}")
        
        if not text:
            raise HTTPException(status_code=404, detail="Document not found or has no text content")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Document has no text content")
        safe_name = "".join(c for c in doc_name if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        safe_name = safe_name.replace(' ', '_')
        
        # Generate audio file path
        audio_id = str(uuid.uuid4())
        audio_path = AUDIO_DIR / f"{audio_id}.wav"
        
        # Note: Bark supports history_prompt for voice cloning, but we use default for now
        # speaker_wav parameter is kept for API compatibility but not used with Bark
        
        # Run TTS conversion in thread pool (it's CPU/GPU intensive)
        logger.info("Starting TTS conversion", doc_id=doc_id, text_length=len(text))
        
        try:
            loop = asyncio.get_event_loop()
            audio_file_path = await loop.run_in_executor(
                tts_executor,
                text_to_speech_sync,
                text,
                audio_path,
                speaker_wav  # Pass speaker_wav (Bark doesn't use it but kept for API compatibility)
            )
        except Exception as e:
            error_msg = str(e)
            logger.error("TTS conversion failed", error=error_msg, exc_info=True)
            
            # Provide helpful error messages
            if "Bark" in error_msg or "bark" in error_msg.lower():
                raise HTTPException(
                    status_code=500,
                    detail="Bark TTS not available. Install with: pip install git+https://github.com/suno-ai/bark.git"
                )
            elif "TTS model not available" in error_msg or "No TTS model" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail="Bark TTS not available. Install with: pip install git+https://github.com/suno-ai/bark.git"
                )
            elif "ImportError" in error_msg or "ModuleNotFoundError" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail="Bark TTS library not found. Install with: pip install git+https://github.com/suno-ai/bark.git"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"TTS conversion failed: {error_msg}"
                )
        
        # Get audio file size
        audio_size = audio_path.stat().st_size if audio_path.exists() else 0
        
        logger.info("TTS conversion completed", audio_path=audio_file_path, size=audio_size)
        
        safe_name = "".join(c for c in doc_name if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        safe_name = safe_name.replace(' ', '_')
        
        return {
            "success": True,
            "audio": {
                "id": audio_id,
                "file_path": f"/api/writer/audio/{audio_id}",
                "filename": f"{safe_name}.wav",
                "size": audio_size,
                "document_id": doc_id,
                "document_name": doc_name
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("PDF to audio conversion error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.get("/api/writer/audio/{audio_id}")
async def get_audio_file(audio_id: str):
    """Get generated audio file."""
    try:
        audio_path = AUDIO_DIR / f"{audio_id}.wav"
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=str(audio_path),
            filename=f"{audio_id}.wav",
            media_type="audio/wav"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get audio file error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/writer/projects/{project_id}/text")
async def get_project_text(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get text content from a book-writer project for TTS conversion."""
    try:
        from app.models import BookProject, BookChapter
        from sqlalchemy import select
        
        # Get project
        result = await db.execute(select(BookProject).where(BookProject.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get chapters
        chapters_result = await db.execute(
            select(BookChapter).where(BookChapter.project_id == project_id).order_by(BookChapter.chapter_number)
        )
        chapters = chapters_result.scalars().all()
        
        if not chapters:
            raise HTTPException(status_code=404, detail="No chapters found. Generate the book first.")
        
        # Create formatted text
        text = f"# {project.title}\n\n"
        if project.initial_prompt:
            text += f"**Premise:** {project.initial_prompt}\n\n"
        
        for chapter in chapters:
            text += f"## Chapter {chapter.chapter_number}: {chapter.title}\n\n"
            if chapter.content:
                text += f"{chapter.content}\n\n"
        
        return {
            "success": True,
            "text": text,
            "title": project.title,
            "text_length": len(text)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get project text", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/writer/audio")
async def list_audio_files():
    """List all generated audio files."""
    try:
        audio_files = []
        for audio_file in AUDIO_DIR.glob("*.wav"):
            audio_id = audio_file.stem
            audio_files.append({
                "id": audio_id,
                "filename": audio_file.name,
                "size": audio_file.stat().st_size,
                "file_path": f"/api/writer/audio/{audio_id}"
            })
        
        # Sort by modification time (newest first)
        audio_files.sort(key=lambda x: (AUDIO_DIR / f"{x['id']}.wav").stat().st_mtime, reverse=True)
        
        return {"success": True, "audio_files": audio_files}
    
    except Exception as e:
        logger.error("List audio files error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

