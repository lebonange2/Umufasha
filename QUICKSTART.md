# 🚀 Assistant Application - Complete Quick Start Guide

A comprehensive AI-powered personal assistant with voice brainstorming capabilities, powered by MCP (Model Context Protocol) server.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Setup](#quick-setup)
4. [Running the Application](#running-the-application)
5. [Using MCP Server](#using-mcp-server)
6. [Web Application](#web-application)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

## 🎯 Overview

This application consists of two main components:

1. **Web Application** - FastAPI-based personal assistant with admin UI
   - User management
   - Calendar integration
   - Notification planning
   - Voice and email notifications

2. **MCP Server** - Model Context Protocol server for application control
   - Start/stop web application
   - Manage users, events, notifications
   - Dashboard statistics
   - LLM integration via MCP protocol

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│            MCP Server (Control Layer)           │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ App Mgmt     │  │ User/Event   │            │
│  │ Tools        │  │ Management   │            │
│  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────┘
          │                    │
          ▼                    ▼
┌─────────────────────────────────────────────────┐
│      Web Application (Port 8000)                │
│  FastAPI + Admin UI + API Endpoints             │
└─────────────────────────────────────────────────┘
```

## ⚡ Quick Setup

### Prerequisites

- Python 3.10+
- pip
- Virtual environment (recommended)

### Installation Steps

```bash
# 1. Clone or navigate to project directory
cd /home/uwisiyose/ASSISTANT

# 2. Create virtual environment (if not exists)
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install MCP server
cd mcp
pip install -e ".[app-management]"
cd ..

# 5. Initialize database
python3 scripts/init_db.py

# 6. Create .env file (if not exists)
cp .env.example .env
```

## 🚀 Running the Application

### Option 1: Start via MCP Server (Recommended)

The MCP server can start and control the entire application:

```bash
# Start web application via MCP
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio

# Check status
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"webApplicationStatus","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

### Option 2: Start Web Application Directly

```bash
# Using startup script
./start.sh

# Or directly
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Option 3: Unified Application (Brainstorming + Assistant)

```bash
./start_unified.sh
```

## 🎮 Using MCP Server

The MCP server acts as the **control layer** for the entire application. You can manage everything through MCP tools.

### Start MCP Server

**Stdio Mode:**
```bash
python3 -m mcp.server --transport stdio
```

**WebSocket Mode:**
```bash
python3 -m mcp.server --transport websocket --host localhost --port 8080
```

### Available MCP Tools

#### Application Management
- `startWebApplication` - Start web app on port 8000
- `stopWebApplication` - Stop web app
- `webApplicationStatus` - Check web app status

#### User Management
- `createUser` - Create new user account
- `getUser` - Get user details by ID
- `updateUser` - Update user preferences
- `deleteUser` - Delete user account

#### Event Management
- `getEvent` - Get event details by ID
- `listEvents` - List events with filters

#### Notification Management
- `listNotifications` - List notifications with filters
- `planNotifications` - Plan notifications using LLM policy
- `cancelNotification` - Cancel scheduled notification

#### Calendar Management
- `syncCalendar` - Sync Google Calendar events for a user

#### Dashboard
- `getDashboardStats` - Get dashboard statistics

### Example: Complete Workflow via MCP

```bash
# 1. Start web application
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio

# 2. Create a user
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"John Doe","email":"john@example.com"}}}' | \
python3 -m mcp.server --transport stdio

# 3. Get dashboard statistics
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"getDashboardStats","arguments":{}}}' | \
python3 -m mcp.server --transport stdio

# 4. Stop web application
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"stopWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

### Integration with Claude Desktop

Add to Claude Desktop config:
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

## 🌐 Web Application

### Access Points

Once the web application is running (port 8000):

- **🏠 Main Dashboard**: http://localhost:8000
- **🧠 Brainstorming Mode**: http://localhost:8000/brainstorm (if unified mode)
- **📅 Personal Assistant**: http://localhost:8000/personal
- **⚙️ Admin Panel**: http://localhost:8000/admin
  - Default login: `admin` / `admin123`
- **📚 API Documentation**: http://localhost:8000/docs
  - Interactive Swagger UI
- **🔧 Health Check**: http://localhost:8000/health

### Features

#### User Management
- Create, edit, delete users
- Set notification preferences
- Configure quiet hours and channels
- Phone and email settings

#### Calendar Integration
- Google Calendar sync
- Event management
- OAuth authentication
- Calendar webhook handling

#### Notifications
- Intelligent notification planning
- Email notifications
- Voice call notifications
- RSVP links in emails

#### Admin Interface
- Dashboard with system overview
- User management
- Event management
- Notification history
- Audit logs

### API Endpoints

#### Core API
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `GET /api/events/` - List events
- `GET /api/notifications/` - List notifications

#### Testing API
- `GET /testing/status` - Check mock mode status
- `POST /testing/mock/test-call/{user_id}` - Test mock call
- `POST /testing/mock/test-email/{user_id}` - Test mock email

## 💡 Examples

### Create User via MCP

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"Jane Smith","email":"jane@example.com","phone_e164":"+15551234567","channel_pref":"both"}}}' | \
python3 -m mcp.server --transport stdio
```

### Plan Notifications via MCP

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"planNotifications","arguments":{"user_id":"user-123"}}}' | \
python3 -m mcp.server --transport stdio
```

### Check Web App Status

```bash
# Via MCP
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"webApplicationStatus","arguments":{}}}' | \
python3 -m mcp.server --transport stdio

# Or directly
curl http://localhost:8000/health
```

### Check Status Script

```bash
# Quick status check
./mcp/scripts/check_webapp.sh
```

## 🔧 Troubleshooting

### Web Application Won't Start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing processes
pkill -f "uvicorn app.main"

# Check logs
tail -f logs/webapp_stderr.log
```

### MCP Server Errors

```bash
# Check if MCP server can start
python3 -m mcp.server --transport stdio

# Check imports
python3 -c "from mcp import server; print('OK')"
```

### Database Issues

```bash
# Reinitialize database
rm assistant.db
python3 scripts/init_db.py
```

### Module Not Found

```bash
# Ensure you're in the correct directory
cd /home/uwisiyose/ASSISTANT

# Check PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH

# Reinstall MCP server
cd mcp
pip install -e ".[app-management]"
```

## 📚 Additional Documentation

### MCP Server Documentation
- **MCP Quick Start**: `mcp/QUICK_START_BRAIN.md`
- **MCP as Brain**: `mcp/docs/MCP_AS_BRAIN.md`
- **Adding Users**: `mcp/docs/ADD_USER_GUIDE.md`
- **How It Works**: `mcp/docs/HOW_IT_WORKS.md`
- **Usage Guide**: `mcp/docs/USAGE_GUIDE.md`
- **Troubleshooting**: `mcp/docs/TROUBLESHOOTING.md`
- **Installation**: `mcp/docs/INSTALLATION.md`

### Web Application Documentation
- **Testing Guide**: `TESTING_GUIDE.md`
- **Architecture**: `ARCHITECTURE.md`
- **Deployment**: `DEPLOYMENT.md`

## 🎯 Common Workflows

### Workflow 1: Start Everything via MCP

```bash
# 1. Start web app
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio

# 2. Create user
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"John","email":"john@example.com"}}}' | \
python3 -m mcp.server --transport stdio

# 3. Access web UI
# Open: http://localhost:8000/admin
```

### Workflow 2: Traditional Start

```bash
# 1. Start web app directly
./start.sh

# 2. Access web UI
# Open: http://localhost:8000/admin

# 3. Create user via web UI
```

### Workflow 3: Development Mode

```bash
# Terminal 1: Web app with auto-reload
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: MCP server
python3 -m mcp.server --transport websocket --host localhost --port 8080

# Terminal 3: Test client
python3 mcp/examples/test_websocket.py
```

## 🔐 Security Notes

- Default admin credentials: `admin` / `admin123` (change in production!)
- OAuth tokens are encrypted
- RSVP tokens use HMAC signing
- Use HTTPS in production

## 📦 Project Structure

```
ASSISTANT/
├── app/                    # Web application code
│   ├── main.py            # FastAPI app
│   ├── models.py          # Database models
│   ├── routes/            # API routes
│   ├── templates/         # Admin UI
│   └── ...
├── mcp/                    # MCP server
│   ├── server.py          # MCP server main
│   ├── capabilities/      # MCP tools/resources/prompts
│   ├── core/              # MCP protocol implementation
│   ├── docs/              # MCP documentation
│   └── ...
├── scripts/               # Utility scripts
├── logs/                  # Application logs
├── assistant.db           # SQLite database
├── start.sh              # Start script
└── README.md              # Main README
```

## ✅ Verification

After setup, verify everything works:

```bash
# 1. Check web app status
./mcp/scripts/check_webapp.sh

# 2. Test MCP server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"getDashboardStats","arguments":{}}}' | \
python3 -m mcp.server --transport stdio

# 3. Test web app health
curl http://localhost:8000/health
```

## 🎉 You're Ready!

Your Assistant application is now set up with:
- ✅ Web application with admin UI
- ✅ MCP server for programmatic control
- ✅ User and event management
- ✅ Notification planning
- ✅ Calendar integration

Start with MCP server or web application - both work independently and together!

## 🆘 Need Help?

- Check troubleshooting section above
- Review detailed documentation in `mcp/docs/`
- Check logs in `logs/` directory
- Review API documentation at http://localhost:8000/docs
