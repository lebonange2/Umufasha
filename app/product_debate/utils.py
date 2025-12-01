"""Utility functions for product debate."""
from typing import Tuple, Optional
from app.core.config import settings


def detect_provider_from_model(model_name: str) -> str:
    """Detect provider (openai/anthropic) from model name.
    
    Args:
        model_name: Model name (e.g., "gpt-4o", "claude-3-5-sonnet-20240620")
        
    Returns:
        Provider name: "openai" or "anthropic"
    """
    model_lower = model_name.lower()
    
    # Check for Anthropic/Claude models
    if model_lower.startswith("claude") or "claude" in model_lower:
        return "anthropic"
    
    # Check for OpenAI models
    if model_lower.startswith("gpt") or "gpt" in model_lower:
        return "openai"
    
    # Default to OpenAI if unclear
    return "openai"


def get_api_key_for_provider(provider: str) -> Optional[str]:
    """Get API key for the specified provider.
    
    Args:
        provider: Provider name ("openai" or "anthropic")
        
    Returns:
        API key or None if not set
    """
    if provider == "anthropic":
        return settings.ANTHROPIC_API_KEY
    elif provider == "openai":
        return settings.OPENAI_API_KEY
    return None


def create_llm_client_for_model(model_name: str) -> Tuple[Optional[str], str]:
    """Create LLM client configuration for a model.
    
    Args:
        model_name: Model name
        
    Returns:
        Tuple of (api_key, provider)
    """
    provider = detect_provider_from_model(model_name)
    api_key = get_api_key_for_provider(provider)
    return api_key, provider

