"""OpenAI LLM client."""
from typing import List, Optional
from llm.base import LLMBackend, Message
from utils.logging import get_logger

logger = get_logger('llm.openai')


class OpenAIClient(LLMBackend):
    """OpenAI API client."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview",
                 temperature: float = 0.7, max_tokens: int = 1000,
                 base_url: Optional[str] = None):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            base_url: Optional custom base URL
        """
        super().__init__(model, temperature, max_tokens)
        self.api_key = api_key
        self.base_url = base_url
        self.client = None
        
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            
            self.client = OpenAI(**kwargs)
            logger.info(f"OpenAI client initialized: model={self.model}")
            
        except ImportError:
            logger.error("openai package not installed")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if backend is available."""
        return self.client is not None and bool(self.api_key)
    
    def chat(self, messages: List[Message], **kwargs) -> Optional[str]:
        """Send chat messages and get response.
        
        Args:
            messages: List of messages
            **kwargs: Additional parameters
            
        Returns:
            Assistant response text or None
        """
        if not self.is_available():
            logger.error("OpenAI client not available")
            return None
        
        try:
            # Convert messages to dict format
            message_dicts = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message_dicts,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens)
            )
            
            # Extract response text
            text = response.choices[0].message.content
            
            if text:
                logger.info(f"LLM response: {len(text)} chars")
                return text.strip()
            else:
                logger.warning("Empty response from LLM")
                return None
                
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            return None
