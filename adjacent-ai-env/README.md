# AI Coding Environment - Adjacent to MCP Server

An independent AI Coding Environment that works alongside (not inside) the existing MCP server. Provides file operations, code editing, search, and task execution capabilities via VS Code extension.

## 🎯 Key Principles

- ✅ **MCP Server Untouched**: Existing MCP server remains completely unchanged
- ✅ **Independent Process**: CWS runs as separate daemon
- ✅ **OSS-Only**: All dependencies are open source
- ✅ **Security-First**: Workspace sandboxing, policy enforcement
- ✅ **Test-Gated**: All tests must pass

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────┐
│      VS Code Extension (TypeScript)                │
│  ┌──────────────┐         ┌──────────────┐        │
│  │ MCP Client   │         │ CWS Client   │        │
│  └──────┬───────┘         └──────┬───────┘        │
└─────────┼─────────────────────────┼───────────────┘
          │                         │
          ▼                         ▼
┌────────────────────┐   ┌──────────────────────┐
│  MCP Server        │   │ Coding Workspace     │
│  (Existing)        │   │ Service (CWS)        │
│                    │   │                      │
│  • Tools           │   │  • File Operations  │
│  • Resources       │   │  • Search/Grep      │
│  • Prompts         │   │  • Code Editing      │
│                    │   │  • Task Execution    │
└────────────────────┘   └──────────────────────┘
```

## 📦 Components

### 1. Coding Workspace Service (CWS)

Standalone daemon providing:
- **File Operations**: Read, write, create, delete, move, list
- **Search**: Full-text search, regex search, symbol search
- **Code Editing**: Batch edits, formatting, diff/patch
- **Tasks**: Run commands, execute tests, terminal operations
- **Security**: Policy enforcement, workspace sandboxing

**Location**: `coding-workspace-service/`

**Transport**: Stdio (default) or WebSocket

### 2. VS Code Extension

Extension providing:
- **Dual Connections**: MCP server (existing) + CWS (new)
- **Unified UX**: Commands, tree views, status bar
- **AI Agent Hooks**: Commands for AI workflows

**Location**: `vscode-extension/`

## 🚀 Quick Start

### 1. Install Coding Workspace Service

```bash
cd adjacent-ai-env/coding-workspace-service
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Install VS Code Extension

```bash
cd adjacent-ai-env/vscode-extension
npm install
npm run compile
npm run package
code --install-extension *.vsix
```

### 3. Configure Workspace Policy

Create `.cws-policy.json` in workspace root:

```json
{
  "allowedPaths": ["**/*"],
  "deniedPaths": [".git/**", "node_modules/**"],
  "maxFileSize": 10485760,
  "allowedCommands": ["npm", "python3", "make"],
  "confirmationRequired": ["delete", "applyPatch", "task.run"]
}
```

### 4. Run CWS

```bash
# Stdio mode
python3 -m cws.main --transport stdio

# WebSocket mode
python3 -m cws.main --transport websocket --host localhost --port 9090
```

## 📚 Documentation

- **[CWS Quick Start](coding-workspace-service/docs/QUICKSTART.md)** - Getting started with CWS
- **[CWS Message Catalog](coding-workspace-service/docs/MESSAGE_CATALOG.md)** - Complete API reference
- **[Policy Guide](coding-workspace-service/docs/POLICY.md)** - Security policy configuration
- **[Troubleshooting](coding-workspace-service/docs/TROUBLESHOOTING.md)** - Common issues
- **[VS Code Extension README](vscode-extension/README.md)** - Extension documentation

## ✅ Features

### File Operations
- ✅ Read files (text/binary with base64)
- ✅ Write files (atomic writes)
- ✅ Create files/directories
- ✅ Delete files/directories
- ✅ Move/rename files
- ✅ List directory contents

### Search & Code
- ✅ Full-text search with regex support
- ✅ Symbol search (functions, classes)
- ✅ Batch code edits
- ✅ Code formatting
- ✅ Diff generation

### Tasks & Terminal
- ✅ Run commands with policy enforcement
- ✅ Build/test task execution
- ✅ Terminal session management

### Security
- ✅ Workspace root sandboxing
- ✅ Path traversal prevention
- ✅ Policy-based access control
- ✅ Confirmation requirements
- ✅ File size limits

## 🧪 Testing

```bash
# Run all tests
cd coding-workspace-service
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## 📋 Implementation Status

See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for complete status.

## 🔒 Security

- Workspace root sandboxing
- Path traversal prevention
- Policy enforcement
- Command allowlist
- Confirmation requirements

## 📄 License

MIT License - All components are open source

## 🆘 Support

See [TROUBLESHOOTING.md](coding-workspace-service/docs/TROUBLESHOOTING.md) for help.
