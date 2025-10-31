"""Stdio transport for CWS."""
import asyncio
import sys
from typing import Optional
import structlog

from cws.internal.protocol.messages import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    parse_message,
    serialize_message
)

logger = structlog.get_logger(__name__)


class StdioTransport:
    """Stdio transport for CWS."""
    
    def __init__(self, server):
        """Initialize stdio transport."""
        self.server = server
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._shutdown = False
    
    async def run(self):
        """Run transport."""
        loop = asyncio.get_event_loop()
        
        self.reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(self.reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        self.writer = asyncio.StreamWriter(
            sys.stdout.buffer,
            protocol=None,
            reader=None,
            loop=loop
        )
        
        logger.info("Stdio transport connected")
        
        try:
            while not self._shutdown:
                line = await self.reader.readline()
                if not line:
                    break
                
                line_str = line.decode("utf-8").rstrip("\n\r")
                if not line_str:
                    continue
                
                try:
                    message = parse_message(line_str)
                    if isinstance(message, JSONRPCRequest):
                        response = await self.server.handle_request(message)
                        self.writer.write((serialize_message(response) + "\n").encode("utf-8"))
                        await self.writer.drain()
                    elif isinstance(message, JSONRPCNotification):
                        # Handle notification
                        logger.debug("Received notification", method=message.method)
                except Exception as e:
                    logger.error("Error processing message", error=str(e), exc_info=True)
        except EOFError:
            logger.info("EOF received, shutting down")
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            await self.disconnect()
    
    async def disconnect(self):
        """Disconnect transport."""
        self._shutdown = True
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except (NotImplementedError, Exception):
                pass
        logger.info("Stdio transport disconnected")

