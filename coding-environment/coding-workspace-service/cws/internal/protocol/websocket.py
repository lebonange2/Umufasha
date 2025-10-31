"""WebSocket transport for CWS."""
import asyncio
import json
from typing import Optional, Any
import structlog

try:
    from websockets.server import serve as ws_serve
    from websockets.exceptions import ConnectionClosed, WebSocketException
    from websockets.legacy.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = None  # type: ignore

from cws.internal.protocol.messages import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    parse_message,
    serialize_message
)

logger = structlog.get_logger(__name__)


class WebSocketTransport:
    """WebSocket transport for CWS."""
    
    def __init__(self, server, host: str = "localhost", port: int = 9090):
        """Initialize WebSocket transport."""
        if not WEBSOCKETS_AVAILABLE:
            raise RuntimeError("websockets library not available")
        
        self.server = server
        self.host = host
        self.port = port
        self.server_obj: Optional[Any] = None
        self._shutdown = False
    
    async def run(self):
        """Run WebSocket server."""
        async def handle_client(websocket: WebSocketServerProtocol, path: str):
            logger.info("Client connected", path=path)
            try:
                async for message in websocket:
                    try:
                        mcp_message = parse_message(message)
                        if isinstance(mcp_message, JSONRPCRequest):
                            response = await self.server.handle_request(mcp_message)
                            await websocket.send(serialize_message(response))
                        elif isinstance(mcp_message, JSONRPCNotification):
                            logger.debug("Received notification", method=mcp_message.method)
                    except Exception as e:
                        logger.error("Error processing message", error=str(e), exc_info=True)
            except ConnectionClosed:
                logger.info("Client disconnected")
            except Exception as e:
                logger.error("Connection handler error", error=str(e), exc_info=True)
        
        self.server_obj = await ws_serve(handle_client, self.host, self.port)
        logger.info("WebSocket transport listening", host=self.host, port=self.port)
        
        try:
            while not self._shutdown:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            await self.disconnect()
    
    async def disconnect(self):
        """Disconnect transport."""
        self._shutdown = True
        if self.server_obj:
            self.server_obj.close()
            await self.server_obj.wait_closed()
        logger.info("WebSocket transport disconnected")

