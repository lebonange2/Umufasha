"""Base tool interface."""
from typing import Dict, Any, Optional, Callable
from abc import ABC, abstractmethod

from mcp.core.concurrency import CancellationToken


class Tool(ABC):
    """Base interface for MCP tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON Schema for input parameters."""
        pass
    
    @abstractmethod
    async def execute(
        self,
        params: Dict[str, Any],
        cancellation_token: Optional[CancellationToken] = None
    ) -> Dict[str, Any]:
        """Execute the tool.
        
        Args:
            params: Input parameters
            cancellation_token: Optional cancellation token
            
        Returns:
            Tool result
        """
        pass
    
    def get_definition(self) -> Dict[str, Any]:
        """Get tool definition for introspection."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


class FunctionTool(Tool):
    """Tool wrapper for async functions."""
    
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[[Dict[str, Any], Optional[CancellationToken]], Any]
    ):
        """Initialize function tool.
        
        Args:
            name: Tool name
            description: Tool description
            input_schema: JSON Schema for input
            handler: Async handler function
        """
        self._name = name
        self._description = description
        self._input_schema = input_schema
        self._handler = handler
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return self._input_schema
    
    async def execute(
        self,
        params: Dict[str, Any],
        cancellation_token: Optional[CancellationToken] = None
    ) -> Dict[str, Any]:
        """Execute the tool."""
        if cancellation_token:
            cancellation_token.check()
        
        result = await self._handler(params, cancellation_token)
        
        if isinstance(result, dict):
            return result
        return {"result": result}

