"""Base resource interface."""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class Resource(ABC):
    """Base interface for MCP resources."""
    
    @property
    @abstractmethod
    def uri(self) -> str:
        """Resource URI pattern."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Resource name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Resource description."""
        pass
    
    @abstractmethod
    async def read(
        self,
        uri: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Read resource content.
        
        Args:
            uri: Resource URI
            offset: Optional byte offset
            limit: Optional byte limit
            
        Returns:
            Resource content with metadata
        """
        pass
    
    def get_definition(self) -> Dict[str, Any]:
        """Get resource definition for introspection."""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description
        }

