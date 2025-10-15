"""LLM client for policy decisions and content generation."""
import json
from typing import Dict, Any, Optional, List
import httpx
import structlog

logger = structlog.get_logger(__name__)


class LLMClient:
    """Generic LLM client that can work with OpenAI or other HTTP endpoints."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key
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
            logger.error("LLM completion failed", error=str(e), model=self.model)
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
