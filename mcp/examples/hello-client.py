"""Simple MCP client example."""
import asyncio
import json
import sys
from typing import Dict, Any, Optional

from mcp.core.protocol.messages import (
    JSONRPCRequest,
    JSONRPCResponse,
    parse_message,
    serialize_message
)


class SimpleMCPClient:
    """Simple MCP client for testing."""
    
    def __init__(self, stdin=sys.stdin, stdout=sys.stdout):
        self.stdin = stdin
        self.stdout = stdout
        self.request_id = 0
    
    def _next_id(self) -> int:
        """Get next request ID."""
        self.request_id += 1
        return self.request_id
    
    async def send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a request and wait for response."""
        request = JSONRPCRequest(
            id=self._next_id(),
            method=method,
            params=params or {}
        )
        
        # Send request
        request_data = serialize_message(request)
        self.stdout.write(request_data + "\n")
        self.stdout.flush()
        
        # Read response
        response_line = await asyncio.to_thread(self.stdin.readline)
        if not response_line:
            raise EOFError("End of input")
        
        response_data = response_line.rstrip("\n\r")
        response_dict = json.loads(response_data)
        
        if "error" in response_dict:
            raise RuntimeError(
                f"Request failed: {response_dict['error'].get('message', 'Unknown error')}"
            )
        
        return response_dict.get("result", {})
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize connection."""
        return await self.send_request(
            "initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "hello-client",
                    "version": "1.0.0"
                }
            }
        )
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return await self.send_request("tools/list")
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool."""
        return await self.send_request(
            "tools/call",
            params={
                "name": name,
                "arguments": arguments
            }
        )
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources."""
        return await self.send_request("resources/list")
    
    async def read_resource(
        self,
        uri: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Read a resource."""
        params = {"uri": uri}
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        
        return await self.send_request("resources/read", params=params)
    
    async def list_prompts(self) -> Dict[str, Any]:
        """List available prompts."""
        return await self.send_request("prompts/list")
    
    async def get_prompt(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get a prompt."""
        return await self.send_request(
            "prompts/get",
            params={
                "name": name,
                "arguments": arguments
            }
        )


async def main():
    """Main demo function."""
    print("=== MCP Client Demo ===", file=sys.stderr)
    
    client = SimpleMCPClient()
    
    # Initialize
    print("\n1. Initializing...", file=sys.stderr)
    init_result = await client.initialize()
    print(f"   Server: {init_result.get('serverInfo', {}).get('name')}", file=sys.stderr)
    
    # Send initialized notification
    import json
    notification = {
        "jsonrpc": "2.0",
        "method": "initialized"
    }
    print(json.dumps(notification), flush=True)
    
    # List tools
    print("\n2. Listing tools...", file=sys.stderr)
    tools_result = await client.list_tools()
    tools = tools_result.get("tools", [])
    print(f"   Found {len(tools)} tools:", file=sys.stderr)
    for tool in tools[:3]:  # Show first 3
        print(f"   - {tool.get('name')}: {tool.get('description', '')[:50]}...", file=sys.stderr)
    
    # Call a tool (example)
    if tools:
        print(f"\n3. Calling tool: {tools[0].get('name')}...", file=sys.stderr)
        # This would require valid parameters - skip for demo
        print("   (Skipping tool call - requires valid parameters)", file=sys.stderr)
    
    # List resources
    print("\n4. Listing resources...", file=sys.stderr)
    resources_result = await client.list_resources()
    resources = resources_result.get("resources", [])
    print(f"   Found {len(resources)} resources:", file=sys.stderr)
    for resource in resources[:3]:  # Show first 3
        print(f"   - {resource.get('uri')}: {resource.get('name', '')[:50]}...", file=sys.stderr)
    
    # List prompts
    print("\n5. Listing prompts...", file=sys.stderr)
    prompts_result = await client.list_prompts()
    prompts = prompts_result.get("prompts", [])
    print(f"   Found {len(prompts)} prompts:", file=sys.stderr)
    for prompt in prompts[:3]:  # Show first 3
        print(f"   - {prompt.get('name')}: {prompt.get('description', '')[:50]}...", file=sys.stderr)
    
    print("\n=== Demo Complete ===", file=sys.stderr)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

