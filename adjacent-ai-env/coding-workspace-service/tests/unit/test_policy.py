"""Unit tests for policy enforcement."""
import pytest
from pathlib import Path
import tempfile

from cws.internal.policy.loader import Policy, load_policy


def test_policy_path_validation():
    """Test path validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        policy = Policy({
            "allowedPaths": ["**/*"],
            "deniedPaths": ["**/__pycache__/**"]
        })
        
        # Allowed paths (with **/* pattern, all files should be allowed except denied)
        assert policy.is_path_allowed("test.py", workspace_root) == True
        assert policy.is_path_allowed("test.md", workspace_root) == True
        assert policy.is_path_allowed("dir/test.py", workspace_root) == True
        
        # Denied path
        assert policy.is_path_allowed("__pycache__/test.pyc", workspace_root) == False


def test_policy_command_validation():
    """Test command validation."""
    policy = Policy({
        "allowedCommands": ["python3", "npm", "make"]
    })
    
    assert policy.is_command_allowed("python3") == True
    assert policy.is_command_allowed("npm") == True
    assert policy.is_command_allowed("rm") == False


def test_policy_confirmation_required():
    """Test confirmation requirements."""
    policy = Policy({
        "confirmationRequired": ["delete", "applyPatch", "task.run"]
    })
    
    assert policy.requires_confirmation("delete") == True
    assert policy.requires_confirmation("applyPatch") == True
    assert policy.requires_confirmation("read") == False


def test_load_policy():
    """Test loading policy from file."""
    import json
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        policy_file = workspace_root / ".cws-policy.json"
        
        policy_data = {
            "allowedPaths": ["**/*"],
            "allowedCommands": ["python3"]
        }
        
        with open(policy_file, "w") as f:
            json.dump(policy_data, f)
        
        policy = load_policy(workspace_root)
        assert policy is not None
        assert policy.is_command_allowed("python3") == True


def test_path_traversal_prevention():
    """Test path traversal prevention."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        policy = Policy({})
        
        # Path traversal should be detected
        with pytest.raises(ValueError, match="Path traversal"):
            policy._normalize_path("../../etc/passwd", workspace_root)

