"""Configuration for the book generation system."""
from typing import Dict
from app.core.config import settings


def get_config() -> Dict:
    """Get the configuration for the agents."""
    # Use the existing LLM client configuration
    # Note: No timeout - phases run until completion or user cancellation
    return {
        "base_url": settings.LLM_LOCAL_URL,
        "model": settings.LLM_MODEL,
        "provider": "local",
        "temperature": 0.7,
        "max_tokens": 4000,
    }

