"""MCP Server implementation."""
import asyncio
import argparse
import json
import signal
import sys
from typing import Dict, Any, Optional, Union
import structlog

from mcp.core.protocol.messages import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    JSONRPCErrorCode
)
from mcp.core.router import Router
from mcp.core.transport.stdio import StdioTransport
from mcp.core.transport.websocket import WebSocketTransport
from mcp.core.errors import MCPMethodNotFoundError, MCPServerError
from mcp.core.validation import SchemaValidator
from mcp.capabilities.tools.base import Tool
from mcp.capabilities.tools.assistant_tools import (
    GET_USER_TOOL,
    GET_EVENT_TOOL,
    LIST_EVENTS_TOOL,
    LIST_NOTIFICATIONS_TOOL,
    PLAN_NOTIFICATIONS_TOOL
)
from mcp.capabilities.tools.app_management import (
    START_WEB_APP_TOOL,
    STOP_WEB_APP_TOOL,
    WEB_APP_STATUS_TOOL
)
from mcp.capabilities.tools.comprehensive_tools import (
    CREATE_USER_TOOL,
    UPDATE_USER_TOOL,
    DELETE_USER_TOOL,
    GET_DASHBOARD_STATS_TOOL,
    SYNC_CALENDAR_TOOL,
    CANCEL_NOTIFICATION_TOOL
)
from mcp.capabilities.tools.coding_environment import (
    READ_FILE_TOOL,
    WRITE_FILE_TOOL,
    SEARCH_FILES_TOOL,
    LIST_FILES_TOOL,
    RUN_COMMAND_TOOL
)
from mcp.capabilities.resources.base import Resource
from mcp.capabilities.resources.assistant_resources import (
    USER_RESOURCE,
    EVENT_RESOURCE,
    USER_EVENTS_RESOURCE
)
from mcp.capabilities.prompts.base import Prompt
from mcp.capabilities.prompts.assistant_prompts import (
    NOTIFICATION_POLICY_PROMPT,
    EMAIL_TEMPLATE_PROMPT,
    TTS_SCRIPT_PROMPT
)
from mcp.core.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    SecretsRedactionMiddleware,
    AuthMiddleware
)

logger = structlog.get_logger(__name__)


class MCPServer:
    """MCP Server implementation."""
    
    def __init__(
        self,
        transport_type: str = "stdio",
        host: str = "localhost",
        port: int = 8080,
        path: str = "/mcp",
        max_concurrent: int = 32,
        default_timeout: float = 30.0
    ):
        """Initialize MCP server.
        
        Args:
            transport_type: Transport type ("stdio" or "websocket")
            host: WebSocket bind host
            port: WebSocket bind port
            path: WebSocket path
            max_concurrent: Maximum concurrent requests
            default_timeout: Default request timeout
        """
        self.transport_type = transport_type
        self.host = host
        self.port = port
        self.path = path
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        
        # Create router
        self.router = Router(max_concurrent, default_timeout)
        
        # Register capabilities
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.prompts: Dict[str, Prompt] = {}
        
        # Server info
        self.server_info = {
            "name": "assistant-mcp-server",
            "version": "1.0.0"
        }
        
        # Register handlers
        self._register_handlers()
        
        # Register tools, resources, prompts
        self._register_capabilities()
        
        # Register middleware
        self._register_middleware()
        
        # Transport
        self.transport: Optional[Union[StdioTransport, WebSocketTransport]] = None
        self._shutdown = False
    
    def _register_capabilities(self):
        """Register tools, resources, and prompts."""
        # Register tools
        for tool in [
            # Application Management
            START_WEB_APP_TOOL,
            STOP_WEB_APP_TOOL,
            WEB_APP_STATUS_TOOL,
            # User Management
            GET_USER_TOOL,
            CREATE_USER_TOOL,
            UPDATE_USER_TOOL,
            DELETE_USER_TOOL,
            # Event Management
            GET_EVENT_TOOL,
            LIST_EVENTS_TOOL,
            # Notification Management
            LIST_NOTIFICATIONS_TOOL,
            PLAN_NOTIFICATIONS_TOOL,
            CANCEL_NOTIFICATION_TOOL,
            # Calendar Management
            SYNC_CALENDAR_TOOL,
            # Dashboard
            GET_DASHBOARD_STATS_TOOL,
            # Coding Environment
            READ_FILE_TOOL,
            WRITE_FILE_TOOL,
            SEARCH_FILES_TOOL,
            LIST_FILES_TOOL,
            RUN_COMMAND_TOOL
        ]:
            self.tools[tool.name] = tool
        
        # Register resources
        for resource in [
            USER_RESOURCE,
            EVENT_RESOURCE,
            USER_EVENTS_RESOURCE
        ]:
            self.resources[resource.uri] = resource
        
        # Register prompts
        for prompt in [
            NOTIFICATION_POLICY_PROMPT,
            EMAIL_TEMPLATE_PROMPT,
            TTS_SCRIPT_PROMPT
        ]:
            self.prompts[prompt.name] = prompt
    
    def _register_middleware(self):
        """Register middleware."""
        # Logging middleware
        self.router.add_middleware(LoggingMiddleware(log_requests=True))
        
        # Rate limiting middleware
        self.router.add_middleware(
            RateLimitMiddleware(
                default_rate=100.0,  # requests per minute
                default_capacity=10
            )
        )
        
        # Secrets redaction middleware
        self.router.add_middleware(SecretsRedactionMiddleware())
        
        # Authentication middleware (disabled by default)
        # Enable in production with environment variable
        import os
        auth_enabled = os.getenv("MCP_AUTH_REQUIRED", "false").lower() == "true"
        auth_token_file = os.getenv("MCP_AUTH_TOKEN_FILE")
        if auth_enabled and auth_token_file:
            self.router.add_middleware(
                AuthMiddleware(enabled=True, token_file=auth_token_file)
            )
    
    def _register_handlers(self):
        """Register MCP protocol handlers."""
        # Initialize
        self.router.register("initialize", self._handle_initialize)
        
        # Tools
        self.router.register("tools/list", self._handle_tools_list)
        self.router.register("tools/call", self._handle_tools_call)
        
        # Resources
        self.router.register("resources/list", self._handle_resources_list)
        self.router.register("resources/read", self._handle_resources_read)
        
        # Prompts
        self.router.register("prompts/list", self._handle_prompts_list)
        self.router.register("prompts/get", self._handle_prompts_get)
    
    async def _handle_initialize(
        self,
        params: Dict[str, Any],
        cancellation_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Handle initialize request."""
        client_info = params.get("clientInfo", {})
        protocol_version = params.get("protocolVersion", "2024-11-05")
        capabilities = params.get("capabilities", {})
        
        logger.info(
            "Client initialize",
            client=client_info.get("name"),
            version=client_info.get("version"),
            protocol=protocol_version
        )
        
        # Build server capabilities
        server_capabilities = {
            "tools": {
                "listChanged": False  # Tools don't change dynamically
            },
            "resources": {
                "subscribe": False,
                "listChanged": False
            },
            "prompts": {
                "listChanged": False
            }
        }
        
        return {
            "protocolVersion": protocol_version,
            "capabilities": server_capabilities,
            "serverInfo": self.server_info
        }
    
    async def _handle_tools_list(
        self,
        params: Dict[str, Any],
        cancellation_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = [tool.get_definition() for tool in self.tools.values()]
        return {"tools": tools}
    
    async def _handle_tools_call(
        self,
        params: Dict[str, Any],
        cancellation_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("tool name is required")
        
        if tool_name not in self.tools:
            raise MCPMethodNotFoundError(f"tool/{tool_name}")
        
        tool = self.tools[tool_name]
        
        # Validate input schema (simplified)
        # In production, use full JSON Schema validation
        
        # Execute tool
        result = await tool.execute(arguments, cancellation_token)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ],
            "isError": "error" in result
        }
    
    async def _handle_resources_list(
        self,
        params: Dict[str, Any],
        cancellation_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Handle resources/list request."""
        resources = [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": "application/json"
            }
            for resource in self.resources.values()
        ]
        return {"resources": resources}
    
    async def _handle_resources_read(
        self,
        params: Dict[str, Any],
        cancellation_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri")
        offset = params.get("offset")
        limit = params.get("limit")
        
        if not uri:
            raise ValueError("resource URI is required")
        
        # Find matching resource
        resource = None
        for resource_pattern, res in self.resources.items():
            # Simple pattern matching (in production, use proper URI matching)
            if resource_pattern.replace("{user_id}", "") in uri or uri.startswith("resources://"):
                resource = res
                break
        
        if not resource:
            raise MCPServerError(
                f"Resource not found: {uri}",
                code=JSONRPCErrorCode.RESOURCE_NOT_FOUND
            )
        
        # Read resource
        result = await resource.read(uri, offset=offset, limit=limit)
        
        return result
    
    async def _handle_prompts_list(
        self,
        params: Dict[str, Any],
        cancellation_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Handle prompts/list request."""
        prompts = [prompt.get_definition() for prompt in self.prompts.values()]
        return {"prompts": prompts}
    
    async def _handle_prompts_get(
        self,
        params: Dict[str, Any],
        cancellation_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Handle prompts/get request."""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not prompt_name:
            raise ValueError("prompt name is required")
        
        if prompt_name not in self.prompts:
            raise MCPMethodNotFoundError(f"prompt/{prompt_name}")
        
        prompt = self.prompts[prompt_name]
        
        # Validate arguments (simplified)
        # In production, validate against prompt.arguments
        
        # Render prompt
        messages = await prompt.render(arguments)
        
        return {
            "messages": messages,
            "description": prompt.description
        }
    
    async def run_stdio(self):
        """Run server with stdio transport."""
        transport = StdioTransport()
        self.transport = transport
        
        await transport.connect()
        
        logger.info("MCP server started (stdio mode)")
        
        try:
            async for message in transport.iterate_messages():
                if isinstance(message, JSONRPCRequest):
                    response = await self.router.handle_request(message)
                    await transport.send_message(response)
                elif isinstance(message, JSONRPCNotification):
                    await self.router.handle_notification(message)
        except EOFError:
            # EOF on stdin is normal when pipe closes
            logger.info("EOF received, shutting down")
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        except Exception as e:
            logger.error("Error in stdio loop", error=str(e), exc_info=True)
        finally:
            try:
                await transport.disconnect()
            except Exception as e:
                logger.debug("Error during transport disconnect", error=str(e))
            await self.router.shutdown()
            logger.info("MCP server stopped")
    
    async def run_websocket(self):
        """Run server with WebSocket transport."""
        transport = WebSocketTransport(self.host, self.port, self.path, router=self.router)
        self.transport = transport
        
        await transport.connect()
        
        logger.info(f"MCP server started (websocket mode) on {self.host}:{self.port}{self.path}")
        
        # Wait for shutdown
        try:
            while not self._shutdown:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            await transport.disconnect()
            await self.router.shutdown()
            logger.info("MCP server stopped")
    
    async def run(self):
        """Run the server."""
        if self.transport_type == "stdio":
            await self.run_stdio()
        elif self.transport_type == "websocket":
            await self.run_websocket()
        else:
            raise ValueError(f"Unknown transport type: {self.transport_type}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Server for Assistant")
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
        default=8080,
        help="WebSocket bind port"
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="WebSocket path"
    )
    
    args = parser.parse_args()
    
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
    
    # Create and run server
    server = MCPServer(
        transport_type=args.transport,
        host=args.host,
        port=args.port,
        path=args.path
    )
    
    # Run server
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server shutdown")


if __name__ == "__main__":
    main()

