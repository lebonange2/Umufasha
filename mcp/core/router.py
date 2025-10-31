"""MCP request router."""
from typing import Dict, Callable, Any, Optional, List
import asyncio
import structlog
import uuid

from mcp.core.protocol.messages import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    JSONRPCErrorCode
)
from mcp.core.errors import MCPMethodNotFoundError, MCPServerError
from mcp.core.concurrency import RequestTracker, TimeoutManager, CancellationToken

logger = structlog.get_logger(__name__)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    Handler = Callable[[Dict[str, Any], Optional[CancellationToken]], Any]
    Middleware = Callable[[JSONRPCRequest, Handler], Any]
else:
    Handler = Callable
    Middleware = Callable


class Router:
    """MCP request router with middleware support."""
    
    def __init__(
        self,
        max_concurrent: int = 32,
        default_timeout: float = 30.0
    ):
        """Initialize router.
        
        Args:
            max_concurrent: Maximum concurrent requests
            default_timeout: Default request timeout in seconds
        """
        self.handlers: Dict[str, Handler] = {}
        self.middleware: List[Middleware] = []
        self.request_tracker = RequestTracker(max_concurrent)
        self.timeout_manager = TimeoutManager(default_timeout)
        self._shutdown = False
    
    def register(self, method: str, handler: Handler):
        """Register a method handler.
        
        Args:
            method: Method name (e.g., "tools/call")
            handler: Async handler function
        """
        if method in self.handlers:
            logger.warn("Handler already registered", method=method)
        self.handlers[method] = handler
        logger.debug("Registered handler", method=method)
    
    def add_middleware(self, middleware: Middleware):
        """Add middleware.
        
        Args:
            middleware: Middleware function
        """
        self.middleware.append(middleware)
    
    async def handle_request(
        self,
        request: JSONRPCRequest
    ) -> JSONRPCResponse:
        """Handle a JSON-RPC request.
        
        Args:
            request: JSON-RPC request
            
        Returns:
            JSON-RPC response
        """
        if self._shutdown:
            return JSONRPCResponse.error_response(
                request.id,
                JSONRPCErrorCode.SERVER_ERROR,
                "Server is shutting down"
            )
        
        # Validate request
        error = request.validate()
        if error:
            return JSONRPCResponse.error_response(
                request.id,
                error.code,
                error.message,
                error.data
            )
        
        # Generate request ID if missing
        if request.id is None:
            request.id = str(uuid.uuid4())
        
        request_id = str(request.id) if isinstance(request.id, (str, int)) else str(uuid.uuid4())
        
        # Acquire request slot
        try:
            cancellation_token = await self.request_tracker.acquire(request_id)
        except asyncio.QueueFull:
            return JSONRPCResponse.error_response(
                request.id,
                JSONRPCErrorCode.SERVER_ERROR,
                "Server is at capacity",
                {"active_requests": self.request_tracker.active_count()}
            )
        
        try:
            # Check if method exists
            if request.method not in self.handlers:
                raise MCPMethodNotFoundError(request.method)
            
            handler = self.handlers[request.method]
            
            # Build middleware chain
            async def execute_handler():
                params = request.params or {}
                
                # Build handler chain
                async def call_handler(p, tok):
                    return await handler(p, tok)
                
                # Apply middleware in reverse order (last registered runs first)
                current_handler = call_handler
                for middleware_func in reversed(self.middleware):
                    mw = middleware_func
                    h = current_handler
                    async def wrapped_handler(p, tok, m=mw, next_h=h):
                        return await m(request, next_h)
                    current_handler = wrapped_handler
                
                return await current_handler(params, cancellation_token)
            
            # Execute with timeout
            result = await self.timeout_manager.execute_with_timeout(
                execute_handler,
                cancellation_token=cancellation_token
            )
            
            return JSONRPCResponse.success(request.id, result)
        
        except MCPMethodNotFoundError as e:
            return JSONRPCResponse.error_response(
                request.id,
                e.code,
                e.message,
                e.data
            )
        except MCPServerError as e:
            return JSONRPCResponse.error_response(
                request.id,
                e.code,
                e.message,
                e.data
            )
        except Exception as e:
            logger.error(
                "Handler error",
                method=request.method,
                error=str(e),
                exc_info=True
            )
            return JSONRPCResponse.error_response(
                request.id,
                JSONRPCErrorCode.INTERNAL_ERROR,
                f"Internal error: {str(e)}"
            )
        finally:
            self.request_tracker.release(request_id)
    
    async def handle_notification(
        self,
        notification: JSONRPCNotification
    ):
        """Handle a JSON-RPC notification (no response).
        
        Args:
            notification: JSON-RPC notification
        """
        error = notification.validate()
        if error:
            logger.warn("Invalid notification", error=error.message)
            return
        
        if notification.method not in self.handlers:
            logger.warn("Unknown notification method", method=notification.method)
            return
        
        handler = self.handlers[notification.method]
        params = notification.params or {}
        
        try:
            await handler(params, None)
        except Exception as e:
            logger.error(
                "Notification handler error",
                method=notification.method,
                error=str(e),
                exc_info=True
            )
    
    def cancel_request(self, request_id: str) -> bool:
        """Cancel a request.
        
        Args:
            request_id: Request ID to cancel
            
        Returns:
            True if request was cancelled, False if not found
        """
        return self.request_tracker.cancel(request_id)
    
    async def shutdown(self):
        """Shutdown router and wait for in-flight requests."""
        self._shutdown = True
        # Wait for active requests to complete (with timeout)
        max_wait = 30.0
        start = asyncio.get_event_loop().time()
        while self.request_tracker.active_count() > 0:
            await asyncio.sleep(0.1)
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed > max_wait:
                logger.warn("Shutdown timeout, forcing close")
                break
        logger.info("Router shutdown complete")

