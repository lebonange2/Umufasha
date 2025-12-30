"""Application configuration."""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = "postgresql://assistant:assistant@db:5432/assistant"
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Neo4j Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4jpassword"
    
    # LLM - Local models only (Ollama)
    LLM_MODEL: str = "gemma2:2b"  # Default local model (small, fast, low memory)
    LLM_PROVIDER: str = "local"  # Always local (Ollama) - no API keys needed
    LLM_LOCAL_URL: str = "http://localhost:11434/v1"  # Ollama default URL
    # Legacy fields (deprecated, not used - kept for backwards compatibility)
    OPENAI_API_KEY: Optional[str] = None  # Deprecated - not used
    ANTHROPIC_API_KEY: Optional[str] = None  # Deprecated - not used
    LLM_BASE_URL: Optional[str] = None  # Deprecated - not used
    
    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_CALLER_ID: Optional[str] = None
    
    # Email
    SENDGRID_API_KEY: Optional[str] = None
    GMAIL_CLIENT_ID: Optional[str] = None
    GMAIL_CLIENT_SECRET: Optional[str] = None
    
    # Google Calendar
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Security
    OAUTH_ENC_KEY: str = "base64:your-32-byte-key-here"
    SECRET_KEY: str = "your-secret-key-here"
    
    # Scheduler
    SCHEDULER: str = "apscheduler"  # apscheduler or celery
    
    # Base URL for webhooks
    BASE_URL: str = "http://localhost:8000"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_TOTP_SECRET: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Testing/Mock mode
    MOCK_MODE: bool = False
    MOCK_TWILIO: bool = False
    MOCK_SENDGRID: bool = False
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Allow reading from environment variables (takes precedence over .env file)
        # This is the default behavior of pydantic-settings


settings = Settings()