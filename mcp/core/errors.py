"""MCP error handling."""
from typing import Optional, Dict, Any
from dataclasses import dataclass

from mcp.core.protocol.messages import JSONRPCError, JSONRPCErrorCode


class MCPServerError(Exception):
    """Base exception for MCP server errors."""
    def __init__(
        self,
        message: str,
        code: int = JSONRPCErrorCode.INTERNAL_ERROR,
        data: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.data = data or {}
        super().__init__(message)
    
    def to_jsonrpc_error(self) -> JSONRPCError:
        """Convert to JSON-RPC error."""
        return JSONRPCError(
            code=self.code,
            message=self.message,
            data=self.data
        )


class MCPValidationError(MCPServerError):
    """Validation error."""
    def __init__(self, message: str, path: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=JSONRPCErrorCode.INVALID_PARAMS,
            data={**(data or {}), "path": path}
        )


class MCPMethodNotFoundError(MCPServerError):
    """Method not found error."""
    def __init__(self, method: str):
        super().__init__(
            message=f"Method not found: {method}",
            code=JSONRPCErrorCode.METHOD_NOT_FOUND,
            data={"method": method}
        )


class MCPResourceNotFoundError(MCPServerError):
    """Resource not found error."""
    def __init__(self, uri: str):
        super().__init__(
            message=f"Resource not found: {uri}",
            code=JSONRPCErrorCode.RESOURCE_NOT_FOUND,
            data={"uri": uri}
        )


class MCPToolExecutionError(MCPServerError):
    """Tool execution error."""
    def __init__(self, tool: str, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Tool execution failed: {message}",
            code=JSONRPCErrorCode.TOOL_EXECUTION_FAILED,
            data={**(data or {}), "tool": tool}
        )


class MCPTimeoutError(MCPServerError):
    """Timeout error."""
    def __init__(self, method: str, timeout_seconds: float):
        super().__init__(
            message=f"Request timed out after {timeout_seconds}s",
            code=JSONRPCErrorCode.TIMEOUT,
            data={"method": method, "timeout": timeout_seconds}
        )


class MCPCancelledError(MCPServerError):
    """Cancellation error."""
    def __init__(self, request_id: str):
        super().__init__(
            message="Request was cancelled",
            code=JSONRPCErrorCode.CANCELLED,
            data={"request_id": request_id}
        )

