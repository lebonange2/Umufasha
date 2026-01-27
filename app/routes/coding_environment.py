"""Coding Environment API routes."""
import os
import subprocess
import psutil
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()

# Paths
ASSISTANT_DIR = Path(__file__).parent.parent.parent
CODING_ENV_DIR = ASSISTANT_DIR / "coding-environment"
CWS_DIR = CODING_ENV_DIR / "coding-workspace-service"
MCP_DIR = ASSISTANT_DIR / "mcp"
VENV_DIR = CODING_ENV_DIR / "venv"
PIDS_DIR = CODING_ENV_DIR / ".pids"

# Default ports
MCP_PORT = int(os.environ.get("MCP_PORT", "8080"))
CWS_PORT = int(os.environ.get("CWS_PORT", "9090"))

# Detect RunPod environment
IS_RUNPOD = bool(
    os.environ.get("RUNPOD_POD_ID") or 
    Path("/workspace").exists() or 
    Path("/runpod-volume").exists()
)
BIND_HOST = "0.0.0.0" if IS_RUNPOD else "localhost"

# IMPORTANT:
# BIND_HOST is used for *binding* services (external accessibility).
# When proxying *to* a local service from within the same host/container,
# we must connect to localhost/127.0.0.1. Using 0.0.0.0 as a connect
# address will fail and can make the UI show "running" but "not connected".
PROXY_CONNECT_HOST = "127.0.0.1"


class ServiceStatus(BaseModel):
    """Service status model."""
    name: str
    running: bool
    pid: Optional[int] = None
    port: Optional[int] = None
    url: Optional[str] = None


class ServiceControl(BaseModel):
    """Service control model."""
    action: str  # "start" or "stop"


def get_pid_from_file(pid_file: Path) -> Optional[int]:
    """Get PID from file if process is still running."""
    if not pid_file.exists():
        return None
    
    try:
        pid = int(pid_file.read_text().strip())
        if psutil.pid_exists(pid):
            return pid
        else:
            pid_file.unlink()
            return None
    except (ValueError, OSError):
        return None


def check_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                return True
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        pass
    return False


@router.get("/models")
async def get_ollama_models():
    """Get available Ollama models."""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                models = [
                    {
                        "value": model["name"],
                        "label": f"{model['name']} (Local)",
                        "provider": "local"
                    }
                    for model in data.get("models", [])
                ]
                return {"models": models, "provider": "local"}
            else:
                return {"models": [], "provider": "local", "error": "Ollama not available"}
    except Exception as e:
        logger.warning("Failed to fetch Ollama models", error=str(e))
        # Return default models if Ollama is not available
        default_models = [
            {"value": "qwen3:30b", "label": "Qwen3 30B (Local)", "provider": "local"},
            {"value": "llama3:latest", "label": "Llama 3 Latest (Local)", "provider": "local"},
            {"value": "llama3.2:latest", "label": "Llama 3.2 (Latest)", "provider": "local"},
            {"value": "mistral:latest", "label": "Mistral (Latest)", "provider": "local"},
            {"value": "codellama:latest", "label": "CodeLlama (Latest)", "provider": "local"},
            {"value": "phi3:latest", "label": "Phi-3 (Latest)", "provider": "local"},
        ]
        return {"models": default_models, "provider": "local", "error": str(e)}


@router.get("/status")
async def get_services_status() -> Dict[str, ServiceStatus]:
    """Get status of CWS and MCP Server."""
    mcp_pid_file = PIDS_DIR / "mcp.pid"
    cws_pid_file = PIDS_DIR / "cws.pid"
    
    mcp_pid = get_pid_from_file(mcp_pid_file)
    cws_pid = get_pid_from_file(cws_pid_file)
    
    mcp_running = mcp_pid is not None or check_port_in_use(MCP_PORT)
    cws_running = cws_pid is not None or check_port_in_use(CWS_PORT)
    
    return {
        "mcp": ServiceStatus(
            name="MCP Server",
            running=mcp_running,
            pid=mcp_pid,
            port=MCP_PORT if mcp_running else None,
            url=f"ws://{BIND_HOST}:{MCP_PORT}" if mcp_running else None
        ),
        "cws": ServiceStatus(
            name="CWS",
            running=cws_running,
            pid=cws_pid,
            port=CWS_PORT if cws_running else None,
            url=f"ws://{BIND_HOST}:{CWS_PORT}" if cws_running else None
        )
    }


@router.post("/services/{service_name}/control")
async def control_service(service_name: str, control: ServiceControl):
    """Start or stop a service."""
    if service_name not in ["mcp", "cws"]:
        raise HTTPException(status_code=400, detail="Invalid service name. Use 'mcp' or 'cws'")
    
    if control.action == "start":
        return await start_service(service_name)
    elif control.action == "stop":
        return await stop_service(service_name)
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'start' or 'stop'")


async def start_service(service_name: str) -> Dict[str, Any]:
    """Start a service."""
    # Ensure PIDs directory exists
    PIDS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if already running
    status = await get_services_status()
    if status[service_name].running:
        return {"status": "already_running", "message": f"{service_name.upper()} is already running"}
    
    # Activate venv if it exists
    venv_python = VENV_DIR / "bin" / "python3"
    python_cmd = str(venv_python) if venv_python.exists() else "python3"
    
    try:
        if service_name == "mcp":
            # Start MCP Server
            log_file = PIDS_DIR / "mcp.log"
            cmd = [
                python_cmd, "-m", "mcp.server",
                "--transport", "websocket",
                "--host", BIND_HOST,
                "--port", str(MCP_PORT)
            ]
            process = subprocess.Popen(
                cmd,
                cwd=str(ASSISTANT_DIR),
                stdout=open(log_file, "w"),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            pid_file = PIDS_DIR / "mcp.pid"
            pid_file.write_text(str(process.pid))
            logger.info("MCP Server started", pid=process.pid, port=MCP_PORT)
            
        elif service_name == "cws":
            # Start CWS
            log_file = PIDS_DIR / "cws.log"
            workspace_root = os.environ.get("WORKSPACE_ROOT", str(ASSISTANT_DIR))
            
            # Ensure log file directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Build command - use sys.executable to ensure we use the right Python
            import sys
            python_executable = sys.executable if VENV_DIR.exists() and str(venv_python) == python_cmd else python_cmd
            
            cmd = [
                python_executable, "-m", "cws.main",
                "--transport", "websocket",
                "--host", BIND_HOST,
                "--port", str(CWS_PORT),
                "--workspace-root", workspace_root
            ]
            
            # Set up environment with PYTHONPATH
            env = os.environ.copy()
            # Add CWS directory and parent to PYTHONPATH
            pythonpath = env.get("PYTHONPATH", "")
            pythonpath_parts = [p for p in pythonpath.split(os.pathsep) if p]
            if str(CWS_DIR) not in pythonpath_parts:
                pythonpath_parts.insert(0, str(CWS_DIR))
            if str(CODING_ENV_DIR) not in pythonpath_parts:
                pythonpath_parts.insert(0, str(CODING_ENV_DIR))
            env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
            
            try:
                with open(log_file, "w") as log:
                    process = subprocess.Popen(
                        cmd,
                        cwd=str(CWS_DIR),
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                        env=env
                    )
                
                pid_file = PIDS_DIR / "cws.pid"
                pid_file.write_text(str(process.pid))
                logger.info("CWS started", pid=process.pid, port=CWS_PORT, cwd=str(CWS_DIR), cmd=" ".join(cmd))
            except Exception as e:
                error_msg = f"Failed to start CWS: {str(e)}"
                logger.error(error_msg, error=str(e), cmd=" ".join(cmd), cwd=str(CWS_DIR))
                # Read log file if it exists to get more details
                if log_file.exists():
                    try:
                        with open(log_file, "r") as f:
                            log_content = f.read()
                            if log_content:
                                error_msg += f"\nLog: {log_content[-500:]}"  # Last 500 chars
                    except:
                        pass
                raise HTTPException(status_code=500, detail=error_msg)
        
        # Wait a moment for service to start
        import asyncio
        await asyncio.sleep(2)
        
        return {
            "status": "started",
            "message": f"{service_name.upper()} started successfully",
            "pid": process.pid
        }
        
    except Exception as e:
        logger.error(f"Failed to start {service_name}", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start {service_name}: {str(e)}")


async def stop_service(service_name: str) -> Dict[str, Any]:
    """Stop a service."""
    pid_file = PIDS_DIR / f"{service_name}.pid"
    pid = get_pid_from_file(pid_file)
    
    if not pid:
        return {"status": "not_running", "message": f"{service_name.upper()} is not running"}
    
    try:
        process = psutil.Process(pid)
        process.terminate()
        
        # Wait for graceful shutdown
        try:
            process.wait(timeout=5)
        except psutil.TimeoutExpired:
            process.kill()
        
        pid_file.unlink()
        logger.info(f"{service_name.upper()} stopped", pid=pid)
        
        return {"status": "stopped", "message": f"{service_name.upper()} stopped successfully"}
        
    except psutil.NoSuchProcess:
        pid_file.unlink()
        return {"status": "not_running", "message": f"{service_name.upper()} was not running"}
    except Exception as e:
        logger.error(f"Failed to stop {service_name}", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to stop {service_name}: {str(e)}")


@router.websocket("/ws/mcp")
async def mcp_websocket_proxy(websocket: WebSocket):
    """WebSocket proxy for MCP Server."""
    await websocket.accept()
    
    try:
        import websockets
    except ImportError:
        await websocket.send_json({
            "error": "websockets library not available. Install with: pip install websockets"
        })
        await websocket.close(code=1011, reason="websockets not available")
        return
    
    mcp_url = f"ws://{PROXY_CONNECT_HOST}:{MCP_PORT}"
    
    try:
        async with websockets.connect(mcp_url) as mcp_ws:
            # Forward messages bidirectionally
            async def forward_to_mcp():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await mcp_ws.send(data)
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    logger.error("Error forwarding to MCP", error=str(e))
            
            async def forward_from_mcp():
                try:
                    while True:
                        data = await mcp_ws.recv()
                        await websocket.send_text(data)
                except websockets.exceptions.ConnectionClosed:
                    pass
                except Exception as e:
                    logger.error("Error forwarding from MCP", error=str(e))
            
            import asyncio
            await asyncio.gather(
                forward_to_mcp(),
                forward_from_mcp(),
                return_exceptions=True
            )
    except Exception as e:
        logger.error("MCP WebSocket proxy error", error=str(e))
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


@router.websocket("/ws/cws")
async def cws_websocket_proxy(websocket: WebSocket):
    """WebSocket proxy for CWS."""
    await websocket.accept()
    logger.info("CWS WebSocket proxy: Client connected")
    
    try:
        import websockets
    except ImportError:
        error_msg = "websockets library not available. Install with: pip install websockets"
        logger.error(error_msg)
        try:
            await websocket.send_json({"error": error_msg})
            await websocket.close(code=1011, reason="websockets not available")
        except:
            pass
        return
    
    # Check if CWS is actually running
    status = await get_services_status()
    if not status["cws"].running:
        error_msg = "CWS service is not running"
        logger.error(error_msg)
        try:
            await websocket.send_json({"error": error_msg})
            await websocket.close(code=1008, reason=error_msg)
        except:
            pass
        return
    
    cws_url = f"ws://{PROXY_CONNECT_HOST}:{CWS_PORT}"
    logger.info("CWS WebSocket proxy: Connecting to CWS", url=cws_url)
    
    try:
        # Add connection timeout
        async with websockets.connect(cws_url, ping_interval=None, ping_timeout=None) as cws_ws:
            logger.info("CWS WebSocket proxy: Connected to CWS successfully")
            
            # Send initial message to verify connection
            try:
                await websocket.send_text('{"jsonrpc":"2.0","method":"ping"}')
            except:
                pass
            
            # Forward messages bidirectionally
            async def forward_to_cws():
                try:
                    while True:
                        try:
                            data = await websocket.receive_text()
                            logger.debug("CWS proxy: Forwarding to CWS", data_length=len(data))
                            await cws_ws.send(data)
                        except WebSocketDisconnect:
                            logger.info("CWS proxy: Client disconnected")
                            break
                        except Exception as e:
                            logger.error("CWS proxy: Error forwarding to CWS", error=str(e))
                            break
                except Exception as e:
                    logger.error("CWS proxy: Forward to CWS loop error", error=str(e))
            
            async def forward_from_cws():
                try:
                    while True:
                        try:
                            data = await cws_ws.recv()
                            logger.debug("CWS proxy: Forwarding from CWS", data_length=len(str(data)))
                            await websocket.send_text(data)
                        except websockets.exceptions.ConnectionClosed:
                            logger.info("CWS proxy: CWS connection closed")
                            break
                        except Exception as e:
                            logger.error("CWS proxy: Error forwarding from CWS", error=str(e))
                            break
                except Exception as e:
                    logger.error("CWS proxy: Forward from CWS loop error", error=str(e))
            
            import asyncio
            try:
                await asyncio.gather(
                    forward_to_cws(),
                    forward_from_cws(),
                    return_exceptions=True
                )
            except Exception as e:
                logger.error("CWS proxy: Gather error", error=str(e))
    except websockets.exceptions.InvalidURI as e:
        error_msg = f"Invalid CWS URL: {cws_url}"
        logger.error(error_msg, error=str(e))
        try:
            await websocket.send_json({"error": error_msg})
            await websocket.close(code=1002, reason=error_msg)
        except:
            pass
    except websockets.exceptions.InvalidStatusCode as e:
        error_msg = f"CWS connection refused: {cws_url}"
        logger.error(error_msg, error=str(e), status_code=e.status_code)
        try:
            await websocket.send_json({"error": error_msg, "status_code": e.status_code})
            await websocket.close(code=1006, reason=error_msg)
        except:
            pass
    except Exception as e:
        error_msg = f"CWS WebSocket proxy error: {str(e)}"
        logger.error(error_msg, error=str(e), exc_info=True)
        try:
            await websocket.send_json({"error": error_msg})
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
