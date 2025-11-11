"""Code editor with diff generation and patch application."""
import difflib
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class CodeEditor:
    """Handles code editing with diff generation and patch application."""
    
    def __init__(self, workspace_root: Path, config: Dict[str, Any]):
        """Initialize code editor."""
        self.workspace_root = workspace_root.resolve()
        self.config = config
        self.audit_log = config.get("workspace", {}).get("audit_log", "logs/assistant_audit.jsonl")
        self._ensure_audit_log_dir()
    
    def _ensure_audit_log_dir(self):
        """Ensure audit log directory exists."""
        audit_path = Path(self.audit_log)
        audit_path.parent.mkdir(parents=True, exist_ok=True)
    
    def generate_diff(
        self,
        file_path: str,
        old_content: str,
        new_content: str
    ) -> str:
        """Generate unified diff between old and new content."""
        # Normalize paths
        rel_path = str(Path(file_path).relative_to(self.workspace_root))
        
        # Generate unified diff
        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}",
            lineterm=""
        )
        
        return "".join(diff)
    
    def apply_patch(
        self,
        file_path: str,
        new_content: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Apply patch to file."""
        full_path = self.workspace_root / file_path
        
        if not full_path.exists():
            if dry_run:
                return {
                    "status": "would_create",
                    "file": file_path,
                    "size": len(new_content)
                }
            # Create new file
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            self._log_audit("create", file_path, None, new_content)
            
            return {
                "status": "created",
                "file": file_path,
                "size": len(new_content)
            }
        
        # Read old content
        with open(full_path, "r", encoding="utf-8") as f:
            old_content = f.read()
        
        if old_content == new_content:
            return {
                "status": "no_change",
                "file": file_path
            }
        
        # Generate diff
        diff = self.generate_diff(file_path, old_content, new_content)
        
        if dry_run:
            return {
                "status": "would_modify",
                "file": file_path,
                "diff": diff,
                "old_size": len(old_content),
                "new_size": len(new_content)
            }
        
        # Apply changes
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        self._log_audit("modify", file_path, old_content, new_content)
        
        return {
            "status": "modified",
            "file": file_path,
            "diff": diff,
            "old_size": len(old_content),
            "new_size": len(new_content)
        }
    
    def rollback_file(self, file_path: str, git_commit: Optional[str] = None) -> Dict[str, Any]:
        """Rollback file to previous version."""
        full_path = self.workspace_root / file_path
        
        if git_commit:
            # Use git to restore
            try:
                result = subprocess.run(
                    ["git", "checkout", git_commit, "--", file_path],
                    cwd=self.workspace_root,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self._log_audit("rollback", file_path, None, f"git_commit:{git_commit}")
                    return {
                        "status": "rolled_back",
                        "file": file_path,
                        "method": "git"
                    }
            except Exception as e:
                logger.warning("Git rollback failed", file=file_path, error=str(e))
        
        # Try to restore from backup if available
        # For now, return error
        return {
            "status": "error",
            "file": file_path,
            "error": "No backup available"
        }
    
    def create_patch(
        self,
        changes: List[Dict[str, Any]]
    ) -> str:
        """Create a unified patch from multiple changes."""
        patch_lines = []
        
        for change in changes:
            file_path = change.get("file")
            old_content = change.get("old_content", "")
            new_content = change.get("new_content", "")
            
            diff = self.generate_diff(file_path, old_content, new_content)
            patch_lines.append(diff)
        
        return "\n".join(patch_lines)
    
    def apply_patch_string(
        self,
        patch: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Apply a patch string (unified diff format)."""
        # Parse patch
        # For now, simple implementation
        # In production, use patch command or proper parser
        
        if dry_run:
            return {
                "status": "would_apply",
                "files_affected": self._count_files_in_patch(patch)
            }
        
        # Apply using git apply or similar
        try:
            result = subprocess.run(
                ["git", "apply", "--check"],
                input=patch,
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Apply patch
                result = subprocess.run(
                    ["git", "apply"],
                    input=patch,
                    cwd=self.workspace_root,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self._log_audit("apply_patch", "multiple", None, patch)
                    return {
                        "status": "applied",
                        "files_affected": self._count_files_in_patch(patch)
                    }
        except Exception as e:
            logger.error("Failed to apply patch", error=str(e))
        
        return {
            "status": "error",
            "error": "Failed to apply patch"
        }
    
    def _count_files_in_patch(self, patch: str) -> int:
        """Count files affected by patch."""
        files = set()
        for line in patch.splitlines():
            if line.startswith("---") or line.startswith("+++"):
                if "/" in line:
                    file_part = line.split("/", 1)[1].strip()
                    if file_part:
                        files.add(file_part)
        return len(files)
    
    def _log_audit(
        self,
        action: str,
        file_path: str,
        old_content: Optional[str],
        new_content: Optional[str]
    ):
        """Log action to audit log."""
        try:
            audit_path = Path(self.audit_log)
            with open(audit_path, "a") as f:
                import json
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "action": action,
                    "file": file_path,
                    "old_size": len(old_content) if old_content else 0,
                    "new_size": len(new_content) if new_content else 0
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.warning("Failed to write audit log", error=str(e))

