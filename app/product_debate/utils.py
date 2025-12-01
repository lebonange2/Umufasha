"""Utility functions for product debate."""
from typing import Tuple, Optional
from app.core.config import settings


def detect_provider_from_model(model_name: str) -> str:
    """Detect provider - always returns 'local' for Ollama.
    
    Args:
        model_name: Model name (ignored, always uses local)
        
    Returns:
        Provider name: always "local"
    """
    # Always use local provider (Ollama)
    return "local"


def get_api_key_for_provider(provider: str) -> Optional[str]:
    """Get API key for the specified provider.
    
    Args:
        provider: Provider name (ignored, always returns None for local)
        
    Returns:
        Always None (local models don't need API keys)
    """
    # Local models don't need API keys
    return None


def create_llm_client_for_model(model_name: str) -> Tuple[Optional[str], str]:
    """Create LLM client configuration for a model.
    
    Args:
        model_name: Model name (e.g., "llama3.1")
        
    Returns:
        Tuple of (api_key=None, provider="local")
    """
    # Always use local provider
    return None, "local"

