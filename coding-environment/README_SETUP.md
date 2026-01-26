# Coding Environment Setup and Run

This directory contains scripts to set up and run only the coding environment components (CWS + MCP Server) independently from the main FastAPI application.

## Quick Start

### Setup and Run

```bash
cd coding-environment
./setup_and_run.sh
```

This script will:
1. Check Python version (requires 3.10+)
2. Create/activate virtual environment in `coding-environment/venv/`
3. Install CWS dependencies
4. Install MCP server dependencies
5. Start MCP Server on port 8080 (WebSocket)
6. Start CWS on port 9090 (WebSocket)

### Stop Services

```bash
cd coding-environment
./stop.sh
```

Or press `Ctrl+C` in the terminal where services are running.

## Configuration

You can customize the setup using environment variables:

```bash
# Custom ports
export MCP_PORT=8080
export CWS_PORT=9090

# Custom workspace root
export WORKSPACE_ROOT=/path/to/workspace

# Transport type (websocket or stdio)
export TRANSPORT=websocket

# Bind host (for RunPod or external access)
export BIND_HOST_OVERRIDE=0.0.0.0  # Use 0.0.0.0 for RunPod port forwarding

# Run setup
./setup_and_run.sh
```

### RunPod Support

The script automatically detects RunPod environments and binds to `0.0.0.0` instead of `localhost` to enable port forwarding. Detection is based on:
- `RUNPOD_POD_ID` environment variable
- Presence of `/workspace` directory
- Presence of `/runpod-volume` directory

For RunPod:
1. The script will automatically use `0.0.0.0` as the bind host
2. **Ignore Docker build messages**: If you see Docker build instructions in RunPod UI, you can ignore them. The setup script runs directly without Docker.
3. Configure ports in RunPod UI:
   - Go to your pod's page
   - Find "Ports" or "Network" section
   - Add port mappings for `8080` (MCP Server) and `9090` (CWS)
4. Access via RunPod's port forwarding URLs:
   - `https://xxxxx-8080.proxy.runpod.net` (MCP Server)
   - `https://xxxxx-9090.proxy.runpod.net` (CWS)

## Services

### MCP Server
- **Port**: 8080 (default, configurable via `MCP_PORT`)
- **Transport**: WebSocket (default) or stdio
- **Location**: `../mcp/` (relative from coding-environment)
- **Log**: `coding-environment/.pids/mcp.log`

### CWS (Coding Workspace Service)
- **Port**: 9090 (default, configurable via `CWS_PORT`)
- **Transport**: WebSocket (default) or stdio
- **Location**: `coding-environment/coding-workspace-service/`
- **Workspace Root**: Parent directory (ASSISTANT) by default
- **Log**: `coding-environment/.pids/cws.log`

## Directory Structure

```
coding-environment/
├── setup_and_run.sh          # Main setup and run script
├── stop.sh                   # Stop services script
├── venv/                     # Virtual environment (created by script)
├── .pids/                    # PID files and logs (created by script)
│   ├── mcp.pid              # MCP Server process ID
│   ├── cws.pid               # CWS process ID
│   ├── mcp.log               # MCP Server log
│   └── cws.log                # CWS log
└── coding-workspace-service/  # CWS source code
```

## Dependencies

The script automatically installs:
- **CWS dependencies**: From `coding-workspace-service/requirements.txt`
- **MCP server dependencies**: From `mcp/pyproject.toml` (with app-management extras)

## Troubleshooting

### Port Already in Use

If a port is already in use, the script will warn you. To free the port:

```bash
# Check what's using the port
lsof -i :8080
lsof -i :9090

# Kill the process
kill <PID>
```

### Services Not Starting

1. Check logs in `coding-environment/.pids/`:
   ```bash
   tail -f coding-environment/.pids/mcp.log
   tail -f coding-environment/.pids/cws.log
   ```

2. Verify dependencies are installed:
   ```bash
   cd coding-environment
   source venv/bin/activate
   pip list | grep -E "(cws|mcp)"
   ```

3. Check Python version:
   ```bash
   python3 --version  # Should be 3.10+
   ```

### Virtual Environment Issues

If the virtual environment is corrupted:

```bash
cd coding-environment
rm -rf venv
./setup_and_run.sh  # Will recreate venv
```

## Usage Examples

### Start with Custom Ports

```bash
export MCP_PORT=8888
export CWS_PORT=9999
./setup_and_run.sh
```

### Start in Stdio Mode (for VS Code Extension)

```bash
export TRANSPORT=stdio
./setup_and_run.sh
```

### Start with Custom Workspace

```bash
export WORKSPACE_ROOT=/home/user/my-project
./setup_and_run.sh
```

## Integration with Main Application

The coding environment runs **independently** from the main FastAPI application. You can:
- Run the coding environment separately for development
- Run the main application separately for web features
- Run both simultaneously (they use different ports)

## Next Steps

After starting the services:
1. **Test MCP Server**: Connect to `http://localhost:8080`
2. **Test CWS**: Connect to `http://localhost:9090`
3. **Use VS Code Extension**: Configure to use stdio transport
4. **Use from CLI**: Use JSON-RPC clients to interact with services

For more information, see:
- `HOW_TO_RUN.md` - Detailed running instructions
- `QUICKSTART.md` - Quick start guide
- `coding-workspace-service/README.md` - CWS documentation
- `../mcp/README.md` - MCP server documentation
