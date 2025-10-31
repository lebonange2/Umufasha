# Coding Environment - Usage Examples

## File Operations

### Read a File

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"readFile","arguments":{"path":"README.md","workspaceRoot":"."}}}' | \
python3 -m mcp.server --transport stdio
```

### Write a File

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"writeFile","arguments":{"path":"test.txt","contents":"Hello, World!\n","workspaceRoot":"."}}}' | \
python3 -m mcp.server --transport stdio
```

### List Files in Directory

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"listFiles","arguments":{"path":".","workspaceRoot":"."}}}' | \
python3 -m mcp.server --transport stdio
```

### List Files Recursively

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"listFiles","arguments":{"path":".","workspaceRoot":".","options":{"recursive":true}}}}' | \
python3 -m mcp.server --transport stdio
```

## Search Operations

### Simple Text Search

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"searchFiles","arguments":{"query":"def ","workspaceRoot":"."}}}' | \
python3 -m mcp.server --transport stdio
```

### Regex Search

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"searchFiles","arguments":{"query":"^def ","workspaceRoot":".","options":{"regex":true}}}}' | \
python3 -m mcp.server --transport stdio
```

### Case-Sensitive Search

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"searchFiles","arguments":{"query":"Function","workspaceRoot":".","options":{"caseSensitive":true}}}}' | \
python3 -m mcp.server --transport stdio
```

### Search with Glob Patterns

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"searchFiles","arguments":{"query":"import","workspaceRoot":".","options":{"globs":["**/*.py"]}}}}' | \
python3 -m mcp.server --transport stdio
```

## Task Operations

### Run a Simple Command

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"runCommand","arguments":{"command":"python3","args":["--version"],"workspaceRoot":".","options":{"confirmed":true}}}}' | \
python3 -m mcp.server --transport stdio
```

### Run Tests

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"runCommand","arguments":{"command":"python3","args":["-m","pytest"],"workspaceRoot":".","options":{"confirmed":true,"timeout":60}}}}' | \
python3 -m mcp.server --transport stdio
```

### Run Build Command

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"runCommand","arguments":{"command":"make","args":["build"],"workspaceRoot":".","options":{"confirmed":true}}}' | \
python3 -m mcp.server --transport stdio
```

## Complete Workflow Example

### 1. Read a File

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"readFile","arguments":{"path":"main.py","workspaceRoot":"."}}}' | \
python3 -m mcp.server --transport stdio
```

### 2. Search for a Function

```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"searchFiles","arguments":{"query":"def main","workspaceRoot":"."}}}' | \
python3 -m mcp.server --transport stdio
```

### 3. Write a Modified Version

```bash
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"writeFile","arguments":{"path":"main.py","contents":"def main():\n    print(\"Hello\")\n","workspaceRoot":"."}}}' | \
python3 -m mcp.server --transport stdio
```

### 4. Run Tests

```bash
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"runCommand","arguments":{"command":"python3","args":["-m","pytest"],"workspaceRoot":".","options":{"confirmed":true}}}}' | \
python3 -m mcp.server --transport stdio
```

## Policy Configuration

To allow commands, create `.cws-policy.json`:

```json
{
  "allowedPaths": ["**/*"],
  "deniedPaths": [".git/**", "node_modules/**"],
  "allowedCommands": ["python3", "npm", "make"],
  "confirmationRequired": ["runCommand"]
}
```

## Integration with Other Tools

You can combine coding environment tools with other MCP tools:

### 1. Start Web Application
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

### 2. Read Configuration File
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"readFile","arguments":{"path":"config.json"}}}' | \
python3 -m mcp.server --transport stdio
```

### 3. Run Tests
```bash
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"runCommand","arguments":{"command":"python3","args":["-m","pytest"],"options":{"confirmed":true}}}}' | \
python3 -m mcp.server --transport stdio
```

### 4. Get Dashboard Stats
```bash
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"getDashboardStats","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

All tools are available through the same MCP server!

