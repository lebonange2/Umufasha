"""File system operations implementation."""
import os
import hashlib
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime

from cws.internal.policy.loader import Policy

logger = structlog.get_logger(__name__)


class FileOperations:
    """File system operations with policy enforcement."""
    
    def __init__(self, workspace_root: Path, policy: Policy):
        """Initialize file operations."""
        self.workspace_root = workspace_root.resolve()
        self.policy = policy
    
    def normalize_path(self, path: str) -> Path:
        """Normalize and validate path."""
        # Resolve to absolute path
        abs_path = (self.workspace_root / path).resolve()
        
        # Ensure it's within workspace root
        try:
            rel_path = abs_path.relative_to(self.workspace_root)
        except ValueError:
            raise ValueError("Path traversal detected")
        
        # Check policy
        if not self.policy.is_path_allowed(str(rel_path), self.workspace_root):
            raise ValueError(f"Path not allowed by policy: {path}")
        
        return abs_path
    
    async def read(self, path: str) -> Dict[str, Any]:
        """Read file content."""
        file_path = self.normalize_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not file_path.is_file():
            raise ValueError(f"Not a file: {path}")
        
        # Check size
        size = file_path.stat().st_size
        if size > self.policy.max_file_size:
            raise ValueError(f"File too large: {size} bytes (max: {self.policy.max_file_size})")
        
        # Read file
        with open(file_path, "rb") as f:
            content = f.read()
        
        # Determine if binary
        try:
            text = content.decode("utf-8")
            is_binary = False
        except UnicodeDecodeError:
            text = None
            is_binary = True
        
        # Calculate hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Get mtime
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        
        result = {
            "path": path,
            "size": size,
            "mtime": mtime,
            "hash": file_hash,
            "isBinary": is_binary
        }
        
        if is_binary:
            result["content"] = base64.b64encode(content).decode("ascii")
        else:
            result["content"] = text
        
        return result
    
    async def write(self, path: str, contents: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Write file content."""
        options = options or {}
        file_path = self.normalize_path(path)
        
        # Check size
        content_bytes = contents.encode("utf-8") if isinstance(contents, str) else contents
        if len(content_bytes) > self.policy.max_edit_size:
            raise ValueError(f"Content too large: {len(content_bytes)} bytes (max: {self.policy.max_edit_size})")
        
        # Create parent directories if needed
        if options.get("createIfMissing", True):
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Atomic write
        if options.get("atomic", True):
            # Write to temp file, then rename
            temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
            try:
                with open(temp_path, "wb") as f:
                    f.write(content_bytes)
                temp_path.replace(file_path)
            except Exception as e:
                if temp_path.exists():
                    temp_path.unlink()
                raise
        else:
            with open(file_path, "wb") as f:
                f.write(content_bytes)
        
        return {"path": path, "size": len(content_bytes)}
    
    async def create(self, path: str, type: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create file or directory."""
        options = options or {}
        file_path = self.normalize_path(path)
        
        if file_path.exists():
            raise FileExistsError(f"Path already exists: {path}")
        
        # Create parent directories if needed
        if options.get("parents", True):
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if type == "file":
            file_path.touch()
        elif type == "dir":
            file_path.mkdir(parents=True)
        else:
            raise ValueError(f"Invalid type: {type}")
        
        return {"path": path, "type": type}
    
    async def delete(self, path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Delete file or directory."""
        options = options or {}
        file_path = self.normalize_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        # Check confirmation if required
        if self.policy.requires_confirmation("delete"):
            if not options.get("confirmed", False):
                raise ValueError("Confirmation required for delete operation")
        
        # Delete
        if file_path.is_dir():
            if options.get("recursive", False):
                import shutil
                shutil.rmtree(file_path)
            else:
                raise ValueError("Cannot delete directory without recursive option")
        else:
            file_path.unlink()
        
        return {"path": path, "deleted": True}
    
    async def move(self, src: str, dst: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Move file or directory."""
        options = options or {}
        src_path = self.normalize_path(src)
        dst_path = self.normalize_path(dst)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source not found: {src}")
        
        if dst_path.exists() and not options.get("overwrite", False):
            raise FileExistsError(f"Destination already exists: {dst}")
        
        # Move
        src_path.rename(dst_path)
        
        return {"src": src, "dst": dst}
    
    async def list(self, path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List directory contents."""
        options = options or {}
        dir_path = self.normalize_path(path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {path}")
        
        entries = []
        max_entries = options.get("maxEntries", 10000)
        count = 0
        
        def should_include(entry_path: Path) -> bool:
            """Check if entry should be included."""
            # Check glob patterns
            globs = options.get("globs", [])
            if globs:
                import fnmatch
                rel_path = str(entry_path.relative_to(self.workspace_root))
                return any(fnmatch.fnmatch(rel_path, pattern) for pattern in globs)
            return True
        
        for entry in dir_path.iterdir():
            if count >= max_entries:
                break
            
            # Check policy
            try:
                rel_path = str(entry.relative_to(self.workspace_root))
                if not self.policy.is_path_allowed(rel_path, self.workspace_root):
                    continue
            except ValueError:
                continue
            
            if not should_include(entry):
                continue
            
            entry_info = {
                "name": entry.name,
                "path": str(entry.relative_to(self.workspace_root)),
                "type": "file" if entry.is_file() else "dir",
                "size": entry.stat().st_size if entry.is_file() else None,
                "mtime": datetime.fromtimestamp(entry.stat().st_mtime).isoformat()
            }
            entries.append(entry_info)
            count += 1
            
            # Recurse if needed
            if options.get("recursive", False) and entry.is_dir():
                sub_entries = await self.list(str(entry.relative_to(self.workspace_root)), options)
                entries.extend(sub_entries.get("entries", []))
        
        return {"path": path, "entries": entries, "count": len(entries)}

