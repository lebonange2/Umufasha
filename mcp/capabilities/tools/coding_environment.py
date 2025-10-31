"""Coding Environment tools integrated into MCP server."""
from typing import Dict, Any, Optional, List
from pathlib import Path
import hashlib
import base64
import re
import os
import asyncio
import subprocess
import uuid
from datetime import datetime

from mcp.capabilities.tools.base import FunctionTool
from mcp.core.concurrency import CancellationToken
from mcp.capabilities.tools.coding_environment.policy import load_policy, Policy
from mcp.capabilities.tools.coding_environment.path_utils import normalize_path


logger = None  # Will be set during initialization


async def read_file_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Read file content."""
    if cancellation_token:
        cancellation_token.check()
    
    workspace_root = Path(params.get("workspaceRoot", "."))
    path = params["path"]
    
    # Load policy
    policy = load_policy(workspace_root)
    
    # Normalize and validate path
    try:
        file_path = normalize_path(path, workspace_root, policy)
    except ValueError as e:
        return {"error": str(e)}
    
    if not file_path.exists():
        return {"error": f"File not found: {path}"}
    
    if not file_path.is_file():
        return {"error": f"Not a file: {path}"}
    
    # Check size
    size = file_path.stat().st_size
    if size > policy.max_file_size:
        return {"error": f"File too large: {size} bytes (max: {policy.max_file_size})"}
    
    # Read file
    try:
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
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}


async def write_file_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Write file content."""
    if cancellation_token:
        cancellation_token.check()
    
    workspace_root = Path(params.get("workspaceRoot", "."))
    path = params["path"]
    contents = params["contents"]
    options = params.get("options", {})
    
    # Load policy
    policy = load_policy(workspace_root)
    
    # Normalize and validate path
    try:
        file_path = normalize_path(path, workspace_root, policy)
    except ValueError as e:
        return {"error": str(e)}
    
    # Check size
    content_bytes = contents.encode("utf-8") if isinstance(contents, str) else contents
    if len(content_bytes) > policy.max_edit_size:
        return {"error": f"Content too large: {len(content_bytes)} bytes (max: {policy.max_edit_size})"}
    
    # Create parent directories if needed
    if options.get("createIfMissing", True):
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic write
    try:
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
                return {"error": f"Failed to write file: {str(e)}"}
        else:
            with open(file_path, "wb") as f:
                f.write(content_bytes)
        
        return {"path": path, "size": len(content_bytes)}
    except Exception as e:
        return {"error": f"Failed to write file: {str(e)}"}


async def search_files_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Search for text in files."""
    if cancellation_token:
        cancellation_token.check()
    
    workspace_root = Path(params.get("workspaceRoot", "."))
    query = params["query"]
    options = params.get("options", {})
    
    # Load policy
    policy = load_policy(workspace_root)
    
    use_regex = options.get("regex", False)
    case_sensitive = options.get("caseSensitive", False)
    globs = options.get("globs", ["**/*"])
    max_results = options.get("maxResults", 1000)
    
    # Compile pattern
    if use_regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(query, flags)
    else:
        # Escape special regex characters
        escaped = re.escape(query)
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(escaped, flags)
    
    results = []
    count = 0
    
    # Match globs
    import fnmatch
    for pattern_str in globs:
        for file_path in workspace_root.rglob(pattern_str.replace("**", "*")):
            if count >= max_results:
                break
            
            # Check policy
            try:
                rel_path = str(file_path.relative_to(workspace_root))
                if not policy.is_path_allowed(rel_path, workspace_root):
                    continue
            except ValueError:
                continue
            
            # Skip directories
            if not file_path.is_file():
                continue
            
            # Try to read and search
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.splitlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        match = pattern.search(line)
                        if match:
                            results.append({
                                "path": rel_path,
                                "line": line_num,
                                "column": match.start() + 1,
                                "text": line.strip()
                            })
                            count += 1
                            
                            if count >= max_results:
                                break
            except Exception:
                continue
    
    return {"query": query, "results": results, "count": len(results)}


async def list_files_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """List directory contents."""
    if cancellation_token:
        cancellation_token.check()
    
    workspace_root = Path(params.get("workspaceRoot", "."))
    path = params.get("path", ".")
    options = params.get("options", {})
    
    # Load policy
    policy = load_policy(workspace_root)
    
    # Normalize path
    try:
        dir_path = normalize_path(path, workspace_root, policy)
    except ValueError as e:
        return {"error": str(e)}
    
    if not dir_path.exists():
        return {"error": f"Directory not found: {path}"}
    
    if not dir_path.is_dir():
        return {"error": f"Not a directory: {path}"}
    
    entries = []
    max_entries = options.get("maxEntries", 10000)
    count = 0
    
    def should_include(entry_path: Path) -> bool:
        """Check if entry should be included."""
        globs = options.get("globs", [])
        if globs:
            import fnmatch
            rel_path = str(entry_path.relative_to(workspace_root))
            return any(fnmatch.fnmatch(rel_path, pattern) for pattern in globs)
        return True
    
    for entry in dir_path.iterdir():
        if count >= max_entries:
            break
        
        # Check policy
        try:
            rel_path = str(entry.relative_to(workspace_root))
            if not policy.is_path_allowed(rel_path, workspace_root):
                continue
        except ValueError:
            continue
        
        if not should_include(entry):
            continue
        
        entry_info = {
            "name": entry.name,
            "path": rel_path,
            "type": "file" if entry.is_file() else "dir",
            "size": entry.stat().st_size if entry.is_file() else None,
            "mtime": datetime.fromtimestamp(entry.stat().st_mtime).isoformat()
        }
        entries.append(entry_info)
        count += 1
        
        # Recurse if needed
        if options.get("recursive", False) and entry.is_dir():
            sub_result = await list_files_tool({
                "workspaceRoot": str(workspace_root),
                "path": rel_path,
                "options": options
            }, cancellation_token)
            if "entries" in sub_result:
                entries.extend(sub_result["entries"])
    
    return {"path": path, "entries": entries, "count": len(entries)}


async def run_command_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Run a command in the workspace."""
    if cancellation_token:
        cancellation_token.check()
    
    workspace_root = Path(params.get("workspaceRoot", "."))
    command = params["command"]
    args = params.get("args", [])
    options = params.get("options", {})
    
    # Load policy
    policy = load_policy(workspace_root)
    
    # Check confirmation
    if policy.requires_confirmation("task.run"):
        if not options.get("confirmed", False):
            return {"error": "Confirmation required for task.run operation"}
    
    # Check policy
    if not policy.is_command_allowed(command, args):
        return {"error": f"Command not allowed by policy: {command}"}
    
    # Prepare command
    cwd = options.get("cwd", str(workspace_root))
    env = options.get("env", {})
    timeout = options.get("timeout", 300)  # 5 minutes default
    
    # Merge environment
    full_env = dict(os.environ)
    full_env.update(env)
    
    # Filter environment variables by allowlist
    if policy.env_allowlist:
        filtered_env = {k: v for k, v in full_env.items() if k in policy.env_allowlist}
        filtered_env.update(env)  # Always include explicitly provided env vars
        full_env = filtered_env
    
    # Run command
    try:
        process = await asyncio.create_subprocess_exec(
            command,
            *args,
            cwd=cwd,
            env=full_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutExpired:
            process.kill()
            await process.wait()
            return {
                "command": command,
                "args": args,
                "exitCode": -1,
                "stdout": "",
                "stderr": "Command timed out",
                "timedOut": True
            }
        
        return {
            "command": command,
            "args": args,
            "exitCode": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace")
        }
    except Exception as e:
        return {
            "command": command,
            "args": args,
            "exitCode": -1,
            "stdout": "",
            "stderr": str(e),
            "error": True
        }


# Export tools
READ_FILE_TOOL = FunctionTool(
    name="readFile",
    description="Read file content from workspace",
    input_schema={
        "type": "object",
        "properties": {
            "workspaceRoot": {"type": "string", "description": "Workspace root directory (default: current directory)"},
            "path": {"type": "string", "description": "File path relative to workspace root"}
        },
        "required": ["path"]
    },
    handler=read_file_tool
)

WRITE_FILE_TOOL = FunctionTool(
    name="writeFile",
    description="Write file content to workspace",
    input_schema={
        "type": "object",
        "properties": {
            "workspaceRoot": {"type": "string", "description": "Workspace root directory (default: current directory)"},
            "path": {"type": "string", "description": "File path relative to workspace root"},
            "contents": {"type": "string", "description": "File contents to write"},
            "options": {
                "type": "object",
                "properties": {
                    "atomic": {"type": "boolean", "description": "Use atomic write (default: true)"},
                    "createIfMissing": {"type": "boolean", "description": "Create parent directories if missing (default: true)"}
                }
            }
        },
        "required": ["path", "contents"]
    },
    handler=write_file_tool
)

SEARCH_FILES_TOOL = FunctionTool(
    name="searchFiles",
    description="Search for text in files",
    input_schema={
        "type": "object",
        "properties": {
            "workspaceRoot": {"type": "string", "description": "Workspace root directory (default: current directory)"},
            "query": {"type": "string", "description": "Search query"},
            "options": {
                "type": "object",
                "properties": {
                    "regex": {"type": "boolean", "description": "Use regex pattern (default: false)"},
                    "caseSensitive": {"type": "boolean", "description": "Case sensitive search (default: false)"},
                    "globs": {"type": "array", "items": {"type": "string"}, "description": "File glob patterns to search"},
                    "maxResults": {"type": "integer", "description": "Maximum results to return (default: 1000)"}
                }
            }
        },
        "required": ["query"]
    },
    handler=search_files_tool
)

LIST_FILES_TOOL = FunctionTool(
    name="listFiles",
    description="List directory contents",
    input_schema={
        "type": "object",
        "properties": {
            "workspaceRoot": {"type": "string", "description": "Workspace root directory (default: current directory)"},
            "path": {"type": "string", "description": "Directory path relative to workspace root (default: .)"},
            "options": {
                "type": "object",
                "properties": {
                    "recursive": {"type": "boolean", "description": "List recursively (default: false)"},
                    "globs": {"type": "array", "items": {"type": "string"}, "description": "File glob patterns to include"},
                    "maxEntries": {"type": "integer", "description": "Maximum entries to return (default: 10000)"}
                }
            }
        }
    },
    handler=list_files_tool
)

RUN_COMMAND_TOOL = FunctionTool(
    name="runCommand",
    description="Run a command in the workspace",
    input_schema={
        "type": "object",
        "properties": {
            "workspaceRoot": {"type": "string", "description": "Workspace root directory (default: current directory)"},
            "command": {"type": "string", "description": "Command to run"},
            "args": {"type": "array", "items": {"type": "string"}, "description": "Command arguments"},
            "options": {
                "type": "object",
                "properties": {
                    "cwd": {"type": "string", "description": "Working directory"},
                    "env": {"type": "object", "description": "Environment variables"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default: 300)"},
                    "confirmed": {"type": "boolean", "description": "Confirmation flag (required if policy requires it)"}
                }
            }
        },
        "required": ["command"]
    },
    handler=run_command_tool
)

