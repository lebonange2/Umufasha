"""WebSocket transport for MCP."""
import json
from typing import Optional, Any, Union, AsyncIterator
import structlog

try:
    from websockets.server import serve as ws_serve
    from websockets.exceptions import ConnectionClosed, WebSocketException
    from websockets.legacy.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = None  # type: ignore

from mcp.core.protocol.messages import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    parse_message,
    serialize_message
)

logger = structlog.get_logger(__name__)


class WebSocketTransport:
    """WebSocket transport for MCP."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        path: str = "/mcp",
        router: Optional[Any] = None
    ):
        """Initialize WebSocket transport.
        
        Args:
            host: Bind host
            port: Bind port
            path: WebSocket path
            router: Optional router for handling messages
        """
        if not WEBSOCKETS_AVAILABLE:
            raise RuntimeError(
                "websockets library not available. Install with: pip install websockets"
            )
        
        self.host = host
        self.port = port
        self.path = path
        self.router = router
        self.server: Optional[Any] = None
        self.websocket: Optional[WebSocketServerProtocol] = None
        self._shutdown = False
    
    async def connect(self):
        """Start WebSocket server."""
        self.server = await ws_serve(
            self._handle_client,
            self.host,
            self.port
        )
        logger.info(
            "WebSocket transport listening",
            host=self.host,
            port=self.port,
            path=self.path
        )
    
    async def disconnect(self):
        """Stop WebSocket server."""
        self._shutdown = True
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("WebSocket transport disconnected")
    
    async def _handle_client(
        self,
        websocket: WebSocketServerProtocol,
        path: str
    ):
        """Handle WebSocket client connection."""
        if path != self.path:
            logger.warn("Invalid path", path=path, expected=self.path)
            await websocket.close(code=4004, reason="Invalid path")
            return
        
        logger.info("WebSocket client connected", remote=websocket.remote_address)
        self.websocket = websocket
        
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                
                try:
                    mcp_message = parse_message(message)
                    
                    # Process message with router if available
                    if self.router:
                        if isinstance(mcp_message, JSONRPCRequest):
                            response = await self.router.handle_request(mcp_message)
                            await self.send_message(response)
                        elif isinstance(mcp_message, JSONRPCNotification):
                            await self.router.handle_notification(mcp_message)
                    else:
                        # Router will be set later, just log
                        logger.debug("Router not set, message queued", message=mcp_message.method)
                        
                except Exception as e:
                    logger.error("Error parsing message", error=str(e))
                    error_response = JSONRPCResponse.error_response(
                        None,
                        -32700,
                        "Parse error",
                        {"error": str(e)}
                    )
                    await self.send_message(error_response)
        
        except ConnectionClosed:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error("WebSocket error", error=str(e))
        finally:
            self.websocket = None
    
    async def send_message(
        self,
        message: JSONRPCResponse | JSONRPCNotification
    ):
        """Send a message."""
        if not self.websocket:
            raise RuntimeError("No WebSocket connection")
        
        data = serialize_message(message)
        await self.websocket.send(data)
    
    async def receive_message(
        self
    ) -> Optional[Union[JSONRPCRequest, JSONRPCNotification]]:
        """Receive a message (not used in handler pattern)."""
        raise NotImplementedError("Use iterate_messages in handler pattern")
    
    async def iterate_messages(
        self,
        websocket: WebSocketServerProtocol
    ) -> AsyncIterator[Union[JSONRPCRequest, JSONRPCNotification]]:
        """Iterate over incoming messages."""
        async for message in websocket:
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            
            try:
                mcp_message = parse_message(message)
                yield mcp_message
            except Exception as e:
                logger.error("Error parsing message", error=str(e))
                await self.send_error(
                    None,
                    -32700,
                    "Parse error",
                    {"error": str(e)}
                )
    
    async def send_error(
        self,
        request_id: Optional[Union[str, int]],
        code: int,
        message: str,
        data: Optional[dict] = None
    ):
        """Send error response."""
        error = JSONRPCResponse.error_response(request_id, code, message, data)
        await self.send_message(error)

