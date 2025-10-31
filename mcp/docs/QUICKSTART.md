# MCP Server Quickstart Guide

## Installation

### From Source

```bash
cd /home/uwisiyose/ASSISTANT/mcp
pip install -e .
```

### Development Installation

```bash
cd /home/uwisiyose/ASSISTANT/mcp
pip install -e ".[dev]"
```

## Running the Server

### Stdio Mode (Recommended for CLI)

```bash
python -m mcp.server --transport stdio
```

The server will read JSON-RPC messages from stdin and write responses to stdout (newline-delimited JSON).

### WebSocket Mode

```bash
python -m mcp.server --transport websocket --host localhost --port 8080 --path /mcp
```

The server will listen for WebSocket connections on `ws://localhost:8080/mcp`.

## Testing with Hello Client

### Stdio Mode

Run the server and client in separate terminals:

**Terminal 1 (Server):**
```bash
python -m mcp.server --transport stdio
```

**Terminal 2 (Client):**
```bash
python mcp/examples/hello-client.py | python -m mcp.server --transport stdio
```

Or use a pipe:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python -m mcp.server --transport stdio
```

## Available Capabilities

### Tools

- `getUser`: Get user details by ID
- `getEvent`: Get event details by ID
- `listEvents`: List calendar events with filters
- `listNotifications`: List notifications with filters
- `planNotifications`: Plan notifications for user events using LLM policy

### Resources

- `resources://users/{user_id}`: User profile data
- `resources://events/{event_id}`: Event details
- `resources://users/{user_id}/events`: List of user's events

### Prompts

- `notificationPolicy`: LLM prompt template for notification planning
- `emailTemplate`: Email notification template
- `ttsScript`: TTS script template for phone calls

## Example Request/Response

### Initialize Request

```json
{
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
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {"listChanged": false},
      "resources": {"subscribe": false, "listChanged": false},
      "prompts": {"listChanged": false}
    },
    "serverInfo": {
      "name": "assistant-mcp-server",
      "version": "1.0.0"
    }
  }
}
```

### List Tools Request

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "getUser",
        "description": "Get user details by ID",
        "inputSchema": {
          "type": "object",
          "properties": {
            "user_id": {"type": "string", "description": "User ID"}
          },
          "required": ["user_id"]
        }
      },
      ...
    ]
  }
}
```

### Call Tool Request

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "listEvents",
    "arguments": {
      "days_back": 2,
      "days_forward": 30
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"events\": [...],\n  \"count\": 5\n}"
      }
    ],
    "isError": false
  }
}
```

## Configuration

The server can be configured via environment variables:

- `MCP_TRANSPORT`: Transport type ("stdio" or "websocket")
- `MCP_HOST`: WebSocket bind host (default: "localhost")
- `MCP_PORT`: WebSocket bind port (default: 8080)
- `MCP_PATH`: WebSocket path (default: "/mcp")
- `MCP_MAX_CONCURRENT`: Maximum concurrent requests (default: 32)
- `MCP_DEFAULT_TIMEOUT`: Default request timeout in seconds (default: 30.0)

## Next Steps

- See [MESSAGE_CATALOG.md](MESSAGE_CATALOG.md) for complete API documentation
- See [DESIGN_NOTES.md](DESIGN_NOTES.md) for architecture details
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions

