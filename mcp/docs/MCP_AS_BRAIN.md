# MCP Server as Application Brain

## Overview

The MCP server now acts as the **control layer** for the entire web application. You can control and manage the web application entirely through MCP tools, without needing to use the web UI directly.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Server                           │
│                  (Control Layer)                        │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ App          │  │ User/Event   │  │ Notification ││
│  │ Management   │  │ Management   │  │ Management   ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
└─────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│              Web Application (Port 8000)                │
│         FastAPI + Admin UI + API Endpoints              │
└─────────────────────────────────────────────────────────┘
```

## Available MCP Tools

### Application Management

#### `startWebApplication`
Start the web application on port 8000.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "startWebApplication",
    "arguments": {}
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\n  \"status\": \"started\",\n  \"pid\": 12345,\n  \"url\": \"http://localhost:8000\",\n  \"admin_url\": \"http://localhost:8000/admin\",\n  \"api_docs\": \"http://localhost:8000/docs\"\n}"
    }]
  }
}
```

#### `stopWebApplication`
Stop the web application.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "stopWebApplication",
    "arguments": {}
  }
}
```

#### `webApplicationStatus`
Get the current status of the web application.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "webApplicationStatus",
    "arguments": {}
  }
}
```

### User Management

- **`createUser`**: Create a new user account
- **`getUser`**: Get user details by ID
- **`updateUser`**: Update user preferences
- **`deleteUser`**: Delete a user account

### Event Management

- **`getEvent`**: Get event details by ID
- **`listEvents`**: List calendar events with filters

### Notification Management

- **`listNotifications`**: List notifications with filters
- **`planNotifications`**: Plan notifications using LLM policy
- **`cancelNotification`**: Cancel a scheduled notification

### Calendar Management

- **`syncCalendar`**: Sync Google Calendar events for a user

### Dashboard & Statistics

- **`getDashboardStats`**: Get dashboard statistics (user counts, recent notifications, audit logs)

## Usage Examples

### Starting the Web Application

```bash
# Via MCP client
python3 -m mcp.examples.test_websocket

# Or via direct JSON-RPC call
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

### Creating a User via MCP

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "createUser",
    "arguments": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone_e164": "+1234567890",
      "channel_pref": "email"
    }
  }
}
```

### Getting Dashboard Statistics

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "getDashboardStats",
    "arguments": {}
  }
}
```

### Planning Notifications

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "planNotifications",
    "arguments": {
      "user_id": "user-123",
      "force_replan": false
    }
  }
}
```

## Workflow: Using MCP to Control Everything

### Complete Application Management

1. **Start the web application:**
   ```json
   {"method": "tools/call", "params": {"name": "startWebApplication"}}
   ```

2. **Check status:**
   ```json
   {"method": "tools/call", "params": {"name": "webApplicationStatus"}}
   ```

3. **Create a user:**
   ```json
   {"method": "tools/call", "params": {"name": "createUser", "arguments": {...}}}
   ```

4. **Sync their calendar:**
   ```json
   {"method": "tools/call", "params": {"name": "syncCalendar", "arguments": {"user_id": "..."}}}
   ```

5. **Plan notifications:**
   ```json
   {"method": "tools/call", "params": {"name": "planNotifications", "arguments": {"user_id": "..."}}}
   ```

6. **View dashboard stats:**
   ```json
   {"method": "tools/call", "params": {"name": "getDashboardStats"}}
   ```

7. **Stop the application:**
   ```json
   {"method": "tools/call", "params": {"name": "stopWebApplication"}}
   ```

## Integration with LLM Clients

You can use any MCP-compatible LLM client to control the application:

### Claude Desktop (Example)

Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "assistant": {
      "command": "python3",
      "args": ["-m", "mcp.server", "--transport", "stdio"],
      "cwd": "/home/uwisiyose/ASSISTANT/mcp"
    }
  }
}
```

Then you can ask Claude:
- "Start the web application"
- "Create a new user named John Doe with email john@example.com"
- "Show me the dashboard statistics"
- "Plan notifications for user user-123"
- "Sync calendar for user user-123"

### Custom MCP Client

```python
from mcp.examples.hello_client import SimpleMCPClient

client = SimpleMCPClient()

# Start web app
await client.call_tool("startWebApplication", {})

# Create user
await client.call_tool("createUser", {
    "name": "Jane Doe",
    "email": "jane@example.com"
})
```

## Benefits

1. **Single Control Point**: Manage everything through MCP
2. **LLM Integration**: Use AI assistants to control the application
3. **Automation**: Script complex workflows via MCP tools
4. **API Consistency**: All operations use the same MCP protocol
5. **Remote Control**: Control the application via WebSocket from anywhere

## Next Steps

- See [QUICKSTART.md](QUICKSTART.md) for MCP server setup
- See [MESSAGE_CATALOG.md](MESSAGE_CATALOG.md) for complete API reference
- See [EXAMPLES.md](../EXAMPLES.md) for usage examples

