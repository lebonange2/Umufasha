"""Base class for LLM backends."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """Chat message."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMBackend(ABC):
    """Abstract base class for LLM backends."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 1000):
        """Initialize LLM backend.
        
        Args:
            model: Model name/identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    def chat(self, messages: List[Message], **kwargs) -> Optional[str]:
        """Send chat messages and get response.
        
        Args:
            messages: List of messages
            **kwargs: Additional parameters
            
        Returns:
            Assistant response text or None if failed
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available.
        
        Returns:
            True if backend is ready to use
        """
        pass
    
    def simple_prompt(self, system: str, user: str, **kwargs) -> Optional[str]:
        """Simple prompt with system and user messages.
        
        Args:
            system: System message
            user: User message
            **kwargs: Additional parameters
            
        Returns:
            Assistant response
        """
        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user)
        ]
        return self.chat(messages, **kwargs)
