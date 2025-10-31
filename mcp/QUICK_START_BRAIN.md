# Quick Start: Using MCP as Application Brain

## What Changed?

The MCP server is now the **control layer** for your web application. You can:

- ✅ **Start/Stop the web application** via MCP
- ✅ **Control all features** without using the web UI
- ✅ **Manage users, events, notifications** via MCP tools
- ✅ **Get dashboard statistics** via MCP
- ✅ **Integrate with LLM clients** (Claude Desktop, etc.)

## Quick Demo

### 1. Start MCP Server

```bash
cd /home/uwisiyose/ASSISTANT
python3 -m mcp.server --transport stdio
```

### 2. In Another Terminal, Control the Application

```bash
# Initialize and start web app
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | python3 -m mcp.server --transport stdio

# Start web application
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | python3 -m mcp.server --transport stdio

# Check status
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"webApplicationStatus","arguments":{}}}' | python3 -m mcp.server --transport stdio

# Get dashboard stats
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"getDashboardStats","arguments":{}}}' | python3 -m mcp.server --transport stdio

# Create a user
echo '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"John Doe","email":"john@example.com"}}}' | python3 -m mcp.server --transport stdio

# Stop web application
echo '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"stopWebApplication","arguments":{}}}' | python3 -m mcp.server --transport stdio
```

## Available Tools (Summary)

### Application Management
- `startWebApplication` - Start web app on port 8000
- `stopWebApplication` - Stop web app
- `webApplicationStatus` - Check web app status

### User Management
- `createUser` - Create new user
- `getUser` - Get user details
- `updateUser` - Update user settings
- `deleteUser` - Delete user

### Event Management
- `getEvent` - Get event details
- `listEvents` - List events with filters

### Notification Management
- `listNotifications` - List notifications
- `planNotifications` - Plan notifications using LLM
- `cancelNotification` - Cancel scheduled notification

### Calendar Management
- `syncCalendar` - Sync Google Calendar

### Dashboard
- `getDashboardStats` - Get dashboard statistics

## Example Workflow

1. **Start MCP Server**
   ```bash
   python3 -m mcp.server --transport websocket --host localhost --port 8080
   ```

2. **Start Web Application via MCP**
   ```json
   {"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}
   ```

3. **Create User via MCP**
   ```json
   {"method":"tools/call","params":{"name":"createUser","arguments":{"name":"Jane","email":"jane@example.com"}}}
   ```

4. **Get Stats via MCP**
   ```json
   {"method":"tools/call","params":{"name":"getDashboardStats","arguments":{}}}
   ```

5. **Plan Notifications via MCP**
   ```json
   {"method":"tools/call","params":{"name":"planNotifications","arguments":{"user_id":"user-123"}}}
   ```

6. **Stop Web App via MCP**
   ```json
   {"method":"tools/call","params":{"name":"stopWebApplication","arguments":{}}}
   ```

## Integration with Claude Desktop

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "assistant": {
      "command": "python3",
      "args": ["-m", "mcp.server", "--transport", "stdio"],
      "cwd": "/home/uwisiyose/ASSISTANT"
    }
  }
}
```

Then ask Claude:
- "Start the web application"
- "Create a user named John with email john@example.com"
- "Show me the dashboard statistics"
- "Plan notifications for all users"

## Next Steps

- See [MCP_AS_BRAIN.md](docs/MCP_AS_BRAIN.md) for detailed documentation
- See [MESSAGE_CATALOG.md](docs/MESSAGE_CATALOG.md) for complete API reference
- See [examples/mcp_brain_demo.py](examples/mcp_brain_demo.py) for demo script

