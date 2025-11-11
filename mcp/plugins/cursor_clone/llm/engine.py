"""LLM engine abstraction for local models."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class LLMEngine(ABC):
    """Abstract base class for LLM engines."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize LLM engine with configuration."""
        self.config = config
        self.model_path = Path(config.get("model_path", ""))
        self.use_gpu = config.get("use_gpu", False)
        self.context_tokens = config.get("context_tokens", 8192)
        self.max_tokens = config.get("max_tokens", 1024)
        self.temperature = config.get("temperature", 0.7)
        self.top_p = config.get("top_p", 0.9)
        self.top_k = config.get("top_k", 40)
        self._loaded = False
    
    @abstractmethod
    async def load(self) -> bool:
        """Load the model. Returns True if successful."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> str:
        """Generate text from prompt. Returns generated text."""
        pass
    
    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncIterator[str]:
        """Stream tokens from prompt."""
        pass
    
    @abstractmethod
    async def unload(self):
        """Unload the model to free memory."""
        pass
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._loaded


class LLMEngineFactory:
    """Factory for creating LLM engines."""
    
    @staticmethod
    def create(config: Dict[str, Any]) -> LLMEngine:
        """Create appropriate LLM engine based on provider and model."""
        provider = config.get("provider", "local").lower()
        
        # Check provider
        if provider == "openai" or provider == "chatgpt":
            # Use OpenAI/ChatGPT
            import os
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                logger.warning("OPENAI_API_KEY environment variable not set, falling back to local model")
                logger.info("To use ChatGPT, set OPENAI_API_KEY environment variable: export OPENAI_API_KEY=your-api-key")
                provider = "local"
            else:
                logger.info("Using OpenAI/ChatGPT provider", model=config.get("model", "gpt-4o-mini"))
                from mcp.plugins.cursor_clone.llm.backends.openai_client import OpenAIClient
                return OpenAIClient(config)
        
        # Default to local model (gemma3)
        model_path = config.get("model_path", "")
        
        # Check for gemma3 model
        if "gemma" in model_path.lower() or "gemma3" in model_path.lower():
            from mcp.plugins.cursor_clone.llm.backends.gemma3_local import Gemma3LocalEngine
            return Gemma3LocalEngine(config)
        
        # Default to gemma3 for now
        logger.warning("Unknown model type, defaulting to gemma3", model_path=model_path)
        from mcp.plugins.cursor_clone.llm.backends.gemma3_local import Gemma3LocalEngine
        return Gemma3LocalEngine(config)

