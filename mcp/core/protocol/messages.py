"""MCP message types and validation."""
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid


class JSONRPCErrorCode(int, Enum):
    """JSON-RPC 2.0 error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR = -32000
    
    # MCP-specific error codes
    CAPABILITY_NOT_SUPPORTED = -32001
    RESOURCE_NOT_FOUND = -32002
    TOOL_EXECUTION_FAILED = -32003
    TIMEOUT = -32004
    CANCELLED = -32005


@dataclass
class JSONRPCError:
    """JSON-RPC error object."""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 request."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JSONRPCRequest":
        """Create from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method", ""),
            params=data.get("params")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method
        }
        if self.id is not None:
            result["id"] = self.id
        if self.params is not None:
            result["params"] = self.params
        return result
    
    def validate(self) -> Optional[JSONRPCError]:
        """Validate request structure."""
        if self.jsonrpc != "2.0":
            return JSONRPCError(
                code=JSONRPCErrorCode.INVALID_REQUEST,
                message="Invalid jsonrpc version"
            )
        if not self.method:
            return JSONRPCError(
                code=JSONRPCErrorCode.INVALID_REQUEST,
                message="Method is required"
            )
        return None


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 response."""
    id: Union[str, int]
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.error is not None:
            result["error"] = self.error.to_dict()
        elif self.result is not None:
            result["result"] = self.result
        else:
            result["result"] = None
        return result
    
    @classmethod
    def success(cls, request_id: Union[str, int], result: Any) -> "JSONRPCResponse":
        """Create success response."""
        return cls(id=request_id, result=result)
    
    @classmethod
    def error_response(
        cls,
        request_id: Optional[Union[str, int]],
        code: int,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> "JSONRPCResponse":
        """Create error response."""
        return cls(
            id=request_id if request_id is not None else str(uuid.uuid4()),
            error=JSONRPCError(code=code, message=message, data=data)
        )


@dataclass
class JSONRPCNotification:
    """JSON-RPC 2.0 notification (no response)."""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JSONRPCNotification":
        """Create from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data.get("method", ""),
            params=data.get("params")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method
        }
        if self.params is not None:
            result["params"] = self.params
        return result
    
    def validate(self) -> Optional[JSONRPCError]:
        """Validate notification structure."""
        if self.jsonrpc != "2.0":
            return JSONRPCError(
                code=JSONRPCErrorCode.INVALID_REQUEST,
                message="Invalid jsonrpc version"
            )
        if not self.method:
            return JSONRPCError(
                code=JSONRPCErrorCode.INVALID_REQUEST,
                message="Method is required"
            )
        return None


def parse_message(data: str) -> Union[JSONRPCRequest, JSONRPCNotification]:
    """Parse JSON-RPC message from string."""
    try:
        obj = json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    
    if not isinstance(obj, dict):
        raise ValueError("Message must be a JSON object")
    
    # Check if it's a request (has id) or notification (no id)
    if "id" in obj:
        return JSONRPCRequest.from_dict(obj)
    else:
        return JSONRPCNotification.from_dict(obj)


def serialize_message(message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]) -> str:
    """Serialize message to JSON string."""
    if isinstance(message, JSONRPCRequest):
        return json.dumps(message.to_dict())
    elif isinstance(message, JSONRPCResponse):
        return json.dumps(message.to_dict())
    elif isinstance(message, JSONRPCNotification):
        return json.dumps(message.to_dict())
    else:
        raise ValueError(f"Unknown message type: {type(message)}")

