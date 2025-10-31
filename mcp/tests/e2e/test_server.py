"""End-to-end tests for MCP server."""
import pytest
import asyncio
import json
from typing import Dict, Any

from mcp.core.protocol.messages import JSONRPCRequest, parse_message, serialize_message


@pytest.mark.asyncio
async def test_initialize_handshake():
    """Test initialize handshake."""
    from mcp.server import MCPServer
    
    server = MCPServer(transport_type="stdio", max_concurrent=1)
    
    # Create initialize request
    request = JSONRPCRequest(
        id=1,
        method="initialize",
        params={
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    )
    
    # Handle request
    response = await server.router.handle_request(request)
    
    assert response.id == 1
    assert response.error is None
    assert response.result is not None
    assert response.result["protocolVersion"] == "2024-11-05"
    assert "capabilities" in response.result
    assert "serverInfo" in response.result


@pytest.mark.asyncio
async def test_tools_list():
    """Test tools/list method."""
    from mcp.server import MCPServer
    
    server = MCPServer(transport_type="stdio")
    
    request = JSONRPCRequest(
        id=2,
        method="tools/list",
        params={}
    )
    
    response = await server.router.handle_request(request)
    
    assert response.id == 2
    assert response.error is None
    assert response.result is not None
    assert "tools" in response.result
    assert isinstance(response.result["tools"], list)
    assert len(response.result["tools"]) > 0


@pytest.mark.asyncio
async def test_resources_list():
    """Test resources/list method."""
    from mcp.server import MCPServer
    
    server = MCPServer(transport_type="stdio")
    
    request = JSONRPCRequest(
        id=3,
        method="resources/list",
        params={}
    )
    
    response = await server.router.handle_request(request)
    
    assert response.id == 3
    assert response.error is None
    assert response.result is not None
    assert "resources" in response.result
    assert isinstance(response.result["resources"], list)


@pytest.mark.asyncio
async def test_prompts_list():
    """Test prompts/list method."""
    from mcp.server import MCPServer
    
    server = MCPServer(transport_type="stdio")
    
    request = JSONRPCRequest(
        id=4,
        method="prompts/list",
        params={}
    )
    
    response = await server.router.handle_request(request)
    
    assert response.id == 4
    assert response.error is None
    assert response.result is not None
    assert "prompts" in response.result
    assert isinstance(response.result["prompts"], list)


@pytest.mark.asyncio
async def test_method_not_found():
    """Test method not found error."""
    from mcp.server import MCPServer
    
    server = MCPServer(transport_type="stdio")
    
    request = JSONRPCRequest(
        id=5,
        method="unknown/method",
        params={}
    )
    
    response = await server.router.handle_request(request)
    
    assert response.id == 5
    assert response.error is not None
    assert response.error.code == -32601  # METHOD_NOT_FOUND
    assert "Method not found" in response.error.message

