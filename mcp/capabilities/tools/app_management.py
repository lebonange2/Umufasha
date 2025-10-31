"""Application management tools for MCP."""
import asyncio
import subprocess
import os
import signal
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from mcp.capabilities.tools.base import FunctionTool
from mcp.core.concurrency import CancellationToken


# Global process tracking
_web_app_process: Optional[subprocess.Popen] = None


async def start_web_application_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Start the web application."""
    global _web_app_process
    
    if cancellation_token:
        cancellation_token.check()
    
    # Check if already running
    if _web_app_process and _web_app_process.poll() is None:
        return {
            "status": "already_running",
            "pid": _web_app_process.pid,
            "message": "Web application is already running"
        }
    
    # Check if port 8000 is in use
    if PSUTIL_AVAILABLE:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    conns = proc.info.get('connections') or []
                    for conn in conns:
                        if conn.laddr.port == 8000:
                            return {
                                "status": "port_in_use",
                                "pid": proc.info['pid'],
                                "message": f"Port 8000 is already in use by process {proc.info['pid']}"
                            }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
    else:
        # Fallback: Try using lsof command
        try:
            result = subprocess.run(
                ["lsof", "-ti", ":8000"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip()
                return {
                    "status": "port_in_use",
                    "pid": int(pid),
                    "message": f"Port 8000 is already in use by process {pid}",
                    "note": "Install psutil for better process management"
                }
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
    
    # Get project root (go up from mcp/capabilities/tools/ -> ASSISTANT/)
    # Path: mcp/capabilities/tools/app_management.py -> ASSISTANT/
    # .parent = tools/, .parent.parent = capabilities/, .parent.parent.parent = mcp/, .parent.parent.parent.parent = ASSISTANT/
    project_root = Path(__file__).parent.parent.parent.parent
    venv_python = project_root / "venv" / "bin" / "python3"
    
    # Use system python if venv doesn't exist
    if not venv_python.exists():
        python_cmd = "python3"
    else:
        python_cmd = str(venv_python)
    
    try:
        # Start the web application
        env = os.environ.copy()
        # Add project root to PYTHONPATH
        current_pythonpath = env.get('PYTHONPATH', '')
        project_root_str = str(project_root)
        if current_pythonpath:
            env['PYTHONPATH'] = f"{project_root_str}:{current_pythonpath}"
        else:
            env['PYTHONPATH'] = project_root_str
        
        # Create log files for the subprocess
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        stdout_file = log_dir / "webapp_stdout.log"
        stderr_file = log_dir / "webapp_stderr.log"
        
        stdout_fd = open(stdout_file, "a")
        stderr_fd = open(stderr_file, "a")
        
        # Write startup info to logs
        stdout_fd.write(f"\n=== Starting web application at {datetime.now().isoformat()} ===\n")
        stdout_fd.write(f"Command: {python_cmd} -m uvicorn app.main:app --host 0.0.0.0 --port 8000\n")
        stdout_fd.write(f"Working directory: {project_root}\n")
        stdout_fd.write(f"PYTHONPATH: {env.get('PYTHONPATH', 'not set')}\n")
        stdout_fd.flush()
        
        _web_app_process = subprocess.Popen(
            [python_cmd, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=str(project_root),
            env=env,
            stdout=stdout_fd,
            stderr=stderr_fd,
            start_new_session=True
        )
        
        # Write PID to log
        stdout_fd.write(f"Started process with PID: {_web_app_process.pid}\n")
        stdout_fd.flush()
        
        # Wait a moment to check if it started successfully
        await asyncio.sleep(3)
        
        # Check if process is still running
        if _web_app_process.poll() is None:
            # Process is still running - verify it's actually working
            import httpx
            
            # Try multiple times with increasing delays
            for attempt in range(5):
                await asyncio.sleep(1)
                try:
                    async with httpx.AsyncClient(timeout=3.0) as client:
                        response = await client.get("http://localhost:8000/health")
                        if response.status_code == 200:
                            return {
                                "status": "started",
                                "pid": _web_app_process.pid,
                                "url": "http://localhost:8000",
                                "admin_url": "http://localhost:8000/admin",
                                "api_docs": "http://localhost:8000/docs",
                                "log_files": {
                                    "stdout": str(stdout_file),
                                    "stderr": str(stderr_file)
                                },
                                "message": "Web application started successfully"
                            }
                except Exception:
                    # Check if process is still running
                    if _web_app_process.poll() is not None:
                        # Process died - read error logs
                        try:
                            if stderr_file.exists():
                                stderr = stderr_file.read_text()[-2000:]
                            else:
                                stderr = "Process exited but no error log found"
                        except Exception:
                            stderr = "Failed to read error log"
                        
                        return {
                            "status": "failed",
                            "pid": _web_app_process.pid,
                            "error": stderr,
                            "exit_code": _web_app_process.returncode,
                            "log_files": {
                                "stdout": str(stdout_file),
                                "stderr": str(stderr_file)
                            },
                            "message": "Process started but exited - check error log"
                        }
                    # Continue waiting
                    continue
            
            # Process running but not responding after 5 attempts
            # Check if it's actually running
            try:
                # Verify process exists
                os.kill(_web_app_process.pid, 0)  # Signal 0 checks if process exists
                return {
                    "status": "running",
                    "pid": _web_app_process.pid,
                    "url": "http://localhost:8000",
                    "admin_url": "http://localhost:8000/admin",
                    "api_docs": "http://localhost:8000/docs",
                    "log_files": {
                        "stdout": str(stdout_file),
                        "stderr": str(stderr_file)
                    },
                    "warning": "Process is running but not responding to health checks yet",
                    "message": "Web application is running (may need more time to start)"
                }
            except ProcessLookupError:
                # Process doesn't exist
                return {
                    "status": "failed",
                    "error": "Process exited unexpectedly",
                    "log_files": {
                        "stdout": str(stdout_file),
                        "stderr": str(stderr_file)
                    },
                    "message": "Check log files for details"
                }
        else:
            # Process exited - read error from log files
            stderr = ""
            stdout = ""
            
            try:
                if stderr_file.exists():
                    stderr = stderr_file.read_text()[-2000:]  # Last 2000 chars
            except Exception:
                pass
            
            try:
                if stdout_file.exists():
                    stdout = stdout_file.read_text()[-2000:]  # Last 2000 chars
            except Exception:
                pass
            
            return {
                "status": "failed",
                "error": stderr or "Process exited immediately",
                "stdout": stdout[:500] if stdout else None,  # Limit output
                "exit_code": _web_app_process.returncode,
                "log_files": {
                    "stdout": str(stdout_file),
                    "stderr": str(stderr_file)
                },
                "message": "Failed to start web application - check log files"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Error starting web application: {e}"
        }


async def stop_web_application_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Stop the web application."""
    global _web_app_process
    
    if cancellation_token:
        cancellation_token.check()
    
    stopped_pids = []
    
    # Stop our tracked process
    if _web_app_process and _web_app_process.poll() is None:
        try:
            _web_app_process.terminate()
            try:
                _web_app_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _web_app_process.kill()
            stopped_pids.append(_web_app_process.pid)
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Error stopping process: {e}"
            }
    
    # Also try to stop any uvicorn process on port 8000
    if PSUTIL_AVAILABLE:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    if 'uvicorn' in proc.info.get('name', '').lower():
                        conns = proc.info.get('connections') or []
                        for conn in conns:
                            if conn.laddr.port == 8000:
                                proc.terminate()
                                try:
                                    proc.wait(timeout=5)
                                except psutil.TimeoutExpired:
                                    proc.kill()
                                stopped_pids.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
    else:
        # Fallback: Use pkill or kill processes on port 8000
        try:
            # Try pkill uvicorn
            subprocess.run(["pkill", "-f", "uvicorn"], timeout=2, capture_output=True)
            # Try killing processes on port 8000
            result = subprocess.run(
                ["lsof", "-ti", ":8000"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                for pid_str in result.stdout.strip().split('\n'):
                    try:
                        pid = int(pid_str)
                        os.kill(pid, signal.SIGTERM)
                        stopped_pids.append(pid)
                    except (ValueError, ProcessLookupError, PermissionError):
                        pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    
    _web_app_process = None
    
    if stopped_pids:
        return {
            "status": "stopped",
            "stopped_pids": stopped_pids,
            "message": f"Stopped {len(stopped_pids)} process(es)"
        }
    else:
        return {
            "status": "not_running",
            "message": "Web application was not running"
        }


async def web_application_status_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Get web application status."""
    global _web_app_process
    
    if cancellation_token:
        cancellation_token.check()
    
    # Check our tracked process
    our_process_running = _web_app_process is not None and _web_app_process.poll() is None
    
    # Check port 8000
    port_in_use = False
    port_pids = []
    if PSUTIL_AVAILABLE:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    conns = proc.info.get('connections') or []
                    for conn in conns:
                        if conn.laddr.port == 8000:
                            port_in_use = True
                            port_pids.append({
                                "pid": proc.info['pid'],
                                "name": proc.info.get('name', 'unknown')
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
    else:
        # Fallback: Use lsof or netstat
        try:
            result = subprocess.run(
                ["lsof", "-ti", ":8000"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                port_in_use = True
                for pid_str in result.stdout.strip().split('\n'):
                    try:
                        pid = int(pid_str)
                        port_pids.append({
                            "pid": pid,
                            "name": "unknown"
                        })
                    except ValueError:
                        pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    
    # Try to check if web app is responding
    is_responding = False
    if port_in_use:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    is_responding = True
        except Exception:
            pass
    
    status = "running" if (port_in_use and is_responding) else "stopped"
    
    return {
        "status": status,
        "port_8000_in_use": port_in_use,
        "is_responding": is_responding,
        "processes": port_pids,
        "our_process_running": our_process_running,
        "urls": {
            "main": "http://localhost:8000",
            "admin": "http://localhost:8000/admin",
            "api_docs": "http://localhost:8000/docs",
            "health": "http://localhost:8000/health"
        }
    }


# Export tools
START_WEB_APP_TOOL = FunctionTool(
    name="startWebApplication",
    description="Start the web application on port 8000",
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    handler=start_web_application_tool
)

STOP_WEB_APP_TOOL = FunctionTool(
    name="stopWebApplication",
    description="Stop the web application",
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    handler=stop_web_application_tool
)

WEB_APP_STATUS_TOOL = FunctionTool(
    name="webApplicationStatus",
    description="Get the status of the web application (running, stopped, etc.)",
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    handler=web_application_status_tool
)

