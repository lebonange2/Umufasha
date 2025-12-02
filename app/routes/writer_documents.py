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
    """Initialize TTS model (lazy loading) with multiple fallback options."""
    import sys
    
    python_version = sys.version_info
    logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Try Coqui TTS XTTS v2 first (best quality, but requires Python <3.12)
    if python_version.major == 3 and python_version.minor < 12:
        try:
            from TTS.api import TTS
            import torch
            
            tts = TTS(
                model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                progress_bar=False,
                gpu=torch.cuda.is_available()
            )
            logger.info("Initialized Coqui TTS XTTS v2 model")
            return tts, "coqui_xtts"
        except ImportError:
            logger.warning("Coqui TTS not installed, trying alternatives")
        except Exception as e:
            logger.warning(f"Coqui TTS initialization failed: {e}, trying alternatives")
    else:
        logger.info("Python 3.12+ detected, skipping Coqui TTS (not compatible)")
    
    # Try Piper TTS (works with Python 3.12+)
    try:
        from piper import PiperVoice
        from piper.download import ensure_voice_exists, find_voice
        
        # Download and use Piper voice
        voice_name = "en_US-lessac-medium"
        voice_path = ensure_voice_exists(voice_name, [])
        config_path = find_voice(voice_name, [])
        
        tts = PiperVoice.load(voice_path, config_path=config_path)
        logger.info("Initialized Piper TTS model")
        return tts, "piper"
    except ImportError:
        logger.warning("Piper TTS not installed, trying edge-tts")
    except Exception as e:
        logger.warning(f"Piper TTS initialization failed: {e}, trying edge-tts")
    
    # Try edge-tts (Microsoft Edge TTS - works with Python 3.12+, requires internet)
    try:
        import edge_tts
        logger.info("Initialized edge-tts (Microsoft Edge TTS)")
        return edge_tts, "edge_tts"
    except ImportError:
        logger.warning("edge-tts not installed, trying gTTS")
    except Exception as e:
        logger.warning(f"edge-tts initialization failed: {e}, trying gTTS")
    
    # Try gTTS (Google Text-to-Speech - works with Python 3.12+, requires internet)
    try:
        from gtts import gTTS
        import io
        logger.info("Initialized gTTS (Google Text-to-Speech)")
        return {"gTTS": gTTS, "io": io}, "gtts"
    except ImportError:
        logger.warning("gTTS not installed, trying pyttsx3")
    except Exception as e:
        logger.warning(f"gTTS initialization failed: {e}, trying pyttsx3")
    
    # Try pyttsx3 (system TTS - works with Python 3.12+, offline but quality varies)
    try:
        import pyttsx3
        engine = pyttsx3.init()
        # Set properties for better quality
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 0.9)  # Volume level
        # Try to set a better voice if available
        voices = engine.getProperty('voices')
        if voices:
            # Prefer female voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
        logger.info("Initialized pyttsx3 (system TTS)")
        return engine, "pyttsx3"
    except ImportError:
        logger.warning("pyttsx3 not installed")
    except Exception as e:
        logger.warning(f"pyttsx3 initialization failed: {e}")
    
    # If all fail, raise exception with helpful message
    python_version_str = f"{python_version.major}.{python_version.minor}"
    if python_version.minor >= 12:
        raise Exception(
            f"No TTS model available for Python {python_version_str}. "
            f"Install one of: pip install edge-tts (recommended), pip install gtts, or pip install pyttsx3. "
            f"Note: Coqui TTS requires Python <3.12."
        )
    else:
        raise Exception(
            f"No TTS model available. Install one of: "
            f"pip install TTS (Coqui TTS), pip install piper-tts, "
            f"pip install edge-tts, pip install gtts, or pip install pyttsx3"
        )


# Global TTS model instance (lazy loaded)
_tts_model = None
_tts_type = None


def get_tts_model():
    """Get or initialize TTS model."""
    global _tts_model, _tts_type
    if _tts_model is None:
        try:
            _tts_model, _tts_type = _init_tts_model()
        except Exception as e:
            logger.error(f"Failed to initialize TTS model: {e}")
            import sys
            python_version = sys.version_info
            if python_version.minor >= 12:
                raise HTTPException(
                    status_code=500,
                    detail=f"TTS model not available: {str(e)}. "
                    f"For Python 3.12+, install one of: pip install edge-tts (recommended), "
                    f"pip install gtts, or pip install pyttsx3"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"TTS model not available: {str(e)}. "
                    f"Install one of: pip install TTS, pip install piper-tts, "
                    f"pip install edge-tts, pip install gtts, or pip install pyttsx3"
                )
    return _tts_model, _tts_type


def text_to_speech_sync(text: str, output_path: Path, speaker_wav: Optional[str] = None):
    """Convert text to speech synchronously (runs in thread pool)."""
    try:
        # Try to get TTS model, with better error handling
        try:
            tts, tts_type = get_tts_model()
        except HTTPException as e:
            # Re-raise HTTP exceptions (they have proper error messages)
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"TTS model initialization failed: {error_msg}")
            raise Exception(
                f"TTS model not available: {error_msg}. "
                f"Install with: pip install TTS (for Coqui TTS) or pip install piper-tts (for Piper TTS). "
                f"Note: Coqui TTS requires Python <3.12. For Python 3.12+, use Piper TTS."
            )
        
        # Clean and prepare text
        # Split into chunks if too long (TTS models have limits)
        max_chunk_length = 500  # characters per chunk
        chunks = []
        current_chunk = ""
        
        sentences = text.split('. ')
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chunk_length:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        if not chunks:
            chunks = [text[:max_chunk_length]]
        
        # Generate audio for each chunk and concatenate
        import soundfile as sf
        import numpy as np
        
        audio_segments = []
        sample_rate = 22050  # Default sample rate
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
                
            chunk_output = output_path.parent / f"{output_path.stem}_chunk_{i}.wav"
            
            if tts_type == "coqui_xtts":
                # Coqui XTTS v2
                if speaker_wav and os.path.exists(speaker_wav):
                    tts.tts_to_file(
                        text=chunk,
                        file_path=str(chunk_output),
                        speaker_wav=speaker_wav,
                        language="en"
                    )
                else:
                    # Use default speaker
                    tts.tts_to_file(
                        text=chunk,
                        file_path=str(chunk_output),
                        language="en"
                    )
                # Load audio to get sample rate
                if chunk_output.exists():
                    data, sample_rate = sf.read(str(chunk_output))
                    audio_segments.append(data)
                    chunk_output.unlink()
                    
            elif tts_type == "piper":
                # Piper TTS
                with open(chunk_output, "wb") as f:
                    tts.synthesize(chunk, f)
                # Load audio to get sample rate
                if chunk_output.exists():
                    data, sample_rate = sf.read(str(chunk_output))
                    audio_segments.append(data)
                    chunk_output.unlink()
                    
            elif tts_type == "edge_tts":
                # Microsoft Edge TTS (requires internet)
                import asyncio
                import edge_tts
                
                async def generate_edge_tts():
                    communicate = edge_tts.Communicate(chunk, "en-US-AriaNeural")
                    await communicate.save(str(chunk_output))
                
                # Run async function
                try:
                    # Try to get existing event loop, or create new one
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_closed():
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    loop.run_until_complete(generate_edge_tts())
                except Exception as e:
                    logger.warning(f"edge-tts chunk {i} failed: {e}, trying next chunk")
                    continue
                
                # Load audio
                if chunk_output.exists():
                    data, sample_rate = sf.read(str(chunk_output))
                    audio_segments.append(data)
                    chunk_output.unlink()
                    
            elif tts_type == "gtts":
                # Google Text-to-Speech (requires internet)
                import io
                
                try:
                    # Generate speech
                    gTTS_class = tts["gTTS"]
                    tts_obj = gTTS_class(text=chunk, lang='en', slow=False)
                    mp3_buffer = io.BytesIO()
                    tts_obj.write_to_fp(mp3_buffer)
                    mp3_buffer.seek(0)
                    
                    # Convert MP3 to WAV using pydub
                    try:
                        from pydub import AudioSegment
                        audio = AudioSegment.from_mp3(mp3_buffer)
                        audio.export(str(chunk_output), format="wav")
                    except ImportError:
                        # Fallback: save as MP3 and let soundfile handle it (may not work)
                        logger.warning("pydub not available, trying direct MP3 save")
                        with open(str(chunk_output).replace('.wav', '.mp3'), 'wb') as f:
                            f.write(mp3_buffer.getvalue())
                        # Try to read MP3 directly (may fail)
                        chunk_output = Path(str(chunk_output).replace('.wav', '.mp3'))
                    
                    # Load audio
                    if chunk_output.exists():
                        data, sample_rate = sf.read(str(chunk_output))
                        audio_segments.append(data)
                        chunk_output.unlink()
                except Exception as e:
                    logger.warning(f"gTTS chunk {i} failed: {e}, trying next chunk")
                    continue
                    
            elif tts_type == "pyttsx3":
                # System TTS (offline, quality varies)
                import tempfile
                import wave
                
                try:
                    # Save to temporary WAV file
                    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                    temp_wav_path = temp_wav.name
                    temp_wav.close()
                    
                    tts.save_to_file(chunk, temp_wav_path)
                    tts.runAndWait()
                    
                    # Load and convert to proper format
                    if os.path.exists(temp_wav_path):
                        # Read WAV file
                        with wave.open(temp_wav_path, 'rb') as wav_file:
                            sample_rate = wav_file.getframerate()
                            frames = wav_file.readframes(wav_file.getnframes())
                            # Convert to numpy array
                            import struct
                            audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                            audio_segments.append(audio_data)
                        os.unlink(temp_wav_path)
                except Exception as e:
                    logger.warning(f"pyttsx3 chunk {i} failed: {e}, trying next chunk")
                    continue
        
        if not audio_segments:
            raise ValueError("No audio generated from any chunks")
        
        # Concatenate all audio segments
        final_audio = np.concatenate(audio_segments)
        
        # Save final audio file
        sf.write(str(output_path), final_audio, sample_rate)
        
        logger.info("TTS conversion completed", output_path=str(output_path), chunks=len(chunks))
        return str(output_path)
        
    except Exception as e:
        logger.error("TTS conversion error", error=str(e), exc_info=True)
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
        
        # Check if speaker reference file exists
        speaker_path = None
        if speaker_wav:
            speaker_path_obj = Path(speaker_wav)
            if speaker_path_obj.exists():
                speaker_path = str(speaker_path_obj)
            else:
                logger.warning(f"Speaker reference file not found: {speaker_wav}")
        
        # Run TTS conversion in thread pool (it's CPU/GPU intensive)
        logger.info("Starting TTS conversion", doc_id=doc_id, text_length=len(text))
        
        try:
            loop = asyncio.get_event_loop()
            audio_file_path = await loop.run_in_executor(
                tts_executor,
                text_to_speech_sync,
                text,
                audio_path,
                speaker_path
            )
        except Exception as e:
            error_msg = str(e)
            logger.error("TTS conversion failed", error=error_msg, exc_info=True)
            
            # Provide helpful error messages
            if "TTS model not available" in error_msg or "No TTS model" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail="TTS models are not installed. Install with: pip install TTS (or pip install piper-tts for Python 3.12+)"
                )
            elif "ImportError" in error_msg or "ModuleNotFoundError" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail="TTS library not found. Install with: pip install TTS (or pip install piper-tts for Python 3.12+)"
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

