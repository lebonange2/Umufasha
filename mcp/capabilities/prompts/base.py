"""Base prompt interface."""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class Prompt(ABC):
    """Base interface for MCP prompts."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Prompt name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Prompt description."""
        pass
    
    @property
    @abstractmethod
    def arguments(self) -> List[Dict[str, Any]]:
        """Prompt argument schema."""
        pass
    
    @abstractmethod
    async def render(
        self,
        arguments: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Render prompt with arguments.
        
        Args:
            arguments: Argument values
            
        Returns:
            List of prompt messages (typically one system + one user message)
        """
        pass
    
    def get_definition(self) -> Dict[str, Any]:
        """Get prompt definition for introspection."""
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments
        }

