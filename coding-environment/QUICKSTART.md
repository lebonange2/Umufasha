# AI Coding Environment - Quick Start

Complete guide to get the AI Coding Environment up and running.

## Prerequisites

- Python 3.10+
- Node.js 18+ (for VS Code extension)
- VS Code 1.74+

## Installation

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

### 3. Configure Workspace

Create `.cws-policy.json` in your workspace root:

```bash
cp adjacent-ai-env/.cws-policy.json.example .cws-policy.json
```

Edit as needed for your project.

## Running

### Start CWS (Stdio Mode)

```bash
cd adjacent-ai-env/coding-workspace-service
source venv/bin/activate
python3 -m cws.main --transport stdio
```

### Start CWS (WebSocket Mode)

```bash
python3 -m cws.main --transport websocket --host localhost --port 9090
```

### Use VS Code Extension

1. Open VS Code
2. Extension activates automatically
3. Use commands:
   - `CWS: Open File`
   - `CWS: Write File`
   - `CWS: Search`
   - `CWS: Run Task`
   - `CWS: Run Tests`

## Example: Complete Workflow

### 1. Read a File

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"fs.read","params":{"path":"README.md"}}' | \
python3 -m cws.main --transport stdio
```

### 2. Write a File

```bash
echo '{"jsonrpc":"2.0","id":2,"method":"fs.write","params":{"path":"test.txt","contents":"Hello, World!"}}' | \
python3 -m cws.main --transport stdio
```

### 3. Search for Text

```bash
echo '{"jsonrpc":"2.0","id":3,"method":"search.find","params":{"query":"function","options":{}}}' | \
python3 -m cws.main --transport stdio
```

### 4. Run a Task

```bash
echo '{"jsonrpc":"2.0","id":4,"method":"task.run","params":{"command":"python3","args":["-m","pytest"],"options":{"confirmed":true}}}' | \
python3 -m cws.main --transport stdio
```

## Configuration

### VS Code Settings

Add to `.vscode/settings.json`:

```json
{
  "assistantAiCodingEnv.mcp.command": "python3",
  "assistantAiCodingEnv.mcp.args": ["-m", "mcp.server", "--transport", "stdio"],
  "assistantAiCodingEnv.cws.command": "python3",
  "assistantAiCodingEnv.cws.args": ["-m", "cws.main", "--transport", "stdio"]
}
```

### Policy Configuration

See [coding-workspace-service/docs/POLICY.md](coding-workspace-service/docs/POLICY.md) for policy options.

## Testing

```bash
cd adjacent-ai-env/coding-workspace-service
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## Troubleshooting

See [coding-workspace-service/docs/TROUBLESHOOTING.md](coding-workspace-service/docs/TROUBLESHOOTING.md)

## Next Steps

- Read [CWS Message Catalog](coding-workspace-service/docs/MESSAGE_CATALOG.md) for complete API
- Configure security policies
- Integrate with AI workflows

