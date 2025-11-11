"""Unit tests for code editor."""
import pytest
import tempfile
from pathlib import Path

from mcp.plugins.cursor_clone.agent.editor import CodeEditor


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config():
    """Create test config."""
    return {
        "workspace": {
            "audit_log": "logs/audit.jsonl"
        }
    }


@pytest.fixture
def editor(temp_dir, config):
    """Create code editor."""
    return CodeEditor(temp_dir, config)


def test_generate_diff(editor):
    """Test diff generation."""
    old_content = "def hello():\n    print('Hello')\n"
    new_content = "def hello():\n    print('Hello, World!')\n"
    
    diff = editor.generate_diff("test.py", old_content, new_content)
    
    assert "---" in diff
    assert "+++" in diff
    assert "test.py" in diff


def test_apply_patch_create(editor, temp_dir):
    """Test applying patch to create file."""
    file_path = "new_file.py"
    content = "print('Hello')\n"
    
    result = editor.apply_patch(file_path, content, dry_run=True)
    
    assert result["status"] == "would_create"
    assert result["file"] == file_path
    
    # Actually create
    result = editor.apply_patch(file_path, content, dry_run=False)
    assert result["status"] == "created"
    assert (temp_dir / file_path).exists()


def test_apply_patch_modify(editor, temp_dir):
    """Test applying patch to modify file."""
    file_path = "test.py"
    old_content = "print('Hello')\n"
    new_content = "print('Hello, World!')\n"
    
    # Create file
    (temp_dir / file_path).write_text(old_content)
    
    # Modify
    result = editor.apply_patch(file_path, new_content, dry_run=True)
    assert result["status"] == "would_modify"
    
    result = editor.apply_patch(file_path, new_content, dry_run=False)
    assert result["status"] == "modified"
    assert (temp_dir / file_path).read_text() == new_content

