# Coding Workspace Service (CWS)

A standalone daemon providing file operations, code editing, search, and task execution capabilities for AI coding environments.

## Features

- **File Operations**: Read, write, create, delete, move, list files
- **Code Editing**: Batch edits, formatting, diff/patch operations
- **Search**: Full-text search, regex search, symbol search
- **Tasks**: Run commands, execute tests, terminal operations
- **Security**: Policy enforcement, workspace sandboxing, confirmation requirements

## Transport

- **Stdio**: JSON-RPC over standard input/output
- **WebSocket**: JSON-RPC over WebSocket (optional)

## Protocol

JSON-RPC 2.0 with strict schema validation.

## Security

- Workspace root sandboxing
- Path traversal prevention
- Policy-based access control
- Confirmation for destructive operations

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Stdio mode
python3 -m cws.main --stdio

# WebSocket mode
python3 -m cws.main --websocket --host localhost --port 9090
```

## Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
pytest tests/perf/
```

## Documentation

See `docs/` directory for complete documentation.

