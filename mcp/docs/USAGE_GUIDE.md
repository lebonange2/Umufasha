# MCP Server Usage Guide

## Understanding How It Works

### Important: MCP Server vs Web Application Processes

The **MCP server** and the **web application** are **separate processes**:

- **MCP Server**: Handles MCP protocol requests (stdio/WebSocket)
- **Web Application**: FastAPI app running on port 8000

When you use `startWebApplication`:
1. MCP server starts the web application process
2. Web application runs **independently** (detached process)
3. MCP server can exit - web app keeps running!

### Why This Happens

When you pipe input to the MCP server:
```bash
echo '...' | python3 -m mcp.server --transport stdio
```

1. MCP server receives the request
2. Starts web application process (in background)
3. Returns response
4. Input closes (EOF) → MCP server exits
5. **Web application keeps running** (started with `start_new_session=True`)

## How to Check if Web App is Running

### Method 1: Check Status via MCP

```bash
# First, start MCP server (leave it running)
python3 -m mcp.server --transport stdio

# In another terminal, or use a script:
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"webApplicationStatus","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

### Method 2: Direct System Check

```bash
# Check if process is running
ps aux | grep "uvicorn app.main" | grep -v grep

# Check if port 8000 is in use
lsof -i :8000

# Test health endpoint
curl http://localhost:8000/health
```

### Method 3: Check Log Files

After starting via MCP, logs are written to:
- `logs/webapp_stdout.log` - Standard output
- `logs/webapp_stderr.log` - Error output

```bash
# Check logs
tail -f logs/webapp_stdout.log
tail -f logs/webapp_stderr.log
```

## Proper Workflow

### Option 1: Keep MCP Server Running (Recommended)

**Terminal 1: Start MCP Server**
```bash
cd /home/uwisiyose/ASSISTANT
python3 -m mcp.server --transport stdio
```

**Terminal 2: Send Requests**
```bash
# Start web app
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio

# Check status
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"webApplicationStatus","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

### Option 2: Use WebSocket Mode

**Terminal 1: Start MCP Server (WebSocket)**
```bash
python3 -m mcp.server --transport websocket --host localhost --port 8080
```

**Terminal 2: Use Client**
```bash
python3 mcp/examples/test_websocket.py
```

### Option 3: Interactive Script

```bash
#!/bin/bash
# Start web app via MCP
python3 << 'EOF'
import asyncio
import sys
from mcp.examples.hello_client import SimpleMCPClient

async def main():
    client = SimpleMCPClient()
    await client.initialize()
    
    # Start web app
    result = await client.call_tool("startWebApplication", {})
    print("Result:", result)
    
    # Wait a bit
    await asyncio.sleep(3)
    
    # Check status
    status = await client.call_tool("webApplicationStatus", {})
    print("Status:", status)

asyncio.run(main())
EOF
```

## Verification Steps

After starting the web application:

1. **Check Process**
   ```bash
   ps aux | grep uvicorn | grep -v grep
   ```

2. **Check Port**
   ```bash
   lsof -i :8000
   ```

3. **Test Health Endpoint**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Open in Browser**
   - http://localhost:8000/admin
   - http://localhost:8000/docs

## Troubleshooting

### Process Started But Not Running

**Problem**: MCP reports "starting" but process dies immediately.

**Solution**:
1. Check error logs: `logs/webapp_stderr.log`
2. Check if dependencies are installed
3. Check if database exists: `ls assistant.db`
4. Verify PYTHONPATH is set correctly

### Can't Access Web App

**Problem**: Process is running but can't access http://localhost:8000

**Solutions**:
1. Check firewall: `sudo iptables -L`
2. Verify process is listening: `netstat -tlnp | grep 8000`
3. Check logs for errors
4. Try accessing from another terminal: `curl http://localhost:8000/health`

### Process Dies After Starting

**Problem**: Web app starts then exits immediately.

**Check**:
```bash
# View error log
tail -50 logs/webapp_stderr.log

# Check for database errors
python3 -c "from app.database import engine; print('DB OK')"

# Check for import errors
python3 -c "from app.main import app; print('App OK')"
```

## Best Practices

1. **Start MCP Server in Background**: Use `screen` or `tmux` to keep it running
2. **Check Logs Regularly**: Monitor `logs/webapp_stdout.log` and `logs/webapp_stderr.log`
3. **Use Status Tool**: Regularly check `webApplicationStatus` to verify health
4. **Keep MCP Server Running**: Don't use pipes for long-running operations

## Example: Complete Workflow

```bash
# 1. Start MCP server in background (or separate terminal)
python3 -m mcp.server --transport stdio &

# 2. Start web application
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio

# 3. Wait a few seconds
sleep 5

# 4. Verify it's running
curl http://localhost:8000/health

# 5. Access web UI
# Open: http://localhost:8000/admin

# 6. Stop when done
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"stopWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

