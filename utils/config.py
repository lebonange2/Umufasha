"""Configuration management for the brainstorming assistant."""
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv


class Config:
    """Central configuration manager."""
    
    def __init__(self, project_name: Optional[str] = None, config_path: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            project_name: Name of the project/session
            config_path: Path to custom config.yaml (defaults to ./config.yaml)
        """
        # Load environment variables
        load_dotenv()
        
        # Load YAML config
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        
        self.project_name = project_name or "default"
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value using dot notation (e.g., 'audio.sample_rate')."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a config value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to YAML file."""
        path = path or self.config_path
        with open(path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
    
    # Environment variable accessors
    @property
    def openai_api_key(self) -> str:
        return os.getenv('OPENAI_API_KEY', '')
    
    @property
    def openai_base(self) -> str:
        return os.getenv('OPENAI_BASE', 'https://api.openai.com/v1')
    
    @property
    def openai_model(self) -> str:
        return os.getenv('OPENAI_MODEL', self.get('llm.model', 'gpt-4-turbo-preview'))
    
    @property
    def llm_backend(self) -> str:
        return os.getenv('LLM_BACKEND', self.get('llm.backend', 'openai'))
    
    @property
    def llm_http_url(self) -> str:
        return os.getenv('LLM_HTTP_URL', self.get('llm.http_url', 'http://localhost:8000/v1/chat/completions'))
    
    @property
    def llm_http_model(self) -> str:
        return os.getenv('LLM_HTTP_MODEL', self.get('llm.http_model', 'local-model'))
    
    @property
    def stt_backend(self) -> str:
        return os.getenv('STT_BACKEND', self.get('stt.backend', 'whisper_local'))
    
    @property
    def whisper_model_size(self) -> str:
        return os.getenv('WHISPER_MODEL_SIZE', self.get('stt.whisper_model', 'base'))
    
    @property
    def vosk_model_path(self) -> str:
        return os.getenv('VOSK_MODEL_PATH', self.get('stt.vosk_model_path', 'models/vosk-model-small-en-us-0.15'))
    
    @property
    def sample_rate(self) -> int:
        return int(os.getenv('SAMPLE_RATE', self.get('audio.sample_rate', 16000)))
    
    @property
    def vad_enabled(self) -> bool:
        vad_str = os.getenv('VAD', str(self.get('audio.vad_enabled', True)))
        return vad_str.lower() in ('true', '1', 'yes')
    
    @property
    def autosave_interval(self) -> int:
        return int(os.getenv('AUTOSAVE_INTERVAL', self.get('storage.autosave_interval', 30)))
    
    @property
    def dedupe_threshold(self) -> float:
        return float(os.getenv('DEDUPE_THRESHOLD', self.get('brainstorm.dedupe_threshold', 0.85)))
    
    @property
    def storage_base_dir(self) -> Path:
        base = self.get('storage.base_dir', 'brainstorm')
        return Path(base) / self.project_name
    
    def __repr__(self) -> str:
        return f"Config(project={self.project_name}, llm={self.llm_backend}, stt={self.stt_backend})"
