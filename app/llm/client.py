"""LLM client for policy decisions and content generation."""
import json
from typing import Dict, Any, Optional, List, AsyncIterator
import httpx
import structlog

logger = structlog.get_logger(__name__)


class LLMClient:
    """Generic LLM client that can work with OpenAI, Claude (Anthropic), or other HTTP endpoints."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "gpt-4o", provider: str = "openai"):
        self.api_key = api_key
        self.provider = provider.lower()  # openai, anthropic, or custom
        if provider.lower() == "anthropic":
            self.base_url = base_url or "https://api.anthropic.com/v1"
        else:
            self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def complete(self, system: str, user: str, tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """Complete a conversation with the LLM.
        
        Args:
            system: System prompt
            user: User message
            tools: Optional tools/function definitions
            
        Returns:
            LLM response text
        """
        try:
            if self.provider == "anthropic":
                # Claude API format
                payload = {
                    "model": self.model,
                    "max_tokens": 2000,
                    "system": system,
                    "messages": [
                        {"role": "user", "content": user}
                    ]
                }
                
                if not self.api_key:
                    raise ValueError("ANTHROPIC_API_KEY is required but not set")
                
                headers = {
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                }
                
                response = await self.client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                # Claude returns content in a different format
                if "content" in result and len(result["content"]) > 0:
                    content_block = result["content"][0]
                    if isinstance(content_block, dict) and "text" in content_block:
                        content = content_block["text"]
                    else:
                        content = str(content_block)
                else:
                    content = ""
                
                logger.info("Claude completion successful", model=self.model)
                return content
            else:
                # OpenAI-compatible format
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ]
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
                
                if tools:
                    payload["tools"] = tools
                
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                logger.info("LLM completion successful", model=self.model, tokens=result.get("usage", {}).get("total_tokens"))
                return content
            
        except Exception as e:
            logger.error("LLM completion failed", error=str(e), model=self.model, provider=self.provider)
            raise
    
    async def complete_json(self, system: str, user: str) -> Dict[str, Any]:
        """Complete a conversation and parse JSON response.
        
        Args:
            system: System prompt
            user: User message
            
        Returns:
            Parsed JSON response
        """
        response = await self.complete(system, user)
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON response", error=str(e), response=response)
            raise ValueError(f"Invalid JSON response from LLM: {e}")
    
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncIterator[str]:
        """Stream tokens from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Yields:
            Token strings as they are generated
        """
        try:
            if self.provider == "anthropic":
                # Claude API streaming format
                payload = {
                    "model": self.model,
                    "max_tokens": max_tokens or 2000,
                    "system": system_prompt or "",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": True
                }
                
                if not self.api_key:
                    raise ValueError("ANTHROPIC_API_KEY is required but not set")
                
                headers = {
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                }
                
                async with self.client.stream(
                    "POST",
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                # Claude streaming format
                                if "type" in data:
                                    if data["type"] == "content_block_delta" and "delta" in data:
                                        if "text" in data["delta"]:
                                            yield data["delta"]["text"]
                                    elif data["type"] == "message_delta" and "delta" in data:
                                        if "stop_reason" in data["delta"]:
                                            break
                            except json.JSONDecodeError:
                                continue
                            except KeyError:
                                continue
            else:
                # OpenAI-compatible streaming format
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature or 0.7,
                    "max_tokens": max_tokens or 2000,
                    "stream": True
                }
                
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                async with self.client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
                            except KeyError:
                                continue
        
        except Exception as e:
            logger.error("LLM streaming failed", error=str(e), model=self.model, provider=self.provider)
            yield f"Error: {str(e)}"
    
    async def is_available(self) -> bool:
        """Check if the LLM service is available."""
        try:
            await self.complete("You are a helpful assistant.", "Say 'OK' if you can respond.")
            return True
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
