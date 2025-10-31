"""Path utilities for coding environment."""
from pathlib import Path

from mcp.capabilities.tools.coding_environment.policy import Policy


def normalize_path(path: str, workspace_root: Path, policy: Policy) -> Path:
    """Normalize and validate path against workspace root and policy."""
    # Resolve workspace root to absolute
    workspace_abs = workspace_root.resolve()
    
    # Join path with workspace root (handles both absolute and relative paths)
    if Path(path).is_absolute():
        abs_path = Path(path).resolve()
    else:
        abs_path = (workspace_abs / path).resolve()
    
    # Ensure it's within workspace root
    try:
        rel_path = abs_path.relative_to(workspace_abs)
    except ValueError:
        # Path outside workspace - deny access
        raise ValueError("Path traversal detected")
    
    # Check policy
    if not policy.is_path_allowed(str(rel_path), workspace_root):
        raise ValueError(f"Path not allowed by policy: {path}")
    
    return abs_path

