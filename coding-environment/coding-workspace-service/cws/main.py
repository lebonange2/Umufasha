"""Coding Workspace Service main entry point."""
import asyncio
import argparse
import sys
from typing import Optional
import structlog

from cws.internal.protocol.server import CWSServer
from cws.internal.protocol.stdio import StdioTransport
from cws.internal.protocol.websocket import WebSocketTransport

logger = structlog.get_logger(__name__)


async def main_async(transport_type: str, host: str, port: int, workspace_root: Optional[str]):
    """Main async entry point."""
    # Configure logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True
    )
    
    # Create server
    server = CWSServer(workspace_root)
    
    # Create transport
    if transport_type == "stdio":
        transport = StdioTransport(server)
    elif transport_type == "websocket":
        transport = WebSocketTransport(server, host, port)
    else:
        raise ValueError(f"Unknown transport type: {transport_type}")
    
    try:
        await transport.run()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    finally:
        await server.shutdown()
        logger.info("CWS stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Coding Workspace Service")
    parser.add_argument(
        "--transport",
        choices=["stdio", "websocket"],
        default="stdio",
        help="Transport type"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="WebSocket bind host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9090,
        help="WebSocket bind port"
    )
    parser.add_argument(
        "--workspace-root",
        type=str,
        default=None,
        help="Workspace root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main_async(args.transport, args.host, args.port, args.workspace_root))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()

