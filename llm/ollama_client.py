"""Ollama local LLM client for running models like Gemma, Llama, etc."""
from typing import List, Optional
from llm.base import LLMBackend, Message
from utils.logging import get_logger
import requests
import json

logger = get_logger('llm.ollama')


class OllamaClient(LLMBackend):
    """Ollama local LLM client."""
    
    def __init__(self, model: str = "gemma3:latest", base_url: str = "http://localhost:11434",
                 temperature: float = 0.7, max_tokens: int = 2000):
        """Initialize Ollama client.
        
        Args:
            model: Model name (e.g., "gemma2:2b", "llama3", "mistral")
            base_url: Ollama server URL
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(model, temperature, max_tokens)
        self.base_url = base_url.rstrip('/')
        self.model = model
        
        logger.info(f"Initialized Ollama client with model: {model}, URL: {base_url}")
        
        # Test connection
        try:
            self._test_connection()
        except Exception as e:
            logger.warning(f"Could not connect to Ollama: {e}")
    
    def _test_connection(self):
        """Test connection to Ollama server."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                logger.info(f"Connected to Ollama. Available models: {model_names}")
                
                if self.model not in model_names:
                    logger.warning(f"Model {self.model} not found. Available: {model_names}")
            else:
                logger.warning(f"Ollama server responded with status {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def chat(self, messages: List[Message]) -> Optional[str]:
        """Send chat messages to Ollama.
        
        Args:
            messages: List of Message objects
            
        Returns:
            Generated response text
        """
        try:
            # Workaround for models that don't handle system messages well
            # Merge system messages into the first user message
            merged_messages = []
            system_content = []
            
            for msg in messages:
                if msg.role == 'system':
                    system_content.append(msg.content)
                else:
                    # If we have system messages, prepend them to the first user message
                    if system_content and msg.role == 'user' and not merged_messages:
                        combined_content = "\n\n".join(system_content) + "\n\n" + msg.content
                        merged_messages.append({
                            'role': 'user',
                            'content': combined_content
                        })
                        system_content = []  # Clear after use
                    else:
                        merged_messages.append({
                            'role': msg.role,
                            'content': msg.content
                        })
            
            logger.debug(f"Sending {len(merged_messages)} messages to Ollama model: {self.model}")
            
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    'model': self.model,
                    'messages': merged_messages,
                    'stream': False,
                    'options': {
                        'temperature': self.temperature,
                        'num_predict': self.max_tokens
                    }
                },
                timeout=90  # Longer timeout for local inference
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('message', {}).get('content', '')
                logger.info(f"Ollama response received: {len(content)} characters")
                return content
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text[:200]}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "Ollama request timed out after 60 seconds"
            logger.error(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Ollama connection error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Ollama client error: {str(e)}"
            logger.error(error_msg)
            raise
    
    def simple_prompt(self, system: str, user: str) -> Optional[str]:
        """Simple prompt with system and user message.
        
        Args:
            system: System prompt
            user: User prompt
            
        Returns:
            Generated response
        """
        # Use generate API for better compatibility with all models
        # Combine system and user into a single prompt
        combined_prompt = f"{system}\n\n{user}"
        return self.generate(combined_prompt)
    
    def generate(self, prompt: str) -> Optional[str]:
        """Generate completion for a prompt (non-chat mode).
        
        Args:
            prompt: Text prompt
            
        Returns:
            Generated text
        """
        try:
            logger.info(f"Generating completion with prompt length: {len(prompt)}")
            
            # Use a fresh session to avoid connection issues
            with requests.Session() as session:
                session.mount('http://', requests.adapters.HTTPAdapter(
                    max_retries=0,
                    pool_connections=1,
                    pool_maxsize=1
                ))
                
                response = session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        'model': self.model,
                        'prompt': prompt,
                        'stream': False,
                        'options': {
                            'temperature': self.temperature,
                            'num_predict': self.max_tokens
                        }
                    },
                    timeout=(10, 120),  # (connect timeout, read timeout)
                    headers={'Connection': 'close'}
                )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '')
                logger.info(f"Generated: {len(content)} characters")
                return content
            else:
                error_msg = f"Ollama generate error: {response.status_code} - {response.text[:200]}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "Ollama generate timed out after 120 seconds"
            logger.error(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Ollama generate connection error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Ollama generate error: {str(e)}"
            logger.error(error_msg)
            raise
