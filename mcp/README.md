# MCP Server for Assistant Application

A production-ready Model Context Protocol (MCP) server that acts as the **control layer** for the Assistant web application. Manage your entire application through MCP tools, resources, and prompts.

## 🎯 Overview

The MCP server provides programmatic access to all Assistant application features, allowing you to:
- **Control the web application** (start/stop/status)
- **Manage users, events, and notifications** via MCP tools
- **Integrate with LLM clients** (Claude Desktop, etc.)
- **Access application data** via MCP resources
- **Use prompt templates** for LLM interactions

## ✨ Key Features

- ✅ **Full MCP Protocol**: JSON-RPC 2.0 based implementation
- ✅ **Dual Transports**: Stdio and WebSocket support
- ✅ **Application Management**: Start/stop web application via MCP
- ✅ **Comprehensive Tools**: 13 tools covering all application features
- ✅ **Resources**: User, event, and notification data access
- ✅ **Prompts**: Notification policy, email templates, TTS scripts
- ✅ **Security**: Rate limiting, authentication, secrets redaction
- ✅ **Observability**: Structured logging with JSON lines
- ✅ **Production Ready**: Docker, systemd, Kubernetes support

## 🚀 Quick Start

### Installation

```bash
# Navigate to project root
cd /home/uwisiyose/ASSISTANT

# Install MCP server
cd mcp
pip install -e ".[app-management]"
cd ..
```

### Run MCP Server

**Stdio Mode:**
```bash
python3 -m mcp.server --transport stdio
```

**WebSocket Mode:**
```bash
python3 -m mcp.server --transport websocket --host localhost --port 8080
```

### Example: Start Web Application via MCP

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

## 🛠️ Available Tools

### Application Management
- **`startWebApplication`** - Start web app on port 8000
- **`stopWebApplication`** - Stop web app
- **`webApplicationStatus`** - Check web app status

### User Management
- **`createUser`** - Create new user account
- **`getUser`** - Get user details by ID
- **`updateUser`** - Update user preferences
- **`deleteUser`** - Delete user account

### Event Management
- **`getEvent`** - Get event details by ID
- **`listEvents`** - List events with filters

### Notification Management
- **`listNotifications`** - List notifications with filters
- **`planNotifications`** - Plan notifications using LLM policy
- **`cancelNotification`** - Cancel scheduled notification

### Calendar Management
- **`syncCalendar`** - Sync Google Calendar events

### Dashboard
- **`getDashboardStats`** - Get dashboard statistics

## 📦 Resources

Access application data via MCP resources:

- **`resources://users/{user_id}`** - User profile data
- **`resources://events/{event_id}`** - Event details
- **`resources://users/{user_id}/events`** - List of user's events

## 💬 Prompts

Use prompt templates for LLM interactions:

- **`notificationPolicy`** - LLM prompt for notification planning
- **`emailTemplate`** - Email notification template
- **`ttsScript`** - TTS script template

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](QUICK_START_BRAIN.md)** - Quick reference for using MCP as application brain
- **[Usage Guide](docs/USAGE_GUIDE.md)** - Comprehensive usage instructions
- **[How It Works](docs/HOW_IT_WORKS.md)** - Technical explanation of process management

### Reference
- **[Complete API](docs/MESSAGE_CATALOG.md)** - Every method with schemas and examples
- **[Design Notes](docs/DESIGN_NOTES.md)** - Architecture and design decisions
- **[Add User Guide](docs/ADD_USER_GUIDE.md)** - Step-by-step user creation

### Operations
- **[Installation](docs/INSTALLATION.md)** - Installation and dependency management
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Deployment](docs/DEPLOYMENT.md)** - Production deployment guide

### Security
- **[Threat Model](security/threat-model.md)** - Security analysis
- **[Hardening](security/hardening.md)** - Security hardening measures

## 🏗️ Architecture

```
mcp/
├── core/                  # Core protocol implementation
│   ├── protocol/          # Message types and validation
│   ├── transport/        # Stdio and WebSocket transports
│   ├── router.py         # Request router with middleware
│   ├── errors.py         # Error handling
│   ├── validation.py     # JSON Schema validation
│   ├── concurrency.py    # Rate limiting, timeouts, backpressure
│   └── middleware.py     # Logging, auth, rate limiting middleware
├── capabilities/         # MCP capabilities
│   ├── tools/           # Tool implementations
│   │   ├── base.py      # Tool base class
│   │   ├── app_management.py      # Application management tools
│   │   ├── assistant_tools.py    # Assistant-specific tools
│   │   └── comprehensive_tools.py # User/event/notification tools
│   ├── resources/       # Resource implementations
│   │   ├── base.py      # Resource base class
│   │   └── assistant_resources.py # Assistant resources
│   └── prompts/         # Prompt templates
│       ├── base.py      # Prompt base class
│       └── assistant_prompts.py # Assistant prompts
├── server.py            # Main server implementation
├── examples/            # Example clients
│   ├── hello-client.py         # Basic stdio client
│   ├── test_websocket.py       # WebSocket test client
│   ├── mcp_brain_demo.py       # Application control demo
│   └── add_user_example.sh     # User creation example
├── tests/               # Test suite
│   ├── unit/           # Unit tests
│   └── e2e/            # End-to-end tests
├── security/            # Security documentation
├── ops/                 # Deployment files
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── systemd.service
│   └── k8s-deployment.yaml
├── docs/                # Documentation
├── scripts/             # Utility scripts
│   └── check_webapp.sh  # Web app status checker
└── pyproject.toml       # Project configuration
```

## 🔌 Integration

### Claude Desktop

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

Then you can ask Claude:
- "Start the web application"
- "Create a user named John with email john@example.com"
- "Show me the dashboard statistics"
- "Plan notifications for user user-123"

### Custom Client

```python
import asyncio
import json
from mcp.examples.hello_client import SimpleMCPClient

async def main():
    client = SimpleMCPClient()
    await client.initialize()
    
    # Start web app
    result = await client.call_tool("startWebApplication", {})
    print("Result:", result)
    
    # Create user
    result = await client.call_tool("createUser", {
        "name": "Jane Doe",
        "email": "jane@example.com"
    })
    print("User created:", result)

asyncio.run(main())
```

## 🧪 Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[app-management,dev]"

# Run tests
pytest

# Run linter
flake8 mcp/

# Run type checker
mypy mcp/

# Format code
black mcp/
```

### Running Examples

```bash
# Basic stdio client
python3 mcp/examples/hello-client.py

# WebSocket client
python3 mcp/examples/test_websocket.py

# Application control demo
python3 mcp/examples/mcp_brain_demo.py
```

## 📦 Deployment

### Docker

```bash
cd mcp/ops
docker-compose up
```

### systemd

```bash
sudo cp mcp/ops/systemd.service /etc/systemd/system/assistant-mcp.service
sudo systemctl enable assistant-mcp
sudo systemctl start assistant-mcp
```

### Kubernetes

```bash
kubectl apply -f mcp/ops/k8s-deployment.yaml
```

## 🔧 Configuration

### Environment Variables

- `MCP_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `MCP_RATE_LIMIT_REQUESTS_PER_MINUTE` - Rate limit (default: 100)
- `MCP_MAX_CONCURRENT` - Max concurrent requests (default: 32)
- `MCP_DEFAULT_TIMEOUT` - Default timeout in seconds (default: 30.0)

### Authentication

For production, configure authentication:
- File-based tokens
- mTLS (mutual TLS)
- UNIX-domain socket ACLs

See [hardening.md](security/hardening.md) for details.

## 📊 Example Workflows

### Complete Application Management

```bash
# 1. Start web application
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio

# 2. Create user
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"John","email":"john@example.com"}}}' | \
python3 -m mcp.server --transport stdio

# 3. Get dashboard stats
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"getDashboardStats","arguments":{}}}' | \
python3 -m mcp.server --transport stdio

# 4. Plan notifications
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"planNotifications","arguments":{"user_id":"user-123"}}}' | \
python3 -m mcp.server --transport stdio

# 5. Stop web application
echo '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"stopWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

## 📝 License

MIT License - see LICENSE file

## 🆘 Support

- **Documentation**: See `docs/` directory
- **Troubleshooting**: See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Examples**: See `examples/` directory
