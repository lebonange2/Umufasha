"""Document upload and processing for Writer Assistant."""
import os
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
import structlog
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
    """Initialize TTS model (lazy loading)."""
    try:
        # Try Coqui TTS XTTS v2 first (best quality)
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
            logger.warning("Coqui TTS not installed, trying Piper TTS")
        except Exception as e:
            logger.warning(f"Coqui TTS initialization failed: {e}, trying Piper TTS")
        
        # Fallback to Piper TTS (lighter, faster)
        try:
            from piper import PiperVoice
            from piper.download import ensure_voice_exists, find_voice
            import json
            
            # Download and use Piper voice
            voice_name = "en_US-lessac-medium"
            voice_path = ensure_voice_exists(voice_name, [])
            config_path = find_voice(voice_name, [])
            
            tts = PiperVoice.load(voice_path, config_path=config_path)
            logger.info("Initialized Piper TTS model")
            return tts, "piper"
        except ImportError:
            logger.error("Piper TTS not installed")
        except Exception as e2:
            logger.error(f"Piper TTS initialization failed: {e2}")
        
        # If both fail, raise exception
        raise Exception(
            "No TTS model available. Install Coqui TTS: pip install TTS, or Piper TTS: pip install piper-tts"
        )
    except Exception as e:
        logger.error(f"TTS model initialization error: {e}")
        raise


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
            raise HTTPException(
                status_code=500,
                detail=f"TTS model not available: {str(e)}. Install with: pip install TTS or pip install piper-tts"
            )
    return _tts_model, _tts_type


def text_to_speech_sync(text: str, output_path: Path, speaker_wav: Optional[str] = None):
    """Convert text to speech synchronously (runs in thread pool)."""
    try:
        tts, tts_type = get_tts_model()
        
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
            elif tts_type == "piper":
                # Piper TTS
                with open(chunk_output, "wb") as f:
                    tts.synthesize(chunk, f)
            
            # Load and append audio
            if chunk_output.exists():
                data, sample_rate = sf.read(str(chunk_output))
                audio_segments.append(data)
                # Clean up chunk file
                chunk_output.unlink()
        
        if not audio_segments:
            raise ValueError("No audio generated")
        
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
        doc_id: Document ID
        speaker_wav: Optional path to speaker reference audio (for voice cloning with XTTS)
        language: Language code (default: en)
    """
    try:
        # Get document text
        text_path = UPLOADS_DIR / f"{doc_id}.txt"
        if not text_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")
        
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Document has no text content")
        
        # Get metadata
        metadata_path = UPLOADS_DIR / f"{doc_id}.meta.json"
        metadata = {}
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        doc_name = metadata.get("name", "document")
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
        
        loop = asyncio.get_event_loop()
        audio_file_path = await loop.run_in_executor(
            tts_executor,
            text_to_speech_sync,
            text,
            audio_path,
            speaker_path
        )
        
        # Get audio file size
        audio_size = audio_path.stat().st_size if audio_path.exists() else 0
        
        logger.info("TTS conversion completed", audio_path=audio_file_path, size=audio_size)
        
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

