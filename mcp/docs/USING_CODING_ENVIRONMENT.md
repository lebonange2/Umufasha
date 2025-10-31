# Using the Coding Environment - View and Edit Files

The coding environment tools are now integrated into the MCP server. Here are several ways to use them to view and edit files.

## Method 1: Direct MCP Commands (Quick)

### List Files

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"listFiles","arguments":{"path":"."}}}' | \
python3 -m mcp.server --transport stdio | python3 -c "import sys, json; data=json.load(sys.stdin); content=json.loads(data['result']['content'][0]['text']); [print(f\"{'📁' if e['type']=='dir' else '📄'} {e['name']}\") for e in content['entries'][:20]]"
```

### Read a File

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"readFile","arguments":{"path":"README.md"}}}' | \
python3 -m mcp.server --transport stdio | python3 -c "import sys, json; data=json.load(sys.stdin); content=json.loads(data['result']['content'][0]['text']); print(content['content'])"
```

### Write/Edit a File

```bash
# First, get the content you want to write
CONTENT="Your new file content here"

echo "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"writeFile\",\"arguments\":{\"path\":\"test.txt\",\"contents\":\"$CONTENT\"}}}" | \
python3 -m mcp.server --transport stdio
```

## Method 2: Interactive CLI Tool (Recommended)

Use the interactive file browser/editor:

```bash
cd /home/uwisiyose/ASSISTANT
python3 mcp/examples/coding_env_client.py --interactive
```

This provides an interactive interface:

```
============================================================
📁 Current Directory: .
============================================================

Commands:
  ls [path]          - List files
  cat <file>         - Read file
  edit <file>        - Edit file
  search <query>     - Search for text
  exit               - Exit

> ls

📂 Listing: .
  📄 README.md                          7,706 bytes
  📄 QUICKSTART.md                      12,667 bytes
  📁 mcp/                               dir
  📁 app/                               dir
  ...

> cat README.md

📄 Reading: README.md
------------------------------------------------------------
# Assistant Application
...
------------------------------------------------------------

> edit test.py

📝 Editing: test.py
File doesn't exist, creating new file.

Enter new content (end with 'EOF' on a new line):
def hello():
    print("Hello, World!")
EOF
✅ File written: test.py
```

## Method 3: Simple Command-Line Tool

Use the simple file editor script:

```bash
# List files
python3 mcp/examples/file_editor_simple.py ls

# Read a file
python3 mcp/examples/file_editor_simple.py cat README.md

# Edit a file
python3 mcp/examples/file_editor_simple.py edit test.py
# (Enter content, end with Ctrl+D)
```

## Method 4: Web-Based File Browser (VS Code-like Experience)

Start the web file browser:

```bash
python3 mcp/examples/web_file_browser.py
```

Then open your browser to:
```
http://localhost:8001
```

This provides a web interface where you can:
- Browse files and directories
- Click on files to view them
- Edit files in a textarea
- Save files

## Method 5: Use with Claude Desktop

If you have Claude Desktop configured with the MCP server, you can ask Claude:

```
"List all Python files in the mcp directory"
"Read the README.md file"
"Edit test.py to add a hello function"
"Search for all functions named 'main'"
```

Claude will use the MCP tools to:
- `listFiles` - List directory contents
- `readFile` - Read file content
- `writeFile` - Write file content
- `searchFiles` - Search for text

## Complete Workflow Example

### Using Interactive CLI

```bash
# Start interactive mode
python3 mcp/examples/coding_env_client.py --interactive

# In the interactive session:
> ls mcp
📂 mcp:
  📁 capabilities/                        dir
  📁 core/                               dir
  📄 README.md                           2,345 bytes
  ...

> ls mcp/capabilities/tools
📂 mcp/capabilities/tools:
  📄 app_management.py                   1,234 bytes
  📄 coding_environment.py               5,678 bytes
  ...

> cat mcp/capabilities/tools/coding_environment.py
[Shows file content]

> edit test.py
[Enter new content]
✅ File written: test.py

> search def 
[Shows search results]
```

## Tips

1. **Policy Configuration**: Create `.cws-policy.json` in workspace root to allow commands:
   ```json
   {
     "allowedCommands": ["python3", "npm", "make"],
     "allowedPaths": ["**/*"],
     "confirmationRequired": ["runCommand"]
   }
   ```

2. **Workspace Root**: By default, tools use current directory. Specify `workspaceRoot` parameter to use a different directory.

3. **Binary Files**: Binary files are base64 encoded in responses. You can still read them, but editing should be done via proper tools.

4. **Large Files**: Files over the policy `maxFileSize` limit cannot be read/written. Adjust policy if needed.

## Troubleshooting

### Permission Errors
- Check `.cws-policy.json` allows the paths you're accessing
- Ensure paths are within workspace root

### File Not Found
- Use relative paths from workspace root
- Check path spelling
- Use `listFiles` first to see available files

### Command Not Allowed
- Add command to `allowedCommands` in `.cws-policy.json`
- Set `confirmed: true` in options if policy requires confirmation

## Integration with Other Tools

You can combine coding environment tools with other MCP tools:

```bash
# 1. Start web app
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"startWebApplication","arguments":{}}}' | \
python3 -m mcp.server --transport stdio

# 2. Read config file
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"readFile","arguments":{"path":"config.json"}}}' | \
python3 -m mcp.server --transport stdio

# 3. Edit config file
# (Use interactive editor or writeFile tool)

# 4. Run tests
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"runCommand","arguments":{"command":"python3","args":["-m","pytest"],"options":{"confirmed":true}}}}' | \
python3 -m mcp.server --transport stdio
```

All tools work together seamlessly through the MCP server!

