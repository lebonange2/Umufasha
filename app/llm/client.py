"""LLM client for policy decisions and content generation."""
import json
from typing import Dict, Any, Optional, List, AsyncIterator
import httpx

# Try to import structlog, fallback to standard logging if not available
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class LLMClient:
    """Generic LLM client that can work with OpenAI, Claude (Anthropic), or other HTTP endpoints."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "qwen3:30b", provider: str = "local"):
        self.api_key = api_key
        self.provider = provider.lower()  # local, openai, anthropic, or custom
        if provider.lower() == "anthropic":
            self.base_url = base_url or "https://api.anthropic.com/v1"
        elif provider.lower() == "local":
            # Ollama uses OpenAI-compatible API at /v1
            self.base_url = base_url or "http://localhost:11434/v1"
            # Use model name directly (must be valid Ollama model name like llama3:latest)
            self.model = model
        else:
            self.base_url = base_url or "https://api.openai.com/v1"
            self.model = model
        # Initialize httpx client with proper settings and connection pooling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
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
                
                # Local provider doesn't need API keys - skip validation
                if self.provider != "local" and not self.api_key:
                    raise ValueError("API key required for cloud providers")
                
                headers = {
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                }
                
                # Log the request for debugging (without sensitive data)
                logger.debug("Making Anthropic API request", 
                           url=f"{self.base_url}/messages",
                           model=self.model,
                           has_api_key=bool(self.api_key))
                
                # Make request with retry logic for first attempt
                max_retries = 2
                last_error = None
                for attempt in range(max_retries):
                    try:
                        response = await self.client.post(
                            f"{self.base_url}/messages",
                            json=payload,
                            headers=headers
                        )
                        response.raise_for_status()
                        break  # Success, exit retry loop
                    except httpx.HTTPStatusError as e:
                        last_error = e
                        if e.response.status_code == 404:
                            # 404 might be a transient issue or wrong endpoint
                            logger.warning(f"Anthropic API 404 error on attempt {attempt + 1}", 
                                         status_code=e.response.status_code,
                                         response_text=e.response.text[:200] if e.response.text else None)
                            if attempt < max_retries - 1:
                                # Wait a bit before retry
                                import asyncio
                                await asyncio.sleep(0.5 * (attempt + 1))
                                continue
                        raise  # Re-raise if not 404 or last attempt
                    except httpx.RequestError as e:
                        last_error = e
                        logger.warning(f"Anthropic API request error on attempt {attempt + 1}", error=str(e))
                        if attempt < max_retries - 1:
                            import asyncio
                            await asyncio.sleep(0.5 * (attempt + 1))
                            continue
                        raise
                
                if last_error:
                    raise last_error
                
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
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Client error '{e.response.status_code} {e.response.reason_phrase}' for url '{e.request.url}'"
            if e.response.text:
                try:
                    error_data = e.response.json()
                    if "error" in error_data:
                        error_msg += f"\n{error_data['error'].get('message', '')}"
                except:
                    error_msg += f"\n{e.response.text[:500]}"
            error_msg += f"\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/{e.response.status_code}"
            logger.error("LLM HTTP error", 
                        status_code=e.response.status_code,
                        url=str(e.request.url),
                        provider=self.provider,
                        model=self.model)
            raise Exception(error_msg) from e
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error("LLM request error", error=str(e), provider=self.provider, model=self.model)
            raise Exception(error_msg) from e
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
                
                # Local provider doesn't need API keys
                if self.provider != "local" and not self.api_key:
                    raise ValueError("API key required for cloud providers")
                
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
