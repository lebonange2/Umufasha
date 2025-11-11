# Cursor-AI Clone - Usage Examples

## Example 1: Chat About Code

### Via CLI

```bash
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --files "src/parser.py" --question "Explain this function"
```

### Via MCP Server

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.chat","arguments":{"messages":[{"role":"user","content":"Explain the parse function"}],"context_files":["src/parser.py"]}}}' | \
python3 -m mcp.server --transport stdio
```

## Example 2: Plan a Feature

### Via CLI

```bash
python3 -m mcp.plugins.cursor_clone.ui.cli --plan "Add JSON logging" --scope "src/logging/"
```

### Via MCP Server

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.planAndPatch","arguments":{"goal":"Add JSON logging","scope":"src/logging/"}}}' | \
python3 -m mcp.server --transport stdio
```

## Example 3: Search Code

### Via MCP Server

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.searchCode","arguments":{"query":"def parse","max_results":5}}}' | \
python3 -m mcp.server --transport stdio
```

## Example 4: Index Repository

### Via CLI

```bash
python3 -m mcp.plugins.cursor_clone.ui.cli --index
```

### Via MCP Server

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.indexRefresh","arguments":{"full":true}}}' | \
python3 -m mcp.server --transport stdio
```

## Example 5: Complete Workflow

### Step 1: Index Repository

```bash
python3 -m mcp.plugins.cursor_clone.ui.cli --index
```

### Step 2: Plan Feature

```bash
python3 -m mcp.plugins.cursor_clone.ui.cli --plan "Add unit tests for parser" --scope "tests/"
```

### Step 3: Chat About Implementation

```bash
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --files "src/parser.py" --question "How should I structure the tests?"
```

### Step 4: Apply Changes

```bash
# Via MCP server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.applyPatch","arguments":{"diff":"...","message":"Add unit tests"}}}' | \
python3 -m mcp.server --transport stdio
```

### Step 5: Run Tests

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.runTests","arguments":{"suite":"tests/"}}}' | \
python3 -m mcp.server --transport stdio
```

## Example 6: Web Panel

### Start Web Panel

```bash
python3 -m mcp.plugins.cursor_clone.ui.webpanel.app
```

Then open http://localhost:7701 in your browser.

### Features

- Chat interface
- File tree
- Plan and patch workflow
- Search code

## Example 7: Integration with Existing MCP Tools

You can combine Cursor tools with existing coding environment tools:

```bash
# 1. Read a file
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"readFile","arguments":{"path":"src/parser.py"}}}' | \
python3 -m mcp.server --transport stdio

# 2. Chat about it
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"cursor.chat","arguments":{"messages":[{"role":"user","content":"Explain this code"}],"context_files":["src/parser.py"]}}}' | \
python3 -m mcp.server --transport stdio

# 3. Plan improvements
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"cursor.planAndPatch","arguments":{"goal":"Add error handling"}}}' | \
python3 -m mcp.server --transport stdio

# 4. Apply changes
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"writeFile","arguments":{"path":"src/parser.py","contents":"..."}}}' | \
python3 -m mcp.server --transport stdio

# 5. Run tests
echo '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"cursor.runTests","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

All tools work together seamlessly!

