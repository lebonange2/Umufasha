"""Logging utilities with key redaction."""
import logging
import re
from pathlib import Path
from typing import Optional


class RedactingFormatter(logging.Formatter):
    """Formatter that redacts sensitive information."""
    
    PATTERNS = [
        (re.compile(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^"\'}\s]+)', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(bearer\s+)([a-zA-Z0-9\-._~+/]+)', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(sk-[a-zA-Z0-9]{20,})', re.IGNORECASE), r'***REDACTED***'),
    ]
    
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        
        # Redact sensitive patterns
        result = original
        for pattern, replacement in self.PATTERNS:
            result = pattern.sub(replacement, result)
        
        return result


def setup_logging(log_dir: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """Setup application logging with redaction.
    
    Args:
        log_dir: Directory for log files (None = logs to console only)
        level: Logging level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger('brainstorm')
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = RedactingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_dir provided)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / 'brainstorm.log')
        file_handler.setLevel(level)
        file_formatter = RedactingFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f'brainstorm.{name}')
