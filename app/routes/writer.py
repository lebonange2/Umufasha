"""Writer API routes for Book Writing Assistant."""
import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import structlog

from app.llm.client import LLMClient
from app.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()


class LLMRequest(BaseModel):
    """LLM request model."""
    system: Optional[str] = None
    prompt: str
    context: Optional[str] = None
    document_context: Optional[List[str]] = None  # List of document IDs to include
    text_context: Optional[str] = None  # Additional text context
    mode: str  # autocomplete|continue|expand|summarize|outline|rewrite|qa
    provider: Optional[str] = None  # Ignored - always uses local (Ollama)
    model: Optional[str] = None  # Model name - if not provided, uses default from config
    params: Optional[Dict[str, Any]] = None
    stream: bool = True


@router.post("/api/llm")
async def llm_endpoint(request: Request, llm_request: LLMRequest):
    """Streaming LLM endpoint for writer assistant.
    
    Supports Server-Sent Events (SSE) streaming for real-time token delivery.
    """
    try:
        # Force local provider (Ollama) - no API keys needed
        provider = "local"
        model = llm_request.model or settings.LLM_MODEL
        base_url = getattr(settings, 'LLM_LOCAL_URL', 'http://localhost:11434/v1')
        
        # Create LLM client with local provider
        llm_client = LLMClient(
            api_key=None,  # No API key needed for local models
            base_url=base_url,
            model=model,
            provider=provider
        )
        
        # Build system prompt based on mode
        system_prompt = llm_request.system or _get_default_system_prompt(llm_request.mode)
        
        # Load document contexts if provided
        document_texts = []
        if llm_request.document_context:
            document_texts = await _load_document_contexts(llm_request.document_context)
        
        # Build user prompt with context (including documents)
        user_prompt = _build_user_prompt(llm_request, document_texts, llm_request.text_context)
        
        # Get parameters
        params = llm_request.params or {}
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 1000)
        
        # Check if streaming
        if llm_request.stream:
            async def generate_stream():
                """Generator for streaming tokens."""
                try:
                    # Use OpenAI-style streaming if available
                    if hasattr(llm_client, 'stream'):
                        async for token in llm_client.stream(
                            prompt=user_prompt,
                            system_prompt=system_prompt,
                            max_tokens=max_tokens,
                            temperature=temperature
                        ):
                            yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
                    else:
                        # Fallback: use complete and simulate streaming
                        response = await llm_client.complete(
                            system=system_prompt,
                            user=user_prompt
                        )
                        # Stream word by word
                        words = response.split()
                        for word in words:
                            yield f"data: {json.dumps({'token': word + ' ', 'done': False})}\n\n"
                            import asyncio
                            await asyncio.sleep(0.02)  # Small delay for streaming effect
                    
                    # Send completion signal
                    yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"
                except Exception as e:
                    logger.error("Streaming error", error=str(e))
                    yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Non-streaming response
            response = await llm_client.complete(
                system=system_prompt,
                user=user_prompt
            )
            return {
                "response": response,
                "done": True
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("LLM endpoint error", error=str(e), exc_info=True)
        # Check if Ollama is running
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:11434/api/tags", timeout=2.0)
                if response.status_code != 200:
                    error_msg = "Ollama service is not responding. Make sure Ollama is running: ollama serve"
                else:
                    error_msg = f"LLM error: {str(e)}"
        except:
            error_msg = "Ollama service is not running. Start it with: ollama serve"
        raise HTTPException(status_code=500, detail=error_msg)


def _get_default_system_prompt(mode: str) -> str:
    """Get default system prompt based on mode."""
    base = """You are a concise, structure-aware book writing assistant. 
Honor user voice and preserve factual details. 
Never fabricate citations. Avoid repetition. 
When asked to continue, maintain tense, POV, and style of the last 50 tokens."""
    
    mode_specific = {
        "autocomplete": "Complete the current sentence naturally in <= 40 words. Return only the completion, no preface.",
        "continue": "Continue this draft for ~150–250 words, matching tone and POV. Avoid repeating the last lines. Introduce 1 new concrete detail.",
        "expand": "Expand the selection to the target word count, preserving meaning and style.",
        "summarize": "Provide a brief, accurate summary of the selection.",
        "outline": "Produce a hierarchical outline (Chapters > Sections > Beats) from the draft. Return JSON with: title, chapters[{title, summary, sections[{title, beats[]}] }].",
        "rewrite": "Rewrite the selection in the requested tone. Keep facts. Return text only.",
        "qa": "Answer questions about the selection concisely and accurately."
    }
    
    return f"{base}\n\n{mode_specific.get(mode, '')}"


async def _load_document_contexts(document_ids: List[str]) -> List[str]:
    """Load text from document IDs."""
    from pathlib import Path
    uploads_dir = Path("app/static/writer/uploads")
    texts = []
    
    for doc_id in document_ids:
        text_path = uploads_dir / f"{doc_id}.txt"
        if text_path.exists():
            try:
                with open(text_path, 'r', encoding='utf-8') as f:
                    texts.append(f.read())
            except Exception as e:
                logger.warning("Failed to load document", doc_id=doc_id, error=str(e))
    
    return texts


def _build_user_prompt(llm_request: LLMRequest, document_texts: List[str] = None, text_context: Optional[str] = None) -> str:
    """Build user prompt from request with document and text context."""
    mode = llm_request.mode
    
    # Build context sections
    context_parts = []
    
    # Add document contexts
    if document_texts:
        doc_context = "\n\n---\n\n".join([f"Document {i+1}:\n{doc_text}" for i, doc_text in enumerate(document_texts)])
        context_parts.append(f"Reference Documents:\n{doc_context}")
    
    # Add text context
    if text_context:
        context_parts.append(f"Additional Context:\n{text_context}")
    
    # Add current document context
    if llm_request.context:
        context_parts.append(f"Current Document:\n{llm_request.context}")
    
    full_context = "\n\n---\n\n".join(context_parts) if context_parts else ""
    
    if mode == "autocomplete":
        return f"{full_context}\n\nComplete the current sentence:" if full_context else "Complete the current sentence:"
    
    elif mode == "continue":
        return f"{full_context}\n\nContinue writing:" if full_context else "Continue writing:"
    
    elif mode == "expand":
        target_words = llm_request.params.get("target_words", 100) if llm_request.params else 100
        return f"{full_context}\n\nExpand the selection to ~{target_words} words, preserving meaning and style.\n\nSelection:\n{llm_request.context or ''}"
    
    elif mode == "summarize":
        return f"{full_context}\n\nSummarize this section:\n\n{llm_request.context or ''}" if full_context else f"Summarize this section:\n\n{llm_request.context or ''}"
    
    elif mode == "outline":
        return f"{full_context}\n\nDraft:\n{llm_request.context or llm_request.prompt}\n\nGenerate an outline:"
    
    elif mode == "rewrite":
        tone = llm_request.params.get("tone", "plain") if llm_request.params else "plain"
        return f"{full_context}\n\nRewrite the selection in the style: {tone}. Keep facts. Return text only.\n\nSelection:\n{llm_request.context or ''}"
    
    elif mode == "qa":
        return f"{full_context}\n\nQuestion: {llm_request.prompt}\n\nAnswer:" if full_context else f"Question: {llm_request.prompt}\n\nAnswer:"
    
    else:
        # Generic fallback
        if full_context:
            return f"{llm_request.prompt}\n\n{full_context}"
        return llm_request.prompt

