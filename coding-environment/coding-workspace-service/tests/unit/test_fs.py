"""Unit tests for file operations."""
import pytest
from pathlib import Path
import tempfile
import os

from cws.internal.policy.loader import Policy
from cws.internal.fs.operations import FileOperations


@pytest.mark.asyncio
async def test_fs_read():
    """Test reading a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        policy = Policy({})
        fs = FileOperations(workspace_root, policy)
        
        # Create test file
        test_file = workspace_root / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Read file
        result = await fs.read("test.txt")
        assert result["content"] == "Hello, World!"
        assert result["size"] == 13
        assert result["isBinary"] == False


@pytest.mark.asyncio
async def test_fs_write():
    """Test writing a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        policy = Policy({})
        fs = FileOperations(workspace_root, policy)
        
        # Write file
        result = await fs.write("test.txt", "Hello, World!", {"atomic": True})
        assert result["size"] == 13
        
        # Verify file exists
        test_file = workspace_root / "test.txt"
        assert test_file.exists()
        assert test_file.read_text() == "Hello, World!"


@pytest.mark.asyncio
async def test_fs_create():
    """Test creating file/directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        policy = Policy({})
        fs = FileOperations(workspace_root, policy)
        
        # Create file
        result = await fs.create("newfile.txt", "file")
        assert result["type"] == "file"
        
        # Create directory
        result = await fs.create("newdir", "dir")
        assert result["type"] == "dir"


@pytest.mark.asyncio
async def test_fs_list():
    """Test listing directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        policy = Policy({})
        fs = FileOperations(workspace_root, policy)
        
        # Create files
        (workspace_root / "file1.txt").write_text("test1")
        (workspace_root / "file2.txt").write_text("test2")
        (workspace_root / "subdir").mkdir()
        
        # List directory
        result = await fs.list(".", {"recursive": False})
        assert len(result["entries"]) == 3


@pytest.mark.asyncio
async def test_fs_path_traversal_prevention():
    """Test path traversal prevention."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        policy = Policy({})
        fs = FileOperations(workspace_root, policy)
        
        # Attempt path traversal
        with pytest.raises(ValueError, match="Path traversal"):
            await fs.read("../../etc/passwd")

