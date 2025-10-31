"""Policy loader and validation."""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger(__name__)


class Policy:
    """Workspace security policy."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize policy from configuration."""
        self.allowed_paths = config.get("allowedPaths", ["**/*"])
        self.denied_paths = config.get("deniedPaths", [])
        self.max_file_size = config.get("maxFileSize", 10 * 1024 * 1024)  # 10MB
        self.max_edit_size = config.get("maxEditSize", 1024 * 1024)  # 1MB
        self.allowed_commands = config.get("allowedCommands", [])
        self.env_allowlist = config.get("envAllowlist", [])
        self.confirmation_required = config.get("confirmationRequired", ["delete", "applyPatch", "task.run"])
    
    def is_path_allowed(self, path: str, workspace_root: Path) -> bool:
        """Check if path is allowed."""
        try:
            # Normalize path (will raise if path traversal)
            normalized = self._normalize_path(path, workspace_root)
        except ValueError:
            # Path traversal or normalization error
            return False
        
        # Convert to string for pattern matching
        path_str = str(normalized).replace("\\", "/")
        
        # Check denied paths first
        for pattern in self.denied_paths:
            if self._match_pattern(normalized, pattern):
                return False
        
        # Check allowed paths
        if not self.allowed_paths or self.allowed_paths == ["**/*"]:
            # Default allow if no restrictions or wildcard
            return True
        
        for pattern in self.allowed_paths:
            if self._match_pattern(normalized, pattern):
                return True
        
        # Default deny
        return False
    
    def is_command_allowed(self, command: str, args: List[str] = None) -> bool:
        """Check if command is allowed."""
        if not self.allowed_commands:
            return False
        
        # Check command name
        if command not in self.allowed_commands:
            return False
        
        # TODO: Check args patterns if needed
        return True
    
    def requires_confirmation(self, operation: str) -> bool:
        """Check if operation requires confirmation."""
        return operation in self.confirmation_required
    
    def _normalize_path(self, path: str, workspace_root: Path) -> Path:
        """Normalize and validate path."""
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
        
        return rel_path
    
    def _match_pattern(self, path: Path, pattern: str) -> bool:
        """Simple glob pattern matching."""
        # Convert path to string (use forward slashes for glob matching)
        path_str = str(path).replace("\\", "/")
        
        # Simple glob matching
        import fnmatch
        return fnmatch.fnmatch(path_str, pattern)


def load_policy(workspace_root: Path) -> Optional[Policy]:
    """Load policy from .cws-policy.json."""
    policy_file = workspace_root / ".cws-policy.json"
    
    if not policy_file.exists():
        logger.debug("No policy file found, using defaults", path=str(policy_file))
        return Policy({})
    
    try:
        with open(policy_file, "r") as f:
            config = json.load(f)
        return Policy(config)
    except Exception as e:
        logger.warning("Failed to load policy, using defaults", error=str(e))
        return Policy({})

