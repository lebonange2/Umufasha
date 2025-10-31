#!/bin/bash
# Example: Add a user via MCP server

# Method 1: Using pipe (one-shot)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"John Doe","email":"john@example.com","phone_e164":"+1234567890","channel_pref":"email"}}}' | \
python3 -m mcp.server --transport stdio

echo ""
echo "---"

# Method 2: Minimal required fields only
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"Jane Smith","email":"jane@example.com"}}}' | \
python3 -m mcp.server --transport stdio

