"""CWS server implementation."""
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import structlog
import json

from cws.internal.protocol.messages import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    JSONRPCError,
    JSONRPCErrorCode,
    parse_message,
    serialize_message
)
from cws.internal.policy.loader import load_policy, Policy
from cws.internal.fs.operations import FileOperations
from cws.internal.search.operations import SearchOperations
from cws.internal.edits.operations import EditOperations
from cws.internal.tasks.operations import TaskOperations

logger = structlog.get_logger(__name__)


class CWSServer:
    """Coding Workspace Service server."""
    
    def __init__(self, workspace_root: Optional[str] = None):
        """Initialize CWS server."""
        if workspace_root:
            self.workspace_root = Path(workspace_root).resolve()
        else:
            self.workspace_root = Path.cwd().resolve()
        
        # Load policy
        self.policy = load_policy(self.workspace_root)
        
        # Initialize operations
        self.fs = FileOperations(self.workspace_root, self.policy)
        self.search = SearchOperations(self.workspace_root, self.policy)
        self.edits = EditOperations(self.workspace_root, self.policy)
        self.tasks = TaskOperations(self.workspace_root, self.policy)
        
        # Request handlers
        self.handlers = {
            # File operations
            "fs.read": self._handle_fs_read,
            "fs.write": self._handle_fs_write,
            "fs.create": self._handle_fs_create,
            "fs.delete": self._handle_fs_delete,
            "fs.move": self._handle_fs_move,
            "fs.list": self._handle_fs_list,
            # Search operations
            "search.find": self._handle_search_find,
            "code.symbols": self._handle_code_symbols,
            # Edit operations
            "code.batchEdit": self._handle_code_batch_edit,
            "code.format": self._handle_code_format,
            "fs.diff": self._handle_fs_diff,
            "fs.applyPatch": self._handle_fs_apply_patch,
            # Task operations
            "task.run": self._handle_task_run,
            "task.build": self._handle_task_build,
            "task.test": self._handle_task_test,
            "terminal.create": self._handle_terminal_create,
            "terminal.send": self._handle_terminal_send,
            "terminal.dispose": self._handle_terminal_dispose,
            # Introspection
            "initialize": self._handle_initialize,
            "capabilities": self._handle_capabilities,
        }
    
    async def handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Handle JSON-RPC request."""
        try:
            handler = self.handlers.get(request.method)
            if not handler:
                return JSONRPCResponse(
                    id=request.id,
                    error=JSONRPCError(
                        code=JSONRPCErrorCode.METHOD_NOT_FOUND,
                        message=f"Method not found: {request.method}"
                    )
                )
            
            # Call handler
            result = await handler(request.params or {})
            
            return JSONRPCResponse(
                id=request.id,
                result=result
            )
        except ValueError as e:
            # Policy violation or invalid params
            return JSONRPCResponse(
                id=request.id,
                error=JSONRPCError(
                    code=JSONRPCErrorCode.INVALID_PARAMS,
                    message=str(e)
                )
            )
        except Exception as e:
            logger.error("Request handler error", method=request.method, error=str(e), exc_info=True)
            return JSONRPCResponse(
                id=request.id,
                error=JSONRPCError(
                    code=JSONRPCErrorCode.INTERNAL_ERROR,
                    message=f"Internal error: {str(e)}"
                )
            )
    
    async def shutdown(self):
        """Shutdown server."""
        # Cleanup terminals
        for terminal_id in list(self.tasks.terminals.keys()):
            try:
                await self.tasks.dispose_terminal(terminal_id)
            except:
                pass
    
    # File operation handlers
    async def _handle_fs_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.fs.read(params["path"])
    
    async def _handle_fs_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.fs.write(
            params["path"],
            params["contents"],
            params.get("options")
        )
    
    async def _handle_fs_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.fs.create(
            params["path"],
            params["type"],
            params.get("options")
        )
    
    async def _handle_fs_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.fs.delete(
            params["path"],
            params.get("options")
        )
    
    async def _handle_fs_move(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.fs.move(
            params["src"],
            params["dst"],
            params.get("options")
        )
    
    async def _handle_fs_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.fs.list(
            params.get("path", "."),
            params.get("options")
        )
    
    # Search operation handlers
    async def _handle_search_find(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.search.find(
            params["query"],
            params.get("options")
        )
    
    async def _handle_code_symbols(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.search.symbols(
            params["scope"],
            params.get("query")
        )
    
    # Edit operation handlers
    async def _handle_code_batch_edit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.edits.batch_edit(
            params["edits"],
            params.get("options")
        )
    
    async def _handle_code_format(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Simplified formatting - would use proper formatters
        path = params["path"]
        file_path = self.workspace_root / path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        content = file_path.read_text(encoding="utf-8")
        # Basic formatting would go here
        return {"path": path, "formatted": content}
    
    async def _handle_fs_diff(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.edits.diff(
            params.get("basePath"),
            params.get("includeGlobs"),
            params.get("excludeGlobs")
        )
    
    async def _handle_fs_apply_patch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.edits.apply_patch(
            params["patch"],
            params.get("options")
        )
    
    # Task operation handlers
    async def _handle_task_run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.tasks.run(
            params["command"],
            params.get("args"),
            params.get("options")
        )
    
    async def _handle_task_build(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.tasks.build()
    
    async def _handle_task_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.tasks.test()
    
    async def _handle_terminal_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.tasks.create_terminal(
            params.get("name"),
            params.get("cwd")
        )
    
    async def _handle_terminal_send(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.tasks.send_terminal(
            params["id"],
            params["data"]
        )
    
    async def _handle_terminal_dispose(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.tasks.dispose_terminal(params["id"])
    
    # Introspection handlers
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "protocolVersion": "1.0.0",
            "capabilities": {
                "fs": True,
                "search": True,
                "edits": True,
                "tasks": True
            },
            "serverInfo": {
                "name": "coding-workspace-service",
                "version": "1.0.0"
            }
        }
    
    async def _handle_capabilities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "methods": list(self.handlers.keys()),
            "capabilities": {
                "fs": True,
                "search": True,
                "edits": True,
                "tasks": True
            }
        }

