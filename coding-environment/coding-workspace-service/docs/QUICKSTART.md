# CWS Quick Start Guide

## Installation

```bash
cd adjacent-ai-env/coding-workspace-service
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Running

### Stdio Mode

```bash
python3 -m cws.main --transport stdio
```

### WebSocket Mode

```bash
python3 -m cws.main --transport websocket --host localhost --port 9090
```

## Example Usage

### Read a File

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

### Write a File

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

### Search for Text

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "search.find",
  "params": {
    "query": "function",
    "options": {
      "regex": false,
      "caseSensitive": false,
      "globs": ["**/*.py"]
    }
  }
}
```

### Run a Command

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "task.run",
  "params": {
    "command": "python3",
    "args": ["-m", "pytest"],
    "options": {
      "timeout": 60,
      "confirmed": true
    }
  }
}
```

## Policy Configuration

Create `.cws-policy.json` in your workspace root:

```json
{
  "allowedPaths": ["**/*"],
  "deniedPaths": [".git/**", "node_modules/**"],
  "maxFileSize": 10485760,
  "maxEditSize": 1048576,
  "allowedCommands": ["npm", "python3", "make", "pytest"],
  "envAllowlist": ["PATH", "HOME"],
  "confirmationRequired": ["delete", "applyPatch", "task.run"]
}
```

