"""PDF Q&A routes: upload a PDF, ask questions, and get cited answers (page + snippet)."""

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import structlog
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter()

PDF_QA_DIR = Path("app/static/pdf-qa")
UPLOADS_DIR = PDF_QA_DIR / "uploads"
PROCESSED_DIR = PDF_QA_DIR / "processed"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 75 * 1024 * 1024  # 75MB
DEFAULT_MODEL = "qwen:32b"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    pages: int


class AskRequest(BaseModel):
    doc_id: str
    question: str = Field(min_length=1)
    model: str = DEFAULT_MODEL
    top_k_pages: int = 3


class Citation(BaseModel):
    page: int
    snippet: str


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    used_pages: List[int]


def _extract_pages_from_pdf(file_path: Path) -> List[str]:
    """Extract text per page from PDF."""
    try:
        import PyPDF2  # type: ignore
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="PyPDF2 is not installed. Install it with: pip install PyPDF2",
        )

    try:
        pages: List[str] = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text() or ""
                pages.append(text)
        return pages
    except HTTPException:
        raise
    except Exception as e:
        logger.error("PDF extraction failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {str(e)}")


def _tokenize(s: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9]{2,}", s.lower())


def _score_page(query_tokens: List[str], page_text: str) -> int:
    if not page_text:
        return 0
    hay = page_text.lower()
    score = 0
    for t in query_tokens:
        score += hay.count(t)
    return score


def _pick_top_pages(question: str, pages: List[str], k: int) -> List[int]:
    k = max(1, min(int(k or 3), 8))
    q_tokens = _tokenize(question)
    scored = [(idx, _score_page(q_tokens, txt)) for idx, txt in enumerate(pages)]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = [idx for idx, score in scored[:k] if score > 0]
    if not top:
        # fallback: first page with content, otherwise page 1
        for i, txt in enumerate(pages):
            if (txt or "").strip():
                return [i]
        return [0] if pages else []
    return top


def _make_snippet(page_text: str, question: str, max_len: int = 480) -> str:
    txt = re.sub(r"\s+", " ", (page_text or "")).strip()
    if not txt:
        return ""
    tokens = _tokenize(question)[:8]
    best_pos: Optional[int] = None
    low = txt.lower()
    for t in tokens:
        p = low.find(t)
        if p != -1 and (best_pos is None or p < best_pos):
            best_pos = p
    if best_pos is None:
        snippet = txt[:max_len]
        return snippet + ("…" if len(txt) > len(snippet) else "")
    start = max(0, best_pos - 180)
    end = min(len(txt), best_pos + 300)
    snippet = txt[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(txt):
        snippet = snippet + "…"
    if len(snippet) > max_len:
        snippet = snippet[: max_len - 1].rstrip() + "…"
    return snippet


async def _ollama_chat(model: str, messages: List[Dict[str, str]]) -> str:
    """Call Ollama /api/chat and return assistant content."""
    payload: Dict[str, Any] = {"model": model, "messages": messages, "stream": False}
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(OLLAMA_CHAT_URL, json=payload)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Ollama error ({resp.status_code}): {resp.text}")
        data = resp.json()
        return (data.get("message") or {}).get("content") or ""
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama at http://localhost:11434. Start it with: ollama serve",
        )


def _load_pages(doc_id: str) -> Tuple[List[str], Dict[str, Any]]:
    pages_path = PROCESSED_DIR / f"{doc_id}.pages.json"
    meta_path = PROCESSED_DIR / f"{doc_id}.meta.json"
    if not pages_path.exists() or not meta_path.exists():
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")
    with open(pages_path, "r", encoding="utf-8") as f:
        pages = json.load(f).get("pages", [])
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    if not isinstance(pages, list):
        pages = []
    return [str(p or "") for p in pages], meta


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF and preprocess it into per-page text."""
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 75MB).")
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file.")

    doc_id = str(uuid.uuid4())
    pdf_path = UPLOADS_DIR / f"{doc_id}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(content)

    pages = _extract_pages_from_pdf(pdf_path)

    meta = {
        "doc_id": doc_id,
        "filename": file.filename,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
        "bytes": len(content),
        "pages": len(pages),
    }
    with open(PROCESSED_DIR / f"{doc_id}.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)
    with open(PROCESSED_DIR / f"{doc_id}.pages.json", "w", encoding="utf-8") as f:
        json.dump({"pages": pages}, f)

    logger.info("PDF uploaded", doc_id=doc_id, pages=len(pages), filename=file.filename)
    return UploadResponse(doc_id=doc_id, filename=file.filename or "document.pdf", pages=len(pages))


@router.post("/ask", response_model=AskResponse)
async def ask_pdf(req: AskRequest):
    pages, meta = _load_pages(req.doc_id)
    if not pages:
        raise HTTPException(status_code=400, detail="PDF has no extractable text.")

    top_pages = _pick_top_pages(req.question, pages, req.top_k_pages)
    used_pages_1based = [p + 1 for p in top_pages]

    # Build context for the model. Keep it compact to fit in-context limits.
    context_blocks: List[str] = []
    for p in top_pages:
        raw = re.sub(r"\s+", " ", pages[p]).strip()
        raw = raw[:4500]
        context_blocks.append(f"[PAGE {p+1}]\n{raw}")
    context = "\n\n---\n\n".join(context_blocks)

    system = (
        "You answer questions about a PDF using ONLY the provided context. "
        "If the answer isn't in the context, say you don't know based on the document. "
        "Be concise."
    )
    user = f"Question: {req.question}\n\nContext:\n{context}"
    answer = await _ollama_chat(req.model or DEFAULT_MODEL, [{"role": "system", "content": system}, {"role": "user", "content": user}])
    answer = (answer or "").strip()
    if not answer:
        answer = "I couldn't produce an answer."

    # Provide citations from retrieval (deterministic): page + snippet.
    citations: List[Citation] = []
    for p in top_pages[:2]:
        snippet = _make_snippet(pages[p], req.question)
        if snippet:
            citations.append(Citation(page=p + 1, snippet=snippet))

    if not citations and top_pages:
        citations = [Citation(page=top_pages[0] + 1, snippet=_make_snippet(pages[top_pages[0]], req.question) or "")]

    return AskResponse(answer=answer, citations=citations, used_pages=used_pages_1based)

