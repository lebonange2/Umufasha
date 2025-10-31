"""Unit tests for MCP message types."""
import pytest
import json

from mcp.core.protocol.messages import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    JSONRPCErrorCode,
    parse_message,
    serialize_message
)


def test_jsonrpc_request_creation():
    """Test JSON-RPC request creation."""
    request = JSONRPCRequest(
        id=1,
        method="tools/list",
        params={}
    )
    
    assert request.jsonrpc == "2.0"
    assert request.id == 1
    assert request.method == "tools/list"
    assert request.params == {}


def test_jsonrpc_request_validation():
    """Test JSON-RPC request validation."""
    # Valid request
    request = JSONRPCRequest(id=1, method="tools/list")
    assert request.validate() is None
    
    # Invalid jsonrpc version
    request = JSONRPCRequest(jsonrpc="3.0", id=1, method="tools/list")
    error = request.validate()
    assert error is not None
    assert error.code == JSONRPCErrorCode.INVALID_REQUEST
    
    # Missing method
    request = JSONRPCRequest(id=1, method="")
    error = request.validate()
    assert error is not None
    assert error.code == JSONRPCErrorCode.INVALID_REQUEST


def test_jsonrpc_response():
    """Test JSON-RPC response."""
    # Success response
    response = JSONRPCResponse.success(1, {"result": "ok"})
    assert response.id == 1
    assert response.result == {"result": "ok"}
    assert response.error is None
    
    # Error response
    response = JSONRPCResponse.error_response(
        1,
        JSONRPCErrorCode.METHOD_NOT_FOUND,
        "Method not found"
    )
    assert response.id == 1
    assert response.result is None
    assert response.error is not None
    assert response.error.code == JSONRPCErrorCode.METHOD_NOT_FOUND


def test_parse_message():
    """Test message parsing."""
    # Request
    request_data = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
    message = parse_message(request_data)
    assert isinstance(message, JSONRPCRequest)
    assert message.id == 1
    assert message.method == "tools/list"
    
    # Notification
    notification_data = '{"jsonrpc":"2.0","method":"initialized"}'
    message = parse_message(notification_data)
    assert isinstance(message, JSONRPCNotification)
    assert message.method == "initialized"


def test_serialize_message():
    """Test message serialization."""
    request = JSONRPCRequest(id=1, method="tools/list")
    serialized = serialize_message(request)
    
    # Should be valid JSON
    parsed = json.loads(serialized)
    assert parsed["jsonrpc"] == "2.0"
    assert parsed["id"] == 1
    assert parsed["method"] == "tools/list"


def test_jsonrpc_error_codes():
    """Test JSON-RPC error codes."""
    assert JSONRPCErrorCode.PARSE_ERROR == -32700
    assert JSONRPCErrorCode.INVALID_REQUEST == -32600
    assert JSONRPCErrorCode.METHOD_NOT_FOUND == -32601
    assert JSONRPCErrorCode.INVALID_PARAMS == -32602
    assert JSONRPCErrorCode.INTERNAL_ERROR == -32603

