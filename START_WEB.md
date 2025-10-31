# How to Start the Web Application

## Quick Start

The web application is **separate** from the MCP server. It's a FastAPI application that runs on port 8000.

### Option 1: Using the Start Script (Recommended)

```bash
# Make sure you're in the project directory
cd /home/uwisiyose/ASSISTANT

# Activate virtual environment (if not already active)
source venv/bin/activate

# Start the web application
./start.sh
```

This will start the application on **http://localhost:8000**

### Option 2: Using the Unified Start Script

The unified application includes both the assistant and brainstorming features:

```bash
./start_unified.sh
```

### Option 3: Direct Python Command

```bash
# Activate virtual environment
source venv/bin/activate

# Start with uvicorn
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Access the Web Application

Once started, you can access:

- **🌐 Main Dashboard**: http://localhost:8000
- **⚙️ Admin Panel**: http://localhost:8000/admin
  - Default login: `admin` / `admin123`
- **📚 API Documentation**: http://localhost:8000/docs
  - Interactive Swagger UI
- **🔧 Health Check**: http://localhost:8000/health

## If Using Unified Application

- **📊 Unified Dashboard**: http://localhost:8000
- **🧠 Brainstorming Mode**: http://localhost:8000/brainstorm
- **📅 Personal Assistant**: http://localhost:8000/personal
- **⚙️ Admin Panel**: http://localhost:8000/admin
- **📚 API Docs**: http://localhost:8000/docs

## Important Notes

1. **Different from MCP Server**: 
   - **Web Application**: Runs on port 8000 (HTTP/Web UI)
   - **MCP Server**: Runs on port 8080 (WebSocket/Protocol)

2. **Database Required**: The application needs `assistant.db` to exist. If it doesn't, the start script will initialize it automatically.

3. **Environment Variables**: Make sure `.env` file exists or the application may not work correctly.

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill existing processes
lsof -ti:8000 | xargs kill -9
```

### Database Issues

```bash
# Initialize database
python3 scripts/init_db.py
```

### Virtual Environment

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# If venv doesn't exist, run setup
./setup.sh
```

## Running Both Servers

You can run both the web application and MCP server simultaneously:

**Terminal 1: Web Application (Port 8000)**
```bash
./start.sh
```

**Terminal 2: MCP Server (Port 8080)**
```bash
python3 -m mcp.server --transport websocket --host localhost --port 8080
```

Both servers can run at the same time - they use different ports and serve different purposes!

