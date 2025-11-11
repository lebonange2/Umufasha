"""OpenAI ChatGPT backend for Cursor-AI Clone."""
import asyncio
import os
from typing import Optional, AsyncIterator, Dict, Any
import structlog
import httpx

from mcp.plugins.cursor_clone.llm.engine import LLMEngine

logger = structlog.get_logger(__name__)


class OpenAIClient(LLMEngine):
    """OpenAI ChatGPT engine using OpenAI API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI client."""
        super().__init__(config)
        # Get API key from environment variable (automatically)
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = config.get("model", "gpt-4o-mini")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self._client = None
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY environment variable not set, OpenAI client will not work")
            logger.info("Set it with: export OPENAI_API_KEY=your-api-key")
        else:
            logger.info("OpenAI API key found in environment variable", model=self.model)
    
    async def load(self) -> bool:
        """Load the model (no-op for API-based model)."""
        if not self.api_key:
            logger.error("OPENAI_API_KEY not set")
            return False
        
        # Create HTTP client
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
        
        self._loaded = True
        logger.info("OpenAI client initialized", model=self.model)
        return True
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> str:
        """Generate text from prompt using OpenAI API."""
        if not self._loaded:
            await self.load()
        
        if not self._client:
            return "Error: OpenAI client not initialized"
        
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request
        request_data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": self.top_p,
        }
        
        if stream:
            # For streaming, collect tokens
            response_text = ""
            async with self._client.stream(
                "POST",
                "/chat/completions",
                json=request_data
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            import json
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    response_text += delta["content"]
                        except json.JSONDecodeError:
                            continue
            return response_text
        else:
            # Non-streaming
            try:
                response = await self._client.post(
                    "/chat/completions",
                    json=request_data
                )
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error("Unexpected response format", data=data)
                    return "Error: Unexpected response format"
            except httpx.HTTPStatusError as e:
                logger.error("OpenAI API error", status_code=e.response.status_code, error=str(e))
                return f"Error: OpenAI API error ({e.response.status_code})"
            except Exception as e:
                logger.error("Error calling OpenAI API", error=str(e), exc_info=True)
                return f"Error: {str(e)}"
    
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncIterator[str]:
        """Stream tokens from prompt using OpenAI API."""
        if not self._loaded:
            await self.load()
        
        if not self._client:
            yield "Error: OpenAI client not initialized"
            return
        
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request
        request_data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": self.top_p,
            "stream": True
        }
        
        try:
            async with self._client.stream(
                "POST",
                "/chat/completions",
                json=request_data
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            import json
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error("Error streaming from OpenAI API", error=str(e), exc_info=True)
            yield f"Error: {str(e)}"
    
    async def unload(self):
        """Unload the model (close HTTP client)."""
        if self._client:
            await self._client.aclose()
            self._client = None
        
        self._loaded = False
        logger.info("OpenAI client unloaded")

