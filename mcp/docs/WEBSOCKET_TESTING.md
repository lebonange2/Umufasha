# WebSocket Testing Guide

## Understanding the Error

When you try to access a WebSocket server directly in a browser (e.g., `http://localhost:8080/mcp`), you'll see this error:

```
Failed to open a WebSocket connection: invalid Connection header: keep-alive.
```

### Why This Happens

1. **Browsers make HTTP requests**: When you navigate to a URL, your browser sends an HTTP GET request, not a WebSocket connection request.

2. **WebSocket requires a handshake**: WebSocket connections start with an HTTP request but require a special "Upgrade" handshake that converts the connection from HTTP to WebSocket.

3. **The server expects WebSocket**: The MCP server is configured to accept WebSocket connections, not regular HTTP requests.

### The Solution

You need a **WebSocket client** to connect to the server, not a browser's HTTP navigation.

## Testing the WebSocket Server

### Method 1: Use the Test Client Script

```bash
# Make sure the server is running
python3 -m mcp.server --transport websocket --host localhost --port 8080 &

# Run the test client
python3 mcp/examples/test_websocket.py
```

This will:
1. Connect to the WebSocket server
2. Send an `initialize` request
3. List available tools
4. List available resources

### Method 2: Use websocat (Command-line Tool)

Install websocat:
```bash
# On Ubuntu/Debian
sudo apt install websocat

# Or via cargo (Rust)
cargo install websocat
```

Test the connection:
```bash
# Start server in one terminal
python3 -m mcp.server --transport websocket --host localhost --port 8080

# In another terminal, connect with websocat
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | websocat ws://localhost:8080/mcp
```

### Method 3: Use JavaScript in Browser Console

Open your browser's developer console (F12) and run:

```javascript
// Connect to WebSocket server
const ws = new WebSocket('ws://localhost:8080/mcp');

// Handle connection open
ws.onopen = () => {
    console.log('Connected!');
    
    // Send initialize request
    ws.send(JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "initialize",
        params: {
            protocolVersion: "2024-11-05",
            capabilities: {},
            clientInfo: {
                name: "browser-client",
                version: "1.0.0"
            }
        }
    }));
};

// Handle messages
ws.onmessage = (event) => {
    console.log('Received:', JSON.parse(event.data));
};

// Handle errors
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

// Handle close
ws.onclose = () => {
    console.log('Connection closed');
};
```

### Method 4: Use Python Script

```python
import asyncio
import json
import websockets

async def test():
    uri = "ws://localhost:8080/mcp"
    async with websockets.connect(uri) as websocket:
        # Send initialize
        await websocket.send(json.dumps({
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
        response = await websocket.recv()
        print("Response:", json.loads(response))

asyncio.run(test())
```

## Common Issues

### Connection Refused

**Error**: `Connection refused`

**Solution**: Make sure the server is running:
```bash
python3 -m mcp.server --transport websocket --host localhost --port 8080
```

### Invalid Status Code

**Error**: `Invalid status code 404`

**Solution**: Check the WebSocket path. Default is `/mcp`. Make sure your client connects to:
```
ws://localhost:8080/mcp
```

Not:
```
ws://localhost:8080/  (wrong path)
```

### CORS Issues (Browser)

**Error**: CORS policy errors in browser console

**Solution**: The WebSocket server needs to handle CORS if accessed from a browser. Currently, it's designed for direct client connections, not browser-based access.

## Debugging Tips

1. **Check if server is listening**:
```bash
netstat -tlnp | grep 8080
# or
ss -tlnp | grep 8080
```

2. **Check server logs**: The server will log connection attempts in stdio mode or to logs.

3. **Test with curl** (for HTTP endpoint, not WebSocket):
```bash
curl http://localhost:8080/health
```

4. **Use tcpdump/wireshark** to inspect network traffic:
```bash
sudo tcpdump -i lo -A 'tcp port 8080'
```

## WebSocket vs HTTP

| Feature | HTTP | WebSocket |
|---------|------|-----------|
| Connection | Request/Response | Persistent |
| Protocol | HTTP 1.1 | WebSocket (RFC 6455) |
| Browser | Navigate to URL | Use JavaScript WebSocket API |
| Client | Any HTTP client | WebSocket client |
| Use Case | REST API | Real-time communication |

## Next Steps

- See [QUICKSTART.md](QUICKSTART.md) for basic usage
- See [MESSAGE_CATALOG.md](MESSAGE_CATALOG.md) for API reference
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues

