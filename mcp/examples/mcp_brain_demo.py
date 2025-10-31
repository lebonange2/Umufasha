"""Demo: Using MCP Server as the Brain of the Application."""
import asyncio
import json
import sys
from typing import Dict, Any

from mcp.core.protocol.messages import JSONRPCRequest, parse_message, serialize_message


class MCPBrainClient:
    """Client to control application via MCP."""
    
    def __init__(self, stdin=sys.stdin, stdout=sys.stdout):
        self.stdin = stdin
        self.stdout = stdout
        self.request_id = 0
    
    def _next_id(self) -> int:
        self.request_id += 1
        return self.request_id
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool."""
        request = JSONRPCRequest(
            id=self._next_id(),
            method="tools/call",
            params={
                "name": name,
                "arguments": arguments
            }
        )
        
        request_data = serialize_message(request)
        self.stdout.write(request_data + "\n")
        self.stdout.flush()
        
        response_line = await asyncio.to_thread(self.stdin.readline)
        response_data = response_line.rstrip("\n\r")
        response_dict = json.loads(response_data)
        
        if "error" in response_dict:
            raise RuntimeError(f"Tool call failed: {response_dict['error'].get('message')}")
        
        result = response_dict.get("result", {})
        content = result.get("content", [])
        if content and len(content) > 0:
            return json.loads(content[0].get("text", "{}"))
        return result
    
    async def initialize(self):
        """Initialize MCP connection."""
        request = JSONRPCRequest(
            id=self._next_id(),
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-brain-client", "version": "1.0.0"}
            }
        )
        
        request_data = serialize_message(request)
        self.stdout.write(request_data + "\n")
        self.stdout.flush()
        
        response_line = await asyncio.to_thread(self.stdin.readline)
        response_data = response_line.rstrip("\n\r")
        response_dict = json.loads(response_data)
        
        # Send initialized notification
        notification = {"jsonrpc": "2.0", "method": "initialized"}
        self.stdout.write(json.dumps(notification) + "\n")
        self.stdout.flush()
        
        return response_dict.get("result", {})


async def demo_application_control():
    """Demonstrate controlling application via MCP."""
    print("=== MCP Server as Application Brain Demo ===\n", file=sys.stderr)
    
    client = MCPBrainClient()
    
    # Initialize
    print("1. Initializing MCP connection...", file=sys.stderr)
    await client.initialize()
    print("   ✓ Connected\n", file=sys.stderr)
    
    # Check web app status
    print("2. Checking web application status...", file=sys.stderr)
    status = await client.call_tool("webApplicationStatus", {})
    print(f"   Status: {status.get('status')}", file=sys.stderr)
    print(f"   Port in use: {status.get('port_8000_in_use')}", file=sys.stderr)
    print(f"   Responding: {status.get('is_responding')}\n", file=sys.stderr)
    
    # Start web application (if not running)
    if status.get('status') != 'running':
        print("3. Starting web application...", file=sys.stderr)
        start_result = await client.call_tool("startWebApplication", {})
        print(f"   ✓ {start_result.get('message')}", file=sys.stderr)
        if 'url' in start_result:
            print(f"   URL: {start_result.get('url')}", file=sys.stderr)
            print(f"   Admin: {start_result.get('admin_url')}\n", file=sys.stderr)
    
    # Get dashboard stats
    print("4. Getting dashboard statistics...", file=sys.stderr)
    stats = await client.call_tool("getDashboardStats", {})
    print(f"   Users: {stats.get('stats', {}).get('users', 0)}", file=sys.stderr)
    print(f"   Events: {stats.get('stats', {}).get('events', 0)}", file=sys.stderr)
    print(f"   Notifications: {stats.get('stats', {}).get('notifications', 0)}\n", file=sys.stderr)
    
    # List users
    print("5. Listing users...", file=sys.stderr)
    # Note: We need to list via resources or create a listUsers tool
    print("   (List users via resources://users/{user_id})\n", file=sys.stderr)
    
    print("=== Demo Complete ===\n", file=sys.stderr)
    print("You can now control the application entirely via MCP!", file=sys.stderr)
    print("\nTry these commands:", file=sys.stderr)
    print("  - Start web app: tools/call startWebApplication", file=sys.stderr)
    print("  - Create user: tools/call createUser {\"name\":\"...\", \"email\":\"...\"}", file=sys.stderr)
    print("  - Get stats: tools/call getDashboardStats", file=sys.stderr)
    print("  - Stop web app: tools/call stopWebApplication", file=sys.stderr)


if __name__ == "__main__":
    try:
        asyncio.run(demo_application_control())
    except KeyboardInterrupt:
        pass

