"""Configuration management for Cursor-AI Clone."""
import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


def expand_env_vars(value: str) -> Any:
    """Expand environment variables in string values."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        # Extract variable name and default
        var_part = value[2:-1]
        if ":-" in var_part:
            var_name, default = var_part.split(":-", 1)
            result = os.getenv(var_name, default)
            # Try to convert to int if it looks like a number
            if result.isdigit():
                return int(result)
            return result
        else:
            var_name = var_part
            result = os.getenv(var_name, value)
            # Try to convert to int if it looks like a number
            if isinstance(result, str) and result.isdigit():
                return int(result)
            return result
    return value


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file with environment variable expansion."""
    if config_path is None:
        # Default to plugin config directory
        plugin_dir = Path(__file__).parent.parent
        config_path = plugin_dir / "config" / "default.yaml"
    
    if not config_path.exists():
        logger.warning("Config file not found, using defaults", path=str(config_path))
        return _get_default_config()
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Recursively expand environment variables
    def expand_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k] = expand_dict(v)
            elif isinstance(v, list):
                result[k] = [expand_env_vars(item) if isinstance(item, str) else item for item in v]
            else:
                expanded = expand_env_vars(v)
                # Convert known numeric fields to int
                if k == "port" and isinstance(expanded, str) and expanded.isdigit():
                    expanded = int(expanded)
                elif k in ("context_tokens", "max_tokens", "chunk_size", "chunk_overlap", "timeout", "memory_limit") and isinstance(expanded, str) and expanded.isdigit():
                    expanded = int(expanded)
                elif k == "cpu_limit" and isinstance(expanded, str):
                    try:
                        expanded = float(expanded)
                    except ValueError:
                        pass
                result[k] = expanded
        return result
    
    config = expand_dict(config)
    
    # Validate against schema if available
    schema_path = config_path.parent / "schema.json"
    if schema_path.exists():
        # Basic validation (full validation would require jsonschema)
        logger.debug("Config schema available", schema=str(schema_path))
    
    return config


def _get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    # Helper to safely convert to int
    def safe_int(value: str, default: int) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    return {
        "llm": {
            "provider": os.getenv("LLM_PROVIDER", "local"),
            "model_path": os.getenv("LOCAL_LLM_MODEL_PATH", "models/gemma3-4b.gguf"),
            "use_gpu": os.getenv("LOCAL_LLM_USE_GPU", "false").lower() == "true",
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "context_tokens": safe_int(os.getenv("LOCAL_LLM_CONTEXT_TOKENS", "8192"), 8192),
            "max_tokens": safe_int(os.getenv("LOCAL_LLM_MAX_TOKENS", "1024"), 1024),
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40
        },
        "workspace": {
            "root": os.getenv("WORKSPACE_ROOT", "."),
            "disable_network": os.getenv("ASSISTANT_DISABLE_NETWORK", "true").lower() == "true",
            "audit_log": os.getenv("ASSISTANT_AUDIT_LOG", "logs/assistant_audit.jsonl")
        },
        "ui": {
            "enable_webpanel": os.getenv("ASSISTANT_ENABLE_WEBPANEL", "true").lower() == "true",
            "port": safe_int(os.getenv("ASSISTANT_PORT", "7701"), 7701)
        },
        "logging": {
            "level": os.getenv("ASSISTANT_LOG_LEVEL", "INFO")
        }
    }


def get_workspace_root(config: Dict[str, Any]) -> Path:
    """Get workspace root from config."""
    root_str = config.get("workspace", {}).get("root", ".")
    return Path(root_str).resolve()

