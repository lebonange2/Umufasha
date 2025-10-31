"""Code editing and diff operations."""
import difflib
from pathlib import Path
from typing import Dict, Any, List, Optional
import structlog
import tempfile
import shutil

from cws.internal.policy.loader import Policy

logger = structlog.get_logger(__name__)


class EditOperations:
    """Code editing operations."""
    
    def __init__(self, workspace_root: Path, policy: Policy):
        """Initialize edit operations."""
        self.workspace_root = workspace_root.resolve()
        self.policy = policy
    
    async def batch_edit(self, edits: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply batch edits atomically."""
        options = options or {}
        atomic = options.get("atomic", True)
        
        if atomic:
            # Create backup and apply all edits
            backups = {}
            try:
                # Create backups
                for edit in edits:
                    file_path = self.workspace_root / edit["path"]
                    if file_path.exists():
                        backups[edit["path"]] = file_path.read_bytes()
                
                # Apply edits
                results = []
                for edit in edits:
                    file_path = self.workspace_root / edit["path"]
                    
                    # Read current content
                    if file_path.exists():
                        content = file_path.read_text(encoding="utf-8")
                    else:
                        content = ""
                    
                    # Apply edit
                    new_content = self._apply_edit(content, edit)
                    
                    # Write file
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(new_content, encoding="utf-8")
                    
                    results.append({"path": edit["path"], "success": True})
                
                return {"edits": results, "applied": len(results)}
            except Exception as e:
                # Rollback
                for path, backup in backups.items():
                    file_path = self.workspace_root / path
                    file_path.write_bytes(backup)
                raise Exception(f"Batch edit failed, rolled back: {e}")
        else:
            # Apply edits non-atomically
            results = []
            for edit in edits:
                try:
                    file_path = self.workspace_root / edit["path"]
                    content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
                    new_content = self._apply_edit(content, edit)
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(new_content, encoding="utf-8")
                    results.append({"path": edit["path"], "success": True})
                except Exception as e:
                    results.append({"path": edit["path"], "success": False, "error": str(e)})
            
            return {"edits": results, "applied": sum(1 for r in results if r["success"])}
    
    def _apply_edit(self, content: str, edit: Dict[str, Any]) -> str:
        """Apply a single edit to content."""
        lines = content.splitlines(keepends=True)
        
        range_info = edit.get("range", {})
        start_line = range_info.get("startLine", 0)
        start_col = range_info.get("startCol", 0)
        end_line = range_info.get("endLine", len(lines))
        end_col = range_info.get("endCol", 0)
        
        new_text = edit.get("newText", "")
        
        # Build new content
        if start_line >= len(lines):
            # Append
            return content + new_text
        elif start_line == end_line:
            # Single line edit
            line = lines[start_line]
            prefix = line[:start_col] if len(line) > start_col else line
            suffix = line[end_col:] if len(line) > end_col else ""
            lines[start_line] = prefix + new_text + suffix
        else:
            # Multi-line edit
            prefix = lines[start_line][:start_col] if start_line < len(lines) else ""
            suffix = lines[end_line][end_col:] if end_line < len(lines) else ""
            
            # Replace lines
            new_lines = [prefix + new_text + suffix]
            lines = lines[:start_line] + new_lines + lines[end_line + 1:]
        
        return "".join(lines)
    
    async def diff(self, base_path: Optional[str] = None, include_globs: Optional[List[str]] = None, exclude_globs: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate unified diff."""
        # For now, simplified diff - compare current state to a reference
        # In production, would compare to git index or specified base
        
        if base_path:
            base_dir = Path(base_path)
        else:
            # Compare to git index if available
            import subprocess
            try:
                subprocess.run(["git", "status", "--porcelain"], cwd=self.workspace_root, check=True, capture_output=True)
                # Would compare to git index
            except:
                base_dir = None
        
        # Simplified: return empty diff for now
        # Full implementation would compare files
        return {"diff": "", "files": []}
    
    async def apply_patch(self, patch: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply unified diff patch."""
        options = options or {}
        
        # Check confirmation
        if self.policy.requires_confirmation("applyPatch"):
            if not options.get("confirmed", False):
                raise ValueError("Confirmation required for applyPatch operation")
        
        # Parse patch (simplified - would use proper patch parser)
        # For now, return error
        raise NotImplementedError("Patch application not fully implemented")

