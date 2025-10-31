"""Stdio transport for MCP."""
import asyncio
import sys
from typing import AsyncIterator, Optional, Callable, Any, Union
import structlog

from mcp.core.protocol.messages import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    parse_message,
    serialize_message
)

logger = structlog.get_logger(__name__)


class StdioTransport:
    """Stdio transport for MCP (newline-delimited JSON)."""
    
    def __init__(
        self,
        stdin: Optional[Any] = None,
        stdout: Optional[Any] = None
    ):
        """Initialize stdio transport.
        
        Args:
            stdin: Input stream (defaults to sys.stdin)
            stdout: Output stream (defaults to sys.stdout)
        """
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._shutdown = False
    
    async def connect(self):
        """Connect the transport."""
        # Create stream reader/writer for stdin/stdout
        loop = asyncio.get_event_loop()
        
        # Create streams from file descriptors
        self.reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(self.reader)
        
        # Attach to stdin/stdout file descriptors
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        # Create writer for stdout
        transport, protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin,
            sys.stdout
        )
        self.writer = asyncio.StreamWriter(
            transport,
            protocol,
            None,
            loop
        )
        
        logger.info("Stdio transport connected")
    
    async def disconnect(self):
        """Disconnect the transport."""
        self._shutdown = True
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except NotImplementedError:
                # wait_closed() may not be implemented for all stream types
                # Just close and continue
                pass
            except Exception as e:
                logger.debug("Error waiting for writer to close", error=str(e))
        logger.info("Stdio transport disconnected")
    
    async def send_message(
        self,
        message: JSONRPCResponse | JSONRPCNotification
    ):
        """Send a message."""
        if self._shutdown or not self.writer:
            raise RuntimeError("Transport not connected")
        
        data = serialize_message(message)
        self.writer.write((data + "\n").encode("utf-8"))
        await self.writer.drain()
    
    async def receive_message(
        self
    ) -> Optional[Union[JSONRPCRequest, JSONRPCNotification]]:
        """Receive a message."""
        if self._shutdown or not self.reader:
            raise RuntimeError("Transport not connected")
        
        try:
            # Read line (newline-delimited JSON)
            line = await asyncio.wait_for(
                self.reader.readline(),
                timeout=60.0
            )
            
            if not line:
                # EOF
                return None
            
            line_str = line.decode("utf-8").rstrip("\n\r")
            if not line_str:
                # Empty line, skip
                return await self.receive_message()
            
            message = parse_message(line_str)
            return message
            
        except asyncio.TimeoutError:
            logger.warn("Read timeout on stdio")
            return None
        except Exception as e:
            logger.error("Error receiving message", error=str(e))
            raise
    
    async def iterate_messages(
        self
    ) -> AsyncIterator[Union[JSONRPCRequest, JSONRPCNotification]]:
        """Iterate over incoming messages."""
        while not self._shutdown:
            message = await self.receive_message()
            if message is None:
                break
            yield message

