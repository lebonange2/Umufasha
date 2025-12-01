"""Configuration for the book generation system."""
from typing import Dict
from app.core.config import settings


def get_config() -> Dict:
    """Get the configuration for the agents."""
    # Use the existing LLM client configuration
    return {
        "base_url": settings.LLM_LOCAL_URL,
        "model": settings.LLM_MODEL,
        "provider": "local",
        "temperature": 0.7,
        "max_tokens": 4000,
        "timeout": 600,
    }

