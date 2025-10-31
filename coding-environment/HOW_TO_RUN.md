# How to Run the AI Coding Environment

## Quick Answer

The Coding Environment (CWS) is **separate** from the MCP server. You need to run **both** independently:

1. **MCP Server** (existing) - for your app management tools
2. **CWS** (new) - for file operations, search, edits, tasks

## Quick Start

### Method 1: Start Both with Helper Script

```bash
cd /home/uwisiyose/ASSISTANT
./adjacent-ai-env/scripts/start-both.sh
```

This starts both:
- **MCP Server** on port 8080 (WebSocket)
- **CWS** on port 9090 (WebSocket)

Stop both:
```bash
./adjacent-ai-env/scripts/stop-both.sh
```

### Method 2: Start Manually (Separate Terminals)

**Terminal 1: MCP Server**
```bash
cd /home/uwisiyose/ASSISTANT
python3 -m mcp.server --transport websocket --host localhost --port 8080
```

**Terminal 2: CWS**
```bash
cd /home/uwisiyose/ASSISTANT/adjacent-ai-env/coding-workspace-service
python3 -m cws.main --transport websocket --host localhost --port 9090
```

### Method 3: Stdio Mode (for VS Code Extension)

The VS Code extension will automatically start both when configured:

```json
{
  "assistantAiCodingEnv.mcp.command": "python3",
  "assistantAiCodingEnv.mcp.args": ["-m", "mcp.server", "--transport", "stdio"],
  "assistantAiCodingEnv.cws.command": "python3",
  "assistantAiCodingEnv.cws.args": ["-m", "cws.main", "--transport", "stdio"]
}
```

## Understanding the Architecture

The Coding Environment is **adjacent** to (not inside) the MCP server:

```
┌─────────────────────────────────────────┐
│         VS Code Extension               │
│  ┌─────────────┐  ┌──────────────┐      │
│  │ MCP Client  │  │ CWS Client   │      │
│  └──────┬──────┘  └──────┬──────┘      │
└─────────┼─────────────────┼─────────────┘
          │                 │
          ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│  MCP Server      │  │  CWS              │
│  (Independent)   │  │  (Independent)   │
│                  │  │                   │
│  Port: 8080      │  │  Port: 9090      │
└─────────────────┘  └──────────────────┘
```

**Key Point**: They are **two separate processes** - neither manages the other.

## What Each Service Does

### MCP Server (Existing)
- Application management (start/stop web app)
- User management (create/update users)
- Event and notification management
- Dashboard statistics
- Calendar synchronization

**Access**: Port 8080 (WebSocket) or stdio

### CWS (New)
- File operations (read, write, create, delete, move, list)
- Search operations (find text, find symbols)
- Code editing (batch edits, formatting)
- Task execution (run commands, build, test)
- Terminal operations

**Access**: Port 9090 (WebSocket) or stdio

## Using Both Services

### From Command Line

**Use MCP Server tools:**
```bash
# Start web app via MCP
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

**Use CWS operations:**
```bash
# Read file via CWS
echo '{"jsonrpc":"2.0","id":1,"method":"fs.read","params":{"path":"README.md"}}' | \
python3 -m cws.main --transport stdio
```

### From VS Code Extension

Once both are running, the VS Code extension provides:
- **MCP Tools**: View in "MCP Tools" tree view
- **CWS Operations**: Use commands like "CWS: Open File", "CWS: Search"

## Installation Steps

### 1. Install CWS

```bash
cd /home/uwisiyose/ASSISTANT/adjacent-ai-env/coding-workspace-service
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Install VS Code Extension (Optional)

```bash
cd adjacent-ai-env/vscode-extension
npm install
npm run compile
npm run package
code --install-extension *.vsix
```

### 3. Configure Policy (Optional)

Create `.cws-policy.json` in workspace root (see `.cws-policy.json.example`)

## Verify Both Are Running

### Check MCP Server
```bash
lsof -i :8080
# Should show python process
```

### Check CWS
```bash
lsof -i :9090
# Should show python process
```

### Check via VS Code Extension
- Status bar shows: `MCP: ✓ CWS: ✓`
- Tree views show: "MCP Tools" and "Workspace (CWS)"

## Common Questions

### Q: Does MCP server start CWS?
**A**: No. They are separate processes. You need to start both.

### Q: Can I run CWS from MCP server?
**A**: No. CWS is a separate daemon. MCP server doesn't manage it.

### Q: How do I use both together?
**A**: 
1. Start both (separate terminals or script)
2. Use VS Code extension (connects to both)
3. Or use them independently via their respective clients

### Q: What port does CWS use?
**A**: Port 9090 (WebSocket) or stdio (default)

### Q: Can I change CWS port?
**A**: Yes:
```bash
python3 -m cws.main --transport websocket --host localhost --port 9999
```

## Troubleshooting

### Both Services Not Starting
1. Check dependencies are installed
2. Check ports 8080 and 9090 are available
3. Check Python version (3.10+)
4. Check workspace root permissions

### VS Code Extension Not Connecting
1. Check VS Code settings are correct
2. Check both services can start manually
3. Check VS Code extension logs (Output panel)
4. Verify command paths in settings.json

### Permission Errors
1. Check workspace root permissions
2. Check `.cws-policy.json` allows operations
3. Check file permissions in workspace

## Next Steps

1. **Start Both**: Use `start-both.sh` script or separate terminals
2. **Test Operations**: Try file operations via CWS
3. **Use VS Code Extension**: For unified UX
4. **Configure Policy**: Customize `.cws-policy.json` for your needs

