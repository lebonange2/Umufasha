"""E2E workflow tests."""
import pytest
import asyncio
import tempfile
from pathlib import Path
import subprocess
import sys
import json

@pytest.mark.asyncio
async def test_e2e_file_operations():
    """E2E test: File operations workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Start CWS server
        proc = subprocess.Popen(
            [sys.executable, "-m", "cws.main", "--transport", "stdio", "--workspace-root", tmpdir],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=tmpdir
        )
        
        try:
            # Initialize
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0.0"}
                }
            }
            proc.stdin.write(f"{json.dumps(request)}\n")
            proc.stdin.flush()
            
            # Write file
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "fs.write",
                "params": {
                    "path": "test.txt",
                    "contents": "Hello, World!"
                }
            }
            proc.stdin.write(f"{json.dumps(request)}\n")
            proc.stdin.flush()
            
            # Read response
            response_line = proc.stdout.readline()
            response = json.loads(response_line)
            assert response.get("id") == 2
            assert response.get("result") is not None
            
        finally:
            proc.terminate()
            proc.wait()


@pytest.mark.asyncio
async def test_e2e_search_workflow():
    """E2E test: Search workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("def hello():\n    print('Hello')\n")
        
        # Start CWS server
        proc = subprocess.Popen(
            [sys.executable, "-m", "cws.main", "--transport", "stdio", "--workspace-root", tmpdir],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=tmpdir
        )
        
        try:
            # Search
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "search.find",
                "params": {
                    "query": "def hello",
                    "options": {}
                }
            }
            proc.stdin.write(f"{json.dumps(request)}\n")
            proc.stdin.flush()
            
            # Read response
            response_line = proc.stdout.readline()
            response = json.loads(response_line)
            assert response.get("id") == 1
            assert response.get("result") is not None
            assert len(response["result"].get("results", [])) > 0
            
        finally:
            proc.terminate()
            proc.wait()
