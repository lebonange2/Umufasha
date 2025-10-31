# Running the AI Coding Environment

## Overview

The AI Coding Environment consists of **two independent services** that work together:

1. **MCP Server** (existing) - Runs on port 8080 (WebSocket) or stdio
2. **CWS (Coding Workspace Service)** - Runs on port 9090 (WebSocket) or stdio

They are **separate processes** - the MCP server does not start or manage CWS.

## Running Both Services

### Option 1: Separate Terminals (Recommended)

**Terminal 1: MCP Server**
```bash
cd /home/uwisiyose/ASSISTANT
python3 -m mcp.server --transport websocket --host localhost --port 8080
```

**Terminal 2: CWS**
```bash
cd /home/uwisiyose/ASSISTANT/adjacent-ai-env/coding-workspace-service
source venv/bin/activate  # if using venv
python3 -m cws.main --transport websocket --host localhost --port 9090
```

### Option 2: Stdio Mode (for VS Code Extension)

**VS Code Extension will start both automatically** based on your configuration:

```json
{
  "assistantAiCodingEnv.mcp.command": "python3",
  "assistantAiCodingEnv.mcp.args": ["-m", "mcp.server", "--transport", "stdio"],
  "assistantAiCodingEnv.cws.command": "python3",
  "assistantAiCodingEnv.cws.args": ["-m", "cws.main", "--transport", "stdio"]
}
```

The extension will spawn both processes automatically when you open VS Code.

### Option 3: Background Processes

**Terminal 1: Start MCP Server in background**
```bash
cd /home/uwisiyose/ASSISTANT
python3 -m mcp.server --transport websocket --host localhost --port 8080 > mcp.log 2>&1 &
echo $! > mcp.pid
```

**Terminal 2: Start CWS in background**
```bash
cd /home/uwisiyose/ASSISTANT/adjacent-ai-env/coding-workspace-service
python3 -m cws.main --transport websocket --host localhost --port 9090 > cws.log 2>&1 &
echo $! > cws.pid
```

**Stop both:**
```bash
kill $(cat mcp.pid)
kill $(cat cws.pid)
```

## Quick Start Script

Create a helper script to start both:

```bash
#!/bin/bash
# start-services.sh

# Start MCP Server
cd /home/uwisiyose/ASSISTANT
python3 -m mcp.server --transport websocket --host localhost --port 8080 &
MCP_PID=$!
echo "MCP Server started (PID: $MCP_PID)"

# Start CWS
cd /home/uwisiyose/ASSISTANT/adjacent-ai-env/coding-workspace-service
python3 -m cws.main --transport websocket --host localhost --port 9090 &
CWS_PID=$!
echo "CWS started (PID: $CWS_PID)"

echo "Both services running. Press Ctrl+C to stop."
echo "MCP Server: http://localhost:8080/mcp"
echo "CWS: http://localhost:9090"

# Wait for interrupt
trap "kill $MCP_PID $CWS_PID; exit" INT TERM
wait
```

## Using from VS Code Extension

The VS Code extension connects to **both** services automatically:

1. **Install Extension**: Package and install the VS Code extension
2. **Configure**: Set paths in VS Code settings
3. **Use**: Extension starts both processes automatically

### VS Code Settings

Add to `.vscode/settings.json`:

```json
{
  "assistantAiCodingEnv.mcp.command": "python3",
  "assistantAiCodingEnv.mcp.args": ["-m", "mcp.server", "--transport", "stdio"],
  "assistantAiCodingEnv.mcp.cwd": "/home/uwisiyose/ASSISTANT",
  "assistantAiCodingEnv.cws.command": "python3",
  "assistantAiCodingEnv.cws.args": ["-m", "cws.main", "--transport", "stdio"],
  "assistantAiCodingEnv.cws.cwd": "/home/uwisiyose/ASSISTANT/adjacent-ai-env/coding-workspace-service"
}
```

## Verifying Both Are Running

### Check MCP Server
```bash
# Check if port 8080 is listening
lsof -i :8080

# Test connection
curl http://localhost:8080/health  # If health endpoint exists
```

### Check CWS
```bash
# Check if port 9090 is listening
lsof -i :9090

# Test connection (via WebSocket client)
python3 adjacent-ai-env/coding-workspace-service/examples/test_client.py
```

### Check Both via VS Code Extension

The extension status bar will show:
- `MCP: ✓` - MCP server connected
- `CWS: ✓` - CWS connected

## Using Both Services

### From MCP Server (Existing Tools)
```bash
# Use existing MCP tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

### From CWS (New Coding Operations)
```bash
# Use CWS file operations
echo '{"jsonrpc":"2.0","id":1,"method":"fs.read","params":{"path":"README.md"}}' | \
python3 -m cws.main --transport stdio
```

### From VS Code Extension

The extension provides commands that use **both**:
- **MCP Tools**: Access via "MCP Tools" tree view
- **CWS Operations**: Access via "CWS: Open File", "CWS: Write File", etc.

## Architecture Recap

```
┌─────────────────────────────────────────┐
│      VS Code Extension                   │
│  ┌─────────────┐  ┌──────────────┐     │
│  │ MCP Client  │  │ CWS Client   │     │
│  └──────┬──────┘  └──────┬───────┘     │
└─────────┼─────────────────┼──────────────┘
          │                 │
          ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│  MCP Server      │  │  CWS              │
│  (Port 8080)     │  │  (Port 9090)      │
│                  │  │                   │
│  • Tools         │  │  • File Ops       │
│  • Resources     │  │  • Search         │
│  • Prompts       │  │  • Edits          │
└─────────────────┘  └──────────────────┘
```

## Important Notes

1. **Separate Processes**: MCP server and CWS are **independent** processes
2. **Different Ports**: MCP uses 8080, CWS uses 9090
3. **Separate Commands**: Different commands to start each
4. **VS Code Extension**: Automatically manages both when configured
5. **No Dependency**: CWS does not depend on MCP server (or vice versa)

## Troubleshooting

### MCP Server Not Starting
```bash
# Check dependencies
pip list | grep mcp

# Check port
lsof -i :8080

# Start manually
python3 -m mcp.server --transport stdio
```

### CWS Not Starting
```bash
# Install CWS
cd adjacent-ai-env/coding-workspace-service
pip install -e .

# Check workspace root
python3 -m cws.main --transport stdio --workspace-root /home/uwisiyose/ASSISTANT

# Check logs
tail -f cws.log
```

### VS Code Extension Not Connecting
1. Check VS Code settings are correct
2. Check both services can be started manually
3. Check VS Code extension logs (Output panel)
4. Verify paths in settings.json are correct

## Next Steps

1. **Start Both Services**: Use separate terminals or background processes
2. **Install VS Code Extension**: For unified UX
3. **Configure Policy**: Create `.cws-policy.json` in workspace root
4. **Test Operations**: Try file operations via CWS, MCP tools via MCP server

