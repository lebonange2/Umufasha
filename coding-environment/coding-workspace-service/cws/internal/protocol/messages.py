"""JSON-RPC message types for CWS."""
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
    
    # CWS-specific error codes
    PATH_TRAVERSAL = -32001
    POLICY_VIOLATION = -32002
    FILE_TOO_LARGE = -32003
    OPERATION_DENIED = -32004
    CONFIRMATION_REQUIRED = -32005


@dataclass
class JSONRPCError:
    """JSON-RPC error object."""
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 request."""
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": self.method
        }
        if self.params is not None:
            result["params"] = self.params
        return result


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 response."""
    id: Union[str, int]
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.error:
            result["error"] = self.error.to_dict()
        else:
            result["result"] = self.result
        return result


@dataclass
class JSONRPCNotification:
    """JSON-RPC 2.0 notification."""
    method: str
    params: Optional[Dict[str, Any]] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method
        }
        if self.params is not None:
            result["params"] = self.params
        return result


def parse_message(data: str) -> Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]:
    """Parse JSON-RPC message from string."""
    try:
        obj = json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    
    if not isinstance(obj, dict):
        raise ValueError("Message must be an object")
    
    if "jsonrpc" not in obj or obj["jsonrpc"] != "2.0":
        raise ValueError("Invalid jsonrpc version")
    
    if "method" in obj:
        # Request or notification
        if "id" in obj:
            return JSONRPCRequest(
                id=obj["id"],
                method=obj["method"],
                params=obj.get("params")
            )
        else:
            return JSONRPCNotification(
                method=obj["method"],
                params=obj.get("params")
            )
    elif "id" in obj:
        # Response
        error = None
        if "error" in obj:
            error = JSONRPCError(
                code=obj["error"]["code"],
                message=obj["error"]["message"],
                data=obj["error"].get("data")
            )
        
        return JSONRPCResponse(
            id=obj["id"],
            result=obj.get("result"),
            error=error
        )
    else:
        raise ValueError("Invalid message format")


def serialize_message(message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]) -> str:
    """Serialize JSON-RPC message to string."""
    if isinstance(message, JSONRPCRequest):
        return json.dumps(message.to_dict())
    elif isinstance(message, JSONRPCResponse):
        return json.dumps(message.to_dict())
    elif isinstance(message, JSONRPCNotification):
        return json.dumps(message.to_dict())
    else:
        raise ValueError(f"Unknown message type: {type(message)}")

