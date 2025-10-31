# How to View and Edit Files Using Coding Environment

The coding environment tools are **integrated into the MCP server**. Here's how to use them to view and edit files like VS Code!

## 🚀 Quick Start - Interactive File Browser

The easiest way is to use the interactive CLI tool:

```bash
cd /home/uwisiyose/ASSISTANT
python3 mcp/examples/coding_env_client.py --interactive
```

This gives you a VS Code-like experience in the terminal:

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

> ls mcp

📂 Listing: mcp
  📁 capabilities/                        dir
  📁 core/                               dir
  📄 README.md                           2,345 bytes
  ...

> cat mcp/README.md

📄 Reading: mcp/README.md
------------------------------------------------------------
# MCP Server for Assistant Application
...
------------------------------------------------------------

> edit test.py

📝 Editing: test.py
Enter new content (end with 'EOF' on a new line):
def hello():
    print("Hello, World!")
EOF
✅ File written: test.py
```

## 🌐 Web-Based File Browser (Best Experience)

For a visual, VS Code-like experience in your browser:

```bash
python3 mcp/examples/web_file_browser.py
```

Then open: **http://localhost:8001**

Features:
- 📁 Browse files and directories
- 📄 Click files to view them
- ✏️ Edit files in a textarea
- 💾 Save files

Just like VS Code, but in your browser!

## 📝 Simple Command-Line Tool

For quick operations:

```bash
# List files
python3 mcp/examples/file_editor_simple.py ls

# Read a file
python3 mcp/examples/file_editor_simple.py cat README.md

# Edit a file
python3 mcp/examples/file_editor_simple.py edit test.py
```

## 🎯 Direct MCP Commands

You can also use the tools directly:

### List Files
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"listFiles","arguments":{"path":"."}}}' | \
python3 -m mcp.server --transport stdio
```

### Read a File
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"readFile","arguments":{"path":"README.md"}}}' | \
python3 -m mcp.server --transport stdio
```

### Write/Edit a File
```bash
# Create/edit a file
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"writeFile","arguments":{"path":"test.txt","contents":"Hello, World!"}}}' | \
python3 -m mcp.server --transport stdio
```

## 🤖 Using with Claude Desktop

If you have Claude Desktop configured, you can ask Claude directly:

- "List all Python files in the project"
- "Read the README.md file"
- "Edit test.py to add a function"
- "Search for all functions named 'main'"

Claude will use the MCP coding environment tools automatically!

## 📋 Complete Example Workflow

### 1. Start Interactive Mode
```bash
python3 mcp/examples/coding_env_client.py --interactive
```

### 2. Browse Files
```
> ls
[Shows all files]

> ls mcp/capabilities
[Shows files in that directory]
```

### 3. View a File
```
> cat mcp/server.py
[Shows file content]
```

### 4. Edit a File
```
> edit test.py
[Enter new content, end with 'EOF']
✅ File written: test.py
```

### 5. Search Files
```
> search def 
[Shows all functions]
```

## 🎨 Web Browser Interface

For the best visual experience, use the web interface:

```bash
# Terminal 1: Start web file browser
python3 mcp/examples/web_file_browser.py

# Browser: Open http://localhost:8001
```

Features:
- ✅ Visual file tree
- ✅ Click to open files
- ✅ Edit files with syntax highlighting
- ✅ Save files
- ✅ Navigate directories

## ⚙️ Configuration

Create `.cws-policy.json` in workspace root to configure security:

```json
{
  "allowedPaths": ["**/*"],
  "deniedPaths": [".git/**", "node_modules/**"],
  "maxFileSize": 10485760,
  "allowedCommands": ["python3", "npm", "make"]
}
```

## 📚 More Information

- **Tool Documentation**: `mcp/docs/CODING_ENVIRONMENT.md`
- **Examples**: `mcp/docs/CODING_ENVIRONMENT_EXAMPLES.md`
- **Complete Guide**: `mcp/docs/USING_CODING_ENVIRONMENT.md`

## 🎯 Recommended Approach

**For Best Experience**: Use the **web file browser**:
```bash
python3 mcp/examples/web_file_browser.py
# Open http://localhost:8001
```

**For Quick Terminal Use**: Use the **interactive CLI**:
```bash
python3 mcp/examples/coding_env_client.py --interactive
```

Both provide a VS Code-like experience for viewing and editing files through the MCP server!

