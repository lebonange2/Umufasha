# CWS Message Catalog

Complete API reference for Coding Workspace Service.

## File Operations

### fs.read
Read file content.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "fs.read",
  "params": {
    "path": "README.md"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "path": "README.md",
    "size": 1234,
    "mtime": "2024-01-01T12:00:00",
    "hash": "sha256:...",
    "isBinary": false,
    "content": "..."
  }
}
```

### fs.write
Write file content.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "fs.write",
  "params": {
    "path": "test.txt",
    "contents": "Hello, World!",
    "options": {
      "atomic": true,
      "createIfMissing": true
    }
  }
}
```

### fs.create
Create file or directory.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "fs.create",
  "params": {
    "path": "newdir",
    "type": "dir",
    "options": {
      "parents": true
    }
  }
}
```

### fs.delete
Delete file or directory.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "fs.delete",
  "params": {
    "path": "test.txt",
    "options": {
      "recursive": false,
      "confirmed": true
    }
  }
}
```

### fs.move
Move file or directory.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "fs.move",
  "params": {
    "src": "old.txt",
    "dst": "new.txt",
    "options": {
      "overwrite": false
    }
  }
}
```

### fs.list
List directory contents.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "fs.list",
  "params": {
    "path": ".",
    "options": {
      "recursive": false,
      "globs": ["**/*.py"],
      "maxEntries": 1000
    }
  }
}
```

## Search Operations

### search.find
Search for text in files.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "search.find",
  "params": {
    "query": "function",
    "options": {
      "regex": false,
      "caseSensitive": false,
      "globs": ["**/*.py"],
      "maxResults": 100
    }
  }
}
```

### code.symbols
Find code symbols.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "code.symbols",
  "params": {
    "scope": "workspace",
    "query": "test"
  }
}
```

## Edit Operations

### code.batchEdit
Apply batch edits atomically.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "method": "code.batchEdit",
  "params": {
    "edits": [
      {
        "path": "test.py",
        "range": {
          "startLine": 1,
          "startCol": 0,
          "endLine": 1,
          "endCol": 10
        },
        "newText": "def hello"
      }
    ],
    "options": {
      "atomic": true
    }
  }
}
```

## Task Operations

### task.run
Run a command.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "task.run",
  "params": {
    "command": "python3",
    "args": ["-m", "pytest"],
    "options": {
      "cwd": ".",
      "timeout": 60,
      "confirmed": true
    }
  }
}
```

### task.build
Run build task.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "method": "task.build",
  "params": {}
}
```

### task.test
Run test task.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 12,
  "method": "task.test",
  "params": {}
}
```

## Error Codes

- `-32700`: Parse error
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32001`: Path traversal detected
- `-32002`: Policy violation
- `-32003`: File too large
- `-32004`: Operation denied
- `-32005`: Confirmation required

