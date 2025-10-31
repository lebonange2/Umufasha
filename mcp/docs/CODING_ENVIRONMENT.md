# Coding Environment Tools

The MCP server now includes coding environment tools for file operations, search, and task execution.

## Available Tools

### File Operations

#### readFile
Read file content from workspace.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "readFile",
    "arguments": {
      "workspaceRoot": ".",
      "path": "README.md"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\n  \"path\": \"README.md\",\n  \"size\": 1234,\n  \"mtime\": \"2024-01-01T12:00:00\",\n  \"hash\": \"sha256:...\",\n  \"isBinary\": false,\n  \"content\": \"...\"\n}"
    }]
  }
}
```

#### writeFile
Write file content to workspace.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "writeFile",
    "arguments": {
      "workspaceRoot": ".",
      "path": "test.txt",
      "contents": "Hello, World!",
      "options": {
        "atomic": true,
        "createIfMissing": true
      }
    }
  }
}
```

#### listFiles
List directory contents.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "listFiles",
    "arguments": {
      "workspaceRoot": ".",
      "path": ".",
      "options": {
        "recursive": false,
        "maxEntries": 100
      }
    }
  }
}
```

### Search Operations

#### searchFiles
Search for text in files.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "searchFiles",
    "arguments": {
      "workspaceRoot": ".",
      "query": "function",
      "options": {
        "regex": false,
        "caseSensitive": false,
        "globs": ["**/*.py"],
        "maxResults": 100
      }
    }
  }
}
```

### Task Operations

#### runCommand
Run a command in the workspace.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "runCommand",
    "arguments": {
      "workspaceRoot": ".",
      "command": "python3",
      "args": ["-m", "pytest"],
      "options": {
        "timeout": 60,
        "confirmed": true
      }
    }
  }
}
```

## Policy Configuration

Create `.cws-policy.json` in your workspace root to configure security:

```json
{
  "allowedPaths": ["**/*"],
  "deniedPaths": [".git/**", "node_modules/**"],
  "maxFileSize": 10485760,
  "maxEditSize": 1048576,
  "allowedCommands": ["npm", "python3", "make"],
  "envAllowlist": ["PATH", "HOME"],
  "confirmationRequired": ["delete", "applyPatch", "task.run"]
}
```

## Security Features

- **Workspace Root Sandboxing**: All paths validated against workspace root
- **Path Traversal Prevention**: Blocks attempts to access files outside workspace
- **Policy Enforcement**: Configurable allowlists for paths and commands
- **Confirmation Requirements**: Explicit consent for destructive operations
- **File Size Limits**: Configurable maximum file and edit sizes

## Examples

### Read a File

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"readFile","arguments":{"path":"README.md"}}}' | \
python3 -m mcp.server --transport stdio
```

### List Files

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"listFiles","arguments":{"path":"."}}}' | \
python3 -m mcp.server --transport stdio
```

### Search for Text

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"searchFiles","arguments":{"query":"def "}}}' | \
python3 -m mcp.server --transport stdio
```

### Run a Command

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"runCommand","arguments":{"command":"python3","args":["--version"],"options":{"confirmed":true}}}}' | \
python3 -m mcp.server --transport stdio
```

## Integration

These tools are now part of the MCP server - no separate service needed! Just use the MCP server as normal, and the coding environment tools are available.

## Notes

- All file operations are relative to `workspaceRoot` (defaults to current directory)
- Path traversal attempts are blocked
- Commands require policy allowlist and confirmation (if configured)
- Binary files are base64 encoded in responses

