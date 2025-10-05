"""Generic HTTP LLM client for self-hosted models."""
from typing import List, Optional, Dict, Any
import httpx
from llm.base import LLMBackend, Message
from utils.logging import get_logger

logger = get_logger('llm.http')


class HTTPClient(LLMBackend):
    """Generic HTTP LLM client compatible with OpenAI API format."""
    
    def __init__(self, url: str, model: str = "local-model",
                 temperature: float = 0.7, max_tokens: int = 1000,
                 api_key: Optional[str] = None, timeout: float = 60.0):
        """Initialize HTTP client.
        
        Args:
            url: API endpoint URL
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        super().__init__(model, temperature, max_tokens)
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        
        logger.info(f"HTTP LLM client initialized: url={url}, model={model}")
    
    def is_available(self) -> bool:
        """Check if backend is available."""
        try:
            # Try a simple health check
            with httpx.Client(timeout=5.0) as client:
                # Try to reach the base URL
                response = client.get(self.url.rsplit('/', 1)[0])
                return response.status_code < 500
        except Exception as e:
            logger.warning(f"HTTP backend not reachable: {e}")
            return False
    
    def chat(self, messages: List[Message], **kwargs) -> Optional[str]:
        """Send chat messages and get response.
        
        Args:
            messages: List of messages
            **kwargs: Additional parameters
            
        Returns:
            Assistant response text or None
        """
        try:
            # Convert messages to dict format
            message_dicts = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Prepare request payload (OpenAI-compatible format)
            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": message_dicts,
                "temperature": kwargs.get('temperature', self.temperature),
                "max_tokens": kwargs.get('max_tokens', self.max_tokens)
            }
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Make request
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                # Parse response (OpenAI-compatible format)
                data = response.json()
                
                # Try to extract text from various response formats
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if "message" in choice:
                        text = choice["message"].get("content", "")
                    elif "text" in choice:
                        text = choice["text"]
                    else:
                        text = str(choice)
                elif "response" in data:
                    text = data["response"]
                elif "text" in data:
                    text = data["text"]
                else:
                    logger.error(f"Unexpected response format: {data}")
                    return None
                
                if text:
                    logger.info(f"LLM response: {len(text)} chars")
                    return text.strip()
                else:
                    logger.warning("Empty response from LLM")
                    return None
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            return None
