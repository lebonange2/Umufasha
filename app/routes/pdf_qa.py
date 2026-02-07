"""PDF Q&A routes: upload a PDF, ask questions, and get cited answers (page + snippet)."""

import asyncio
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
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


class ModelsResponse(BaseModel):
    models: List[str]


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    pages: int


class AskRequest(BaseModel):
    doc_id: str
    question: str = Field(min_length=1)
    model: str = DEFAULT_MODEL
    top_k_pages: int = 3
    explain: bool = False


class Citation(BaseModel):
    page: int
    snippet: str


class AskResponse(BaseModel):
    answer: str
    explanation: Optional[str] = None
    citations: List[Citation]
    used_pages: List[int]

class AskAsyncResponse(BaseModel):
    job_id: str
    status: str = "processing"

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # processing|completed|failed
    result: Optional[AskResponse] = None
    error: Optional[str] = None


def _clean_pdf_text(text: str) -> str:
    """Post-process extracted PDF text to improve readability."""
    if not text:
        return ""
    # Remove soft-hyphen and zero-width chars that often appear mid-word.
    text = text.replace("\u00ad", "")  # soft hyphen
    text = text.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    # Normalize non-breaking spaces
    text = text.replace("\u00a0", " ")
    # De-hyphenate at line breaks: "com-\nputer" -> "computer"
    text = re.sub(r"([A-Za-z0-9])-\s*\n\s*([A-Za-z0-9])", r"\1\2", text)
    # Normalize newlines and whitespace
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_pages_from_pdf(file_path: Path) -> Tuple[List[str], str]:
    """Extract text per page from PDF. Returns (pages, extractor_name)."""
    # Prefer PyMuPDF (fitz) which generally preserves word boundaries better than PyPDF2.
    try:
        import fitz  # type: ignore

        pages: List[str] = []
        doc = fitz.open(str(file_path))
        try:
            for page in doc:
                # sort=True improves reading order in many PDFs
                txt = page.get_text("text", sort=True) or ""
                pages.append(_clean_pdf_text(txt))
        finally:
            doc.close()
        return pages, "pymupdf"
    except ImportError:
        pass
    except Exception as e:
        logger.warning("PyMuPDF extraction failed; falling back to PyPDF2", error=str(e))

    # Fallback: PyPDF2
    try:
        import PyPDF2  # type: ignore
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="PDF extraction requires PyMuPDF or PyPDF2. Install with: pip install pymupdf PyPDF2",
        )

    try:
        pages: List[str] = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                txt = page.extract_text() or ""
                pages.append(_clean_pdf_text(txt))
        return pages, "pypdf2"
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
        # Large local models can be slow (especially on first token). Use a generous timeout.
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(OLLAMA_CHAT_URL, json=payload)
        if resp.status_code != 200:
            # Make "model not found" actionable (common when the user hasn't pulled it yet).
            if resp.status_code == 404:
                try:
                    err = resp.json().get("error")  # {"error":"model 'x' not found"}
                except Exception:
                    err = resp.text
                suggestions = await _get_ollama_model_suggestions(model)
                hint = ""
                if suggestions:
                    hint = f"\n\nAvailable models include:\n- " + "\n- ".join(suggestions[:12])
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Ollama model not found: {model}\n\n"
                        f"Fix:\n- Pull the model: ollama pull {model}\n"
                        f"Or select an installed model on the PDF Q&A page."
                        f"{hint}"
                    ),
                )
            raise HTTPException(status_code=502, detail=f"Ollama error ({resp.status_code}): {resp.text}")
        data = resp.json()
        return (data.get("message") or {}).get("content") or ""
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama at http://localhost:11434. Start it with: ollama serve",
        )


async def _get_ollama_models() -> List[str]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(OLLAMA_TAGS_URL)
        if resp.status_code != 200:
            return []
        data = resp.json()
        models = [m.get("name") for m in data.get("models", []) if isinstance(m, dict) and m.get("name")]
        return [str(x) for x in models]
    except Exception:
        return []


async def _get_ollama_model_suggestions(requested: str) -> List[str]:
    models = await _get_ollama_models()
    if not models:
        return []
    r = (requested or "").lower()
    # Prefer qwen 32b-ish models if requested is qwen:32b.
    if "qwen" in r and "32" in r:
        preferred = [m for m in models if "qwen" in m.lower() and "32" in m.lower()]
        if preferred:
            return preferred
    # Otherwise return all models (sorted) so the UI can show them.
    return sorted(models)


@router.get("/models", response_model=ModelsResponse)
async def get_models():
    """List locally available Ollama models."""
    models = await _get_ollama_models()
    return ModelsResponse(models=models)


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

    # Auto-upgrade older extractions (e.g., from previous versions) if the original PDF is available.
    extractor = (meta or {}).get("extractor")
    pdf_path = UPLOADS_DIR / f"{doc_id}.pdf"
    if extractor != "pymupdf" and pdf_path.exists():
        try:
            new_pages, used = _extract_pages_from_pdf(pdf_path)
            if new_pages and sum(len(p.strip()) for p in new_pages) > sum(len(str(p or "").strip()) for p in pages):
                pages = new_pages
                meta["extractor"] = used
                with open(pages_path, "w", encoding="utf-8") as f:
                    json.dump({"pages": pages}, f)
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f)
        except Exception:
            # Best-effort; keep original pages if upgrade fails.
            pass

    return [str(p or "") for p in pages], meta


# In-memory job store (good enough for a single-process deployment).
# Format:
#   {job_id: {"status": "...", "result": AskResponse|None, "error": str|None}}
qa_jobs: Dict[str, Dict[str, Any]] = {}


async def _run_qa_job(job_id: str, req: AskRequest) -> None:
    try:
        result = await _answer_question(req)
        qa_jobs[job_id] = {"status": "completed", "result": result, "error": None}
    except Exception as e:
        # Ensure we don't leak internal traces to the UI; stringify as best-effort.
        msg = getattr(e, "detail", None) if isinstance(e, HTTPException) else str(e)
        qa_jobs[job_id] = {"status": "failed", "result": None, "error": msg or "Unknown error"}


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

    pages, extractor = _extract_pages_from_pdf(pdf_path)

    meta = {
        "doc_id": doc_id,
        "filename": file.filename,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
        "bytes": len(content),
        "pages": len(pages),
        "extractor": extractor,
    }
    with open(PROCESSED_DIR / f"{doc_id}.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)
    with open(PROCESSED_DIR / f"{doc_id}.pages.json", "w", encoding="utf-8") as f:
        json.dump({"pages": pages}, f)

    logger.info("PDF uploaded", doc_id=doc_id, pages=len(pages), filename=file.filename)
    return UploadResponse(doc_id=doc_id, filename=file.filename or "document.pdf", pages=len(pages))


def _extract_answer_and_explanation(model_text: str) -> Tuple[str, Optional[str]]:
    """Try to parse model output into answer + explanation."""
    t = (model_text or "").strip()
    if not t:
        return "", None
    # Try JSON first
    try:
        obj = json.loads(t)
        if isinstance(obj, dict) and ("answer" in obj or "explanation" in obj):
            ans = str(obj.get("answer") or "").strip()
            expl = obj.get("explanation")
            expl_s = str(expl).strip() if expl is not None else None
            return ans, expl_s
    except Exception:
        pass

    # Fallback: split on common marker
    m = re.split(r"\n\s*Explanation\s*:\s*\n|\n\s*Explanation\s*:\s*", t, maxsplit=1, flags=re.IGNORECASE)
    if len(m) == 2:
        return m[0].strip(), m[1].strip()
    return t, None


async def _answer_question(req: AskRequest) -> AskResponse:
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

    if req.explain:
        system = (
            "You answer questions about a PDF using ONLY the provided context. "
            "If the answer isn't in the context, say you don't know based on the document. "
            "Return JSON with keys: answer, explanation. "
            "explanation should briefly justify using the cited context."
        )
    else:
        system = (
            "You answer questions about a PDF using ONLY the provided context. "
            "If the answer isn't in the context, say you don't know based on the document. "
            "Be concise."
        )
    user = f"Question: {req.question}\n\nContext:\n{context}"
    model_text = await _ollama_chat(req.model or DEFAULT_MODEL, [{"role": "system", "content": system}, {"role": "user", "content": user}])
    answer, explanation = _extract_answer_and_explanation(model_text)
    answer = (answer or "").strip()
    if not answer:
        answer = "I couldn't produce an answer based on the document context."

    # Provide citations from retrieval (deterministic): page + snippet.
    citations: List[Citation] = []
    for p in top_pages[:2]:
        snippet = _make_snippet(pages[p], req.question)
        if snippet:
            citations.append(Citation(page=p + 1, snippet=snippet))

    if not citations and top_pages:
        citations = [Citation(page=top_pages[0] + 1, snippet=_make_snippet(pages[top_pages[0]], req.question) or "")]

    return AskResponse(answer=answer, explanation=explanation if req.explain else None, citations=citations, used_pages=used_pages_1based)


@router.post("/ask", response_model=AskResponse)
async def ask_pdf(req: AskRequest):
    """Synchronous ask (may time out behind some proxies)."""
    return await _answer_question(req)


@router.post("/ask_async", response_model=AskAsyncResponse)
async def ask_pdf_async(req: AskRequest):
    """Async ask that avoids long-held HTTP connections (better for RunPod/Cloudflare)."""
    job_id = str(uuid.uuid4())
    qa_jobs[job_id] = {"status": "processing", "result": None, "error": None}
    asyncio.create_task(_run_qa_job(job_id, req))
    return AskAsyncResponse(job_id=job_id)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    job = qa_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    status = job.get("status", "processing")
    result = job.get("result")
    error = job.get("error")
    return JobStatusResponse(job_id=job_id, status=status, result=result, error=error)

