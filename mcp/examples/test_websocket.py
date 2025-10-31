"""Simple WebSocket client for testing MCP server."""
import asyncio
import json
import sys
from typing import Optional

try:
    import websockets
    from websockets.exceptions import ConnectionClosed, InvalidStatusCode
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("websockets library required. Install with: pip install websockets")
    sys.exit(1)


async def test_websocket_connection(uri: str = "ws://localhost:8080/mcp"):
    """Test WebSocket connection to MCP server."""
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to WebSocket server")
            
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            print(f"\n→ Sending: initialize")
            await websocket.send(json.dumps(init_request))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"← Received: {json.dumps(response_data, indent=2)}")
            
            if response_data.get("result"):
                print("\n✓ Initialize successful!")
                
                # Send initialized notification
                initialized = {
                    "jsonrpc": "2.0",
                    "method": "initialized"
                }
                await websocket.send(json.dumps(initialized))
                
                # List tools
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                
                print(f"\n→ Sending: tools/list")
                await websocket.send(json.dumps(tools_request))
                
                tools_response = await websocket.recv()
                tools_data = json.loads(tools_response)
                print(f"← Received tools: {len(tools_data.get('result', {}).get('tools', []))} tools")
                
                # List resources
                resources_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "resources/list",
                    "params": {}
                }
                
                print(f"\n→ Sending: resources/list")
                await websocket.send(json.dumps(resources_request))
                
                resources_response = await websocket.recv()
                resources_data = json.loads(resources_response)
                print(f"← Received resources: {len(resources_data.get('result', {}).get('resources', []))} resources")
                
                print("\n✓ WebSocket test complete!")
            
    except InvalidStatusCode as e:
        print(f"✗ Connection failed: Invalid status code {e.status_code}")
        print("  Make sure the server is running and the path is correct")
    except ConnectionRefusedError:
        print("✗ Connection refused")
        print("  Make sure the server is running: python -m mcp.server --transport websocket")
    except ConnectionClosed as e:
        print(f"✗ Connection closed: {e}")
        print("  Server closed the connection unexpectedly")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test WebSocket connection to MCP server")
    parser.add_argument(
        "--uri",
        default="ws://localhost:8080/mcp",
        help="WebSocket URI (default: ws://localhost:8080/mcp)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(test_websocket_connection(args.uri))


if __name__ == "__main__":
    main()

