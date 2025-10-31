# Coding Environment - Integrated into MCP Server

The Coding Environment is now **integrated as tools** in the MCP server. All file operations, search, and task execution capabilities are available directly through MCP tools.

## 🎯 Status

**✅ Integrated**: The coding environment functionality is now part of the MCP server as tools. No separate service needed!

## 📦 Available Tools

The following coding environment tools are available in the MCP server:

### File Operations
- **`readFile`** - Read file content from workspace
- **`writeFile`** - Write file content to workspace
- **`listFiles`** - List directory contents

### Search Operations
- **`searchFiles`** - Search for text in files

### Task Operations
- **`runCommand`** - Run a command in the workspace

## 🚀 Usage

All tools are available through the MCP server:

```bash
# Read a file
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"readFile","arguments":{"path":"README.md"}}}' | \
python3 -m mcp.server --transport stdio

# List files
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"listFiles","arguments":{"path":"."}}}' | \
python3 -m mcp.server --transport stdio

# Search files
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"searchFiles","arguments":{"query":"def "}}}' | \
python3 -m mcp.server --transport stdio

# Run command
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"runCommand","arguments":{"command":"python3","args":["--version"],"options":{"confirmed":true}}}}' | \
python3 -m mcp.server --transport stdio
```

## 📚 Documentation

- **[Coding Environment Guide](../mcp/docs/CODING_ENVIRONMENT.md)** - Complete tool documentation
- **[Coding Environment Examples](../mcp/docs/CODING_ENVIRONMENT_EXAMPLES.md)** - Usage examples
- **[MCP README](../mcp/README.md)** - MCP server documentation

## 🔒 Security

Security policy is configured via `.cws-policy.json` in workspace root:

```json
{
  "allowedPaths": ["**/*"],
  "deniedPaths": [".git/**", "node_modules/**"],
  "maxFileSize": 10485760,
  "allowedCommands": ["python3", "npm", "make"],
  "confirmationRequired": ["runCommand"]
}
```

## ✨ Key Features

- ✅ **Integrated**: No separate service needed - use MCP server directly
- ✅ **Security**: Workspace sandboxing, path traversal prevention
- ✅ **Policy**: Configurable allowlists for paths and commands
- ✅ **Unified**: All tools available through single MCP server

## 📝 Note

The old separate CWS service code is preserved in `coding-workspace-service/` for reference, but the functionality is now integrated directly into the MCP server as tools.
