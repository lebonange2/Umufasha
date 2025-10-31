#!/usr/bin/env python3
"""Simple WebSocket test."""
import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

async def test():
    uri = "ws://localhost:8080/mcp"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            print("✓ Connected!")
            
            # Send initialize
            await ws.send(json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0.0"}
                }
            }))
            
            # Receive response
            response = await ws.recv()
            data = json.loads(response)
            print(f"✓ Response: {data.get('result', {}).get('serverInfo', {}).get('name')}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
