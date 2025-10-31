# Coding Environment Tools - Message Catalog

Complete API reference for Coding Environment tools integrated into MCP server.

## File Operations

### readFile

Read file content from workspace.

**Method**: `tools/call`  
**Tool Name**: `readFile`

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

**Parameters:**
- `path` (required): File path relative to workspace root
- `workspaceRoot` (optional): Workspace root directory (default: current directory)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\n  \"path\": \"README.md\",\n  \"size\": 1234,\n  \"mtime\": \"2024-01-01T12:00:00\",\n  \"hash\": \"sha256:abc123...\",\n  \"isBinary\": false,\n  \"content\": \"# README\\n...\"\n}"
    }]
  }
}
```

**Response Fields:**
- `path`: File path
- `size`: File size in bytes
- `mtime`: Last modification time (ISO format)
- `hash`: SHA256 hash of file content
- `isBinary`: Whether file is binary
- `content`: File content (text for text files, base64 for binary)

**Errors:**
- File not found
- Path traversal detected
- File too large (exceeds policy limit)
- Path not allowed by policy

### writeFile

Write file content to workspace.

**Method**: `tools/call`  
**Tool Name**: `writeFile`

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
      "contents": "Hello, World!\n",
      "options": {
        "atomic": true,
        "createIfMissing": true
      }
    }
  }
}
```

**Parameters:**
- `path` (required): File path relative to workspace root
- `contents` (required): File contents to write
- `workspaceRoot` (optional): Workspace root directory
- `options` (optional):
  - `atomic` (default: true): Use atomic write (temp file + rename)
  - `createIfMissing` (default: true): Create parent directories if missing

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\n  \"path\": \"test.txt\",\n  \"size\": 13\n}"
    }]
  }
}
```

**Errors:**
- Content too large (exceeds policy limit)
- Path traversal detected
- Path not allowed by policy
- Write failed

### listFiles

List directory contents.

**Method**: `tools/call`  
**Tool Name**: `listFiles`

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
        "globs": ["**/*.py"],
        "maxEntries": 1000
      }
    }
  }
}
```

**Parameters:**
- `path` (optional): Directory path (default: ".")
- `workspaceRoot` (optional): Workspace root directory
- `options` (optional):
  - `recursive` (default: false): List recursively
  - `globs` (optional): File glob patterns to include
  - `maxEntries` (default: 10000): Maximum entries to return

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\n  \"path\": \".\",\n  \"entries\": [\n    {\n      \"name\": \"file.py\",\n      \"path\": \"file.py\",\n      \"type\": \"file\",\n      \"size\": 1234,\n      \"mtime\": \"2024-01-01T12:00:00\"\n    }\n  ],\n  \"count\": 1\n}"
    }]
  }
}
```

**Errors:**
- Directory not found
- Path traversal detected
- Path not allowed by policy

## Search Operations

### searchFiles

Search for text in files.

**Method**: `tools/call`  
**Tool Name**: `searchFiles`

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
      "query": "def ",
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

**Parameters:**
- `query` (required): Search query
- `workspaceRoot` (optional): Workspace root directory
- `options` (optional):
  - `regex` (default: false): Use regex pattern
  - `caseSensitive` (default: false): Case-sensitive search
  - `globs` (optional): File glob patterns to search
  - `maxResults` (default: 1000): Maximum results to return

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\n  \"query\": \"def \",\n  \"results\": [\n    {\n      \"path\": \"main.py\",\n      \"line\": 10,\n      \"column\": 1,\n      \"text\": \"def hello():\"\n    }\n  ],\n  \"count\": 1\n}"
    }]
  }
}
```

**Errors:**
- Invalid regex pattern (if regex=true)
- Path traversal detected

## Task Operations

### runCommand

Run a command in the workspace.

**Method**: `tools/call`  
**Tool Name**: `runCommand`

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
        "cwd": ".",
        "timeout": 60,
        "confirmed": true
      }
    }
  }
}
```

**Parameters:**
- `command` (required): Command to run
- `args` (optional): Command arguments
- `workspaceRoot` (optional): Workspace root directory
- `options` (optional):
  - `cwd` (optional): Working directory (default: workspaceRoot)
  - `env` (optional): Environment variables
  - `timeout` (default: 300): Timeout in seconds
  - `confirmed` (required if policy requires it): Confirmation flag

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\n  \"command\": \"python3\",\n  \"args\": [\"-m\", \"pytest\"],\n  \"exitCode\": 0,\n  \"stdout\": \"test output...\",\n  \"stderr\": \"\"\n}"
    }]
  }
}
```

**Errors:**
- Command not allowed by policy
- Confirmation required
- Command timeout
- Command execution failed

## Policy Configuration

Create `.cws-policy.json` in workspace root to configure security:

```json
{
  "allowedPaths": ["**/*"],
  "deniedPaths": [".git/**", "node_modules/**"],
  "maxFileSize": 10485760,
  "maxEditSize": 1048576,
  "allowedCommands": ["python3", "npm", "make"],
  "envAllowlist": ["PATH", "HOME"],
  "confirmationRequired": ["runCommand"]
}
```

## Error Codes

- `-32602`: Invalid params (missing required fields, invalid format)
- `-32603`: Internal error
- `-32001`: Path traversal detected
- `-32002`: Policy violation
- `-32003`: File too large
- `-32004`: Operation denied (command not allowed)
- `-32005`: Confirmation required

## Examples

See [CODING_ENVIRONMENT_EXAMPLES.md](CODING_ENVIRONMENT_EXAMPLES.md) for complete examples.

