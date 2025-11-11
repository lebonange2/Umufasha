"""Document upload and processing for Writer Assistant."""
import os
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()

# Create uploads directory
UPLOADS_DIR = Path("app/static/writer/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


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

