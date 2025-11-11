"""Command and test runner with sandboxing."""
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import structlog
import os
import signal

logger = structlog.get_logger(__name__)


class CommandRunner:
    """Runs commands in a sandboxed environment."""
    
    def __init__(self, workspace_root: Path, config: Dict[str, Any]):
        """Initialize command runner."""
        self.workspace_root = workspace_root.resolve()
        self.config = config
        self.sandbox_config = config.get("sandbox", {})
        self.safety_config = config.get("safety", {})
        self.timeout = self.sandbox_config.get("timeout", 300)
        self.allowed_commands = self.safety_config.get("allowed_commands", [])
    
    async def run_command(
        self,
        command: str,
        args: Optional[List[str]] = None,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run a command in sandbox."""
        if args is None:
            args = []
        
        # Check if command is allowed
        if not self._is_command_allowed(command):
            return {
                "status": "error",
                "error": f"Command not allowed: {command}",
                "allowed_commands": self.allowed_commands
            }
        
        cwd = cwd or self.workspace_root
        timeout = timeout or self.timeout
        
        # Prepare environment
        full_env = dict(os.environ)
        if env:
            full_env.update(env)
        
        # Filter environment variables
        filtered_env = self._filter_env(full_env)
        
        try:
            # Run command
            process = await asyncio.create_subprocess_exec(
                command,
                *args,
                cwd=str(cwd),
                env=filtered_env,
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
                    "status": "timeout",
                    "command": command,
                    "args": args,
                    "timeout": timeout
                }
            
            return {
                "status": "success" if process.returncode == 0 else "error",
                "command": command,
                "args": args,
                "exit_code": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace")
            }
        except Exception as e:
            logger.error("Error running command", command=command, error=str(e), exc_info=True)
            return {
                "status": "error",
                "command": command,
                "error": str(e)
            }
    
    async def run_tests(
        self,
        suite: Optional[str] = None,
        pattern: Optional[str] = None,
        path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Run tests."""
        # Try to detect test framework
        test_path = path or self.workspace_root
        
        # Check for pytest
        if (test_path / "pytest.ini").exists() or (test_path / "pyproject.toml").exists():
            return await self._run_pytest(suite, pattern, test_path)
        
        # Check for unittest
        if (test_path / "tests").exists() or (test_path / "test").exists():
            return await self._run_unittest(suite, pattern, test_path)
        
        # Default: try pytest
        return await self._run_pytest(suite, pattern, test_path)
    
    async def _run_pytest(
        self,
        suite: Optional[str],
        pattern: Optional[str],
        path: Path
    ) -> Dict[str, Any]:
        """Run pytest."""
        args = []
        
        if suite:
            args.append(suite)
        elif pattern:
            args.extend(["-k", pattern])
        else:
            args.append("tests/")
        
        result = await self.run_command("python3", ["-m", "pytest"] + args, cwd=path)
        
        # Parse pytest output
        summary = self._parse_pytest_output(result.get("stdout", ""))
        
        return {
            "framework": "pytest",
            "summary": summary,
            "raw_output": result.get("stdout", ""),
            "exit_code": result.get("exit_code", 0)
        }
    
    async def _run_unittest(
        self,
        suite: Optional[str],
        pattern: Optional[str],
        path: Path
    ) -> Dict[str, Any]:
        """Run unittest."""
        args = []
        
        if suite:
            args.append(suite)
        else:
            args.append("discover")
            args.extend(["-s", "tests"])
        
        result = await self.run_command("python3", ["-m", "unittest"] + args, cwd=path)
        
        # Parse unittest output
        summary = self._parse_unittest_output(result.get("stdout", ""))
        
        return {
            "framework": "unittest",
            "summary": summary,
            "raw_output": result.get("stdout", ""),
            "exit_code": result.get("exit_code", 0)
        }
    
    def _parse_pytest_output(self, output: str) -> Dict[str, int]:
        """Parse pytest output to extract summary."""
        summary = {"passed": 0, "failed": 0, "skipped": 0, "total": 0}
        
        # Simple parsing
        lines = output.splitlines()
        for line in lines:
            if "passed" in line.lower():
                import re
                match = re.search(r"(\d+)\s+passed", line)
                if match:
                    summary["passed"] = int(match.group(1))
            if "failed" in line.lower():
                import re
                match = re.search(r"(\d+)\s+failed", line)
                if match:
                    summary["failed"] = int(match.group(1))
            if "skipped" in line.lower():
                import re
                match = re.search(r"(\d+)\s+skipped", line)
                if match:
                    summary["skipped"] = int(match.group(1))
        
        summary["total"] = summary["passed"] + summary["failed"] + summary["skipped"]
        
        return summary
    
    def _parse_unittest_output(self, output: str) -> Dict[str, int]:
        """Parse unittest output to extract summary."""
        summary = {"passed": 0, "failed": 0, "skipped": 0, "total": 0}
        
        # Simple parsing
        lines = output.splitlines()
        for line in lines:
            if "OK" in line:
                import re
                match = re.search(r"Ran\s+(\d+)\s+test", line)
                if match:
                    summary["total"] = int(match.group(1))
                    summary["passed"] = summary["total"]
            if "FAILED" in line:
                import re
                match = re.search(r"failures=(\d+)", line)
                if match:
                    summary["failed"] = int(match.group(1))
        
        return summary
    
    def _is_command_allowed(self, command: str) -> bool:
        """Check if command is allowed."""
        if not self.allowed_commands:
            return True  # No restrictions
        
        # Check if command is in allowed list
        base_command = command.split()[0] if " " in command else command
        return base_command in self.allowed_commands
    
    def _filter_env(self, env: Dict[str, str]) -> Dict[str, str]:
        """Filter environment variables."""
        # Keep only safe environment variables
        safe_vars = {
            "PATH", "HOME", "USER", "SHELL", "LANG", "LC_ALL",
            "PYTHONPATH", "VIRTUAL_ENV"
        }
        
        filtered = {k: v for k, v in env.items() if k in safe_vars}
        
        return filtered

