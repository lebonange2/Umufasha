"""Configuration for the book generation system."""
import os
from typing import Dict
from app.core.config import settings


def get_config() -> Dict:
    """Get the configuration for the agents."""
    # Determine provider and configuration based on settings
    provider = settings.LLM_PROVIDER.lower()
    
    config = {
        "provider": provider,
        "temperature": 0.7,
        "max_tokens": 4000,
        "use_mock_llm": settings.USE_MOCK_LLM,  # For testing
    }
    
    if provider == "openai":
        # OpenAI configuration
        config["base_url"] = "https://api.openai.com/v1"
        config["model"] = getattr(settings, "OPENAI_MODEL", "gpt-4o")
        # Read API key directly from environment variable
        config["api_key"] = os.environ.get("OPENAI_API_KEY")
        if not config["api_key"]:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required when LLM_PROVIDER=openai. "
                "Set it as an environment variable: export OPENAI_API_KEY=your-key"
            )
    else:
        # Local (Ollama) configuration
        config["base_url"] = settings.LLM_LOCAL_URL
        config["model"] = settings.LLM_MODEL
        config["api_key"] = None  # No API key needed for local models
    
    return config

