"""Task and terminal operations."""
import asyncio
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import structlog
import uuid

from cws.internal.policy.loader import Policy

logger = structlog.get_logger(__name__)


class TaskOperations:
    """Task and terminal operations."""
    
    def __init__(self, workspace_root: Path, policy: Policy):
        """Initialize task operations."""
        self.workspace_root = workspace_root.resolve()
        self.policy = policy
        self.terminals: Dict[str, Any] = {}  # Terminal sessions
    
    async def run(self, command: str, args: Optional[List[str]] = None, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run a command."""
        options = options or {}
        args = args or []
        
        # Check confirmation
        if self.policy.requires_confirmation("task.run"):
            if not options.get("confirmed", False):
                raise ValueError("Confirmation required for task.run operation")
        
        # Check policy
        if not self.policy.is_command_allowed(command, args):
            raise ValueError(f"Command not allowed by policy: {command}")
        
        # Prepare command
        cwd = options.get("cwd", str(self.workspace_root))
        env = options.get("env", {})
        timeout = options.get("timeout", 300)  # 5 minutes default
        
        # Merge environment
        full_env = dict(os.environ)
        full_env.update(env)
        
        # Filter environment variables by allowlist
        if self.policy.env_allowlist:
            filtered_env = {k: v for k, v in full_env.items() if k in self.policy.env_allowlist}
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
    
    async def build(self) -> Dict[str, Any]:
        """Run build task."""
        # Check for tasks.json or common build commands
        tasks_file = self.workspace_root / ".vscode" / "tasks.json"
        
        if tasks_file.exists():
            # Parse tasks.json and find build task
            # Simplified for now
            pass
        
        # Try common build commands
        for cmd in ["npm run build", "make", "python setup.py build"]:
            parts = cmd.split()
            if self.policy.is_command_allowed(parts[0]):
                return await self.run(parts[0], parts[1:])
        
        raise ValueError("No build command found")
    
    async def test(self) -> Dict[str, Any]:
        """Run test task."""
        # Try common test commands
        for cmd in ["npm test", "pytest", "python -m pytest", "make test"]:
            parts = cmd.split()
            if self.policy.is_command_allowed(parts[0]):
                return await self.run(parts[0], parts[1:])
        
        raise ValueError("No test command found")
    
    async def create_terminal(self, name: Optional[str] = None, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Create a terminal session."""
        terminal_id = str(uuid.uuid4())
        terminal_cwd = cwd or str(self.workspace_root)
        
        self.terminals[terminal_id] = {
            "id": terminal_id,
            "name": name or terminal_id,
            "cwd": terminal_cwd,
            "process": None
        }
        
        return {"id": terminal_id, "name": name, "cwd": terminal_cwd}
    
    async def send_terminal(self, terminal_id: str, data: str) -> Dict[str, Any]:
        """Send data to terminal."""
        if terminal_id not in self.terminals:
            raise ValueError(f"Terminal not found: {terminal_id}")
        
        terminal = self.terminals[terminal_id]
        # Would send to terminal process
        # Simplified for now
        return {"id": terminal_id, "sent": len(data)}
    
    async def dispose_terminal(self, terminal_id: str) -> Dict[str, Any]:
        """Dispose terminal session."""
        if terminal_id not in self.terminals:
            raise ValueError(f"Terminal not found: {terminal_id}")
        
        terminal = self.terminals[terminal_id]
        if terminal["process"]:
            terminal["process"].kill()
        
        del self.terminals[terminal_id]
        return {"id": terminal_id, "disposed": True}

