# Assistant AI Coding Environment - VS Code Extension

VS Code extension that connects to both the MCP server (existing) and CWS (new) for unified AI coding environment.

## Features

- Dual connections: MCP server (existing) + CWS (new)
- File operations via CWS
- Search and code editing
- Task execution
- Tree views for workspace and MCP tools
- Status bar integration

## Installation

```bash
cd adjacent-ai-env/vscode-extension
npm install
npm run compile
```

## Package Extension

```bash
npm run package
```

This creates a `.vsix` file that can be installed:

```bash
code --install-extension assistant-ai-coding-env-1.0.0.vsix
```

## Configuration

Add to VS Code settings:

```json
{
  "assistantAiCodingEnv.mcp.command": "python3",
  "assistantAiCodingEnv.mcp.args": ["-m", "mcp.server", "--transport", "stdio"],
  "assistantAiCodingEnv.cws.command": "python3",
  "assistantAiCodingEnv.cws.args": ["-m", "cws.main", "--transport", "stdio"]
}
```

## Usage

The extension automatically connects to both MCP server and CWS on startup. Use the commands:

- `CWS: Open File` - Open file via CWS
- `CWS: Write File` - Save current file via CWS
- `CWS: Search` - Search workspace via CWS
- `CWS: Run Task` - Run command via CWS
- `CWS: Run Tests` - Run tests via CWS

## Architecture

- **MCP Client**: Connects to existing MCP server (read-only introspection)
- **CWS Client**: Connects to Coding Workspace Service (file operations, search, tasks)
- **Unified UX**: Commands, tree views, status bar

