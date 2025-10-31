"""Integration tests for CWS server."""
import pytest
import asyncio
import tempfile
from pathlib import Path

from cws.internal.protocol.server import CWSServer
from cws.internal.protocol.messages import JSONRPCRequest


@pytest.mark.asyncio
async def test_server_initialize():
    """Test server initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = CWSServer(tmpdir)
        
        request = JSONRPCRequest(
            id=1,
            method="initialize",
            params={
                "protocolVersion": "1.0.0",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"}
            }
        )
        
        response = await server.handle_request(request)
        assert response.result is not None
        assert response.result["protocolVersion"] == "1.0.0"


@pytest.mark.asyncio
async def test_server_fs_operations():
    """Test file operations via server."""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = CWSServer(tmpdir)
        
        # Write file
        request = JSONRPCRequest(
            id=1,
            method="fs.write",
            params={
                "path": "test.txt",
                "contents": "Hello, World!"
            }
        )
        
        response = await server.handle_request(request)
        assert response.error is None
        assert response.result["size"] == 13
        
        # Read file
        request = JSONRPCRequest(
            id=2,
            method="fs.read",
            params={"path": "test.txt"}
        )
        
        response = await server.handle_request(request)
        assert response.error is None
        assert response.result["content"] == "Hello, World!"


@pytest.mark.asyncio
async def test_server_search():
    """Test search operations via server."""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = CWSServer(tmpdir)
        
        # Create test file
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("def hello():\n    print('Hello')\n")
        
        # Search
        request = JSONRPCRequest(
            id=1,
            method="search.find",
            params={
                "query": "def hello",
                "options": {"regex": False}
            }
        )
        
        response = await server.handle_request(request)
        assert response.error is None
        assert len(response.result["results"]) > 0

