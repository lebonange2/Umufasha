# How to Run the Application

This guide explains how to run the unified AI Assistant application with all its features.

## 🚀 Quick Start (Unified Assistant)

### One-Command Start

```bash
# From project root
./start.sh
```

This starts the unified FastAPI server with:
- Personal Assistant (admin interface)
- Book Writing Assistant
- Brainstorming Assistant
- Coding Environment (if configured)

Access at: **http://localhost:8000**

### Homepage

The unified homepage at http://localhost:8000 provides links to:
- 📝 **Writer Assistant** - `/writer`
- 🧠 **Brainstorming** - `/brainstorm`
- ⚙️ **Admin Panel** - `/admin`
- 📚 **API Docs** - `/docs`

## 📝 Writer Assistant

### Setup

1. **Set API keys** (environment variables):
```bash
export OPENAI_API_KEY=your-openai-key
export ANTHROPIC_API_KEY=sk-ant-your-claude-key
```

2. **Build frontend** (first time):
```bash
cd writer
npm install
npm run build
cd ..
```

3. **Start server**:
```bash
./start.sh
```

4. **Access**: http://localhost:8000/writer

### Features
- Switch between OpenAI and Claude in UI
- Upload PDF/DOCX/TXT documents for context
- All AI features work with both providers

See [README_writer.md](README_writer.md) for details.

---

## Legacy: Cursor-AI Clone Application

The following sections are for the legacy Cursor-AI Clone application.

## Quick Start

### Option 1: Web Panel (Recommended for Beginners)

The easiest way to use the application is through the web panel:

```bash
# 1. Set your OpenAI API key (optional, for ChatGPT)
export OPENAI_API_KEY=your-api-key-here

# 2. Choose provider (optional, defaults to local)
export LLM_PROVIDER=openai  # or "local"

# 3. Start the web panel
python3 -m mcp.plugins.cursor_clone.ui.webpanel.app
```

Then open your browser to: **http://localhost:7701**

You'll see:
- Chat interface
- Provider selector (Local or ChatGPT)
- File tree
- Plan and patch features

### Option 2: CLI Interface

For terminal-based interaction:

```bash
# 1. Set your OpenAI API key (optional, for ChatGPT)
export OPENAI_API_KEY=your-api-key-here

# 2. Start chat mode
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --provider openai

# Or use local model
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --provider local
```

### Option 3: MCP Server (For Integration)

For programmatic access via MCP protocol:

```bash
# 1. Set your OpenAI API key (optional, for ChatGPT)
export OPENAI_API_KEY=your-api-key-here

# 2. Set provider (optional, defaults to local)
export LLM_PROVIDER=openai  # or "local"

# 3. Run MCP server
python3 -m mcp.server --transport stdio
```

Then send JSON-RPC requests to interact with the tools.

## Detailed Instructions

### Prerequisites

1. **Install Dependencies** (if not already installed):

```bash
cd /home/uwisiyose/ASSISTANT
pip install pyyaml httpx fastapi uvicorn structlog
```

2. **Set OpenAI API Key** (if using ChatGPT):

```bash
export OPENAI_API_KEY=your-api-key-here
```

### Method 1: Web Panel

**Step 1: Start the web panel**

```bash
python3 -m mcp.plugins.cursor_clone.ui.webpanel.app
```

**Step 2: Open browser**

Navigate to: **http://localhost:7701**

**Step 3: Use the interface**

- **Chat**: Type questions in the chat box
- **Provider**: Use dropdown to switch between Local and ChatGPT
- **Files**: Browse workspace files
- **Plan**: Use planning features

**Step 4: Stop the server**

Press `Ctrl+C` in the terminal

### Method 2: CLI Interface

**Step 1: Start chat mode**

```bash
# With ChatGPT
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --provider openai

# With local model
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --provider local
```

**Step 2: Interact**

- Type your questions
- Type `exit` to quit
- Type `clear` to clear history

**Other CLI commands:**

```bash
# Index repository
python3 -m mcp.plugins.cursor_clone.ui.cli --index

# Plan a feature
python3 -m mcp.plugins.cursor_clone.ui.cli --plan "Add unit tests" --scope "tests/"

# Chat with specific files
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --files "src/main.py" --question "Explain this code"
```

### Method 3: MCP Server

**Step 1: Start MCP server**

```bash
# Set provider (optional)
export LLM_PROVIDER=openai  # or "local"

# Start server
python3 -m mcp.server --transport stdio
```

**Step 2: Send requests**

Example: Chat with the assistant

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.chat","arguments":{"messages":[{"role":"user","content":"Hello"}]}}}' | \
python3 -m mcp.server --transport stdio
```

Example: Plan a feature

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.planAndPatch","arguments":{"goal":"Add unit tests"}}}' | \
python3 -m mcp.server --transport stdio
```

Example: Search code

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.searchCode","arguments":{"query":"def parse","max_results":5}}}' | \
python3 -m mcp.server --transport stdio
```

## Configuration

### Environment Variables

```bash
# Provider selection
export LLM_PROVIDER=openai  # or "local" or "chatgpt"

# OpenAI/ChatGPT settings
export OPENAI_API_KEY=your-api-key-here
export OPENAI_MODEL=gpt-4o-mini  # optional

# Local model settings
export LOCAL_LLM_MODEL_PATH=models/gemma3-4b.gguf
export LOCAL_LLM_USE_GPU=false

# Workspace settings
export WORKSPACE_ROOT=.

# Web panel settings
export ASSISTANT_PORT=7701
export ASSISTANT_ENABLE_WEBPANEL=true
```

### Config File

Edit `mcp/plugins/cursor_clone/config/default.yaml` for detailed configuration.

## Available Tools

When running via MCP server, you have access to **26 tools**:

### Cursor-AI Clone Tools (7)
- `cursor.planAndPatch` - Plan and generate patch
- `cursor.applyPatch` - Apply patch
- `cursor.rollbackLast` - Rollback changes
- `cursor.chat` - Chat with assistant
- `cursor.runTests` - Run tests
- `cursor.indexRefresh` - Refresh index
- `cursor.searchCode` - Search code

### Coding Environment Tools (5)
- `readFile` - Read file
- `writeFile` - Write file
- `listFiles` - List files
- `searchFiles` - Search files
- `runCommand` - Run command

### Other Tools (14)
- Application management
- User management
- Event management
- Notification management
- Calendar management
- Dashboard tools

## Examples

### Example 1: Chat via Web Panel

```bash
# Start web panel
python3 -m mcp.plugins.cursor_clone.ui.webpanel.app

# Open http://localhost:7701
# Select "ChatGPT (OpenAI)" from dropdown
# Type: "Explain this code" and select a file
```

### Example 2: Plan via CLI

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-api-key

python3 -m mcp.plugins.cursor_clone.ui.cli --plan "Add error handling" --scope "src/"
```

### Example 3: Use via MCP Server

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-api-key

# List all tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
python3 -m mcp.server --transport stdio

# Chat
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.chat","arguments":{"messages":[{"role":"user","content":"Hello"}]}}}' | \
python3 -m mcp.server --transport stdio
```

## Troubleshooting

### Port Already in Use

If port 7701 is already in use:

```bash
export ASSISTANT_PORT=7702
python3 -m mcp.plugins.cursor_clone.ui.webpanel.app
```

### API Key Not Working

Check that the API key is set:

```bash
echo $OPENAI_API_KEY
```

If empty, set it:

```bash
export OPENAI_API_KEY=your-api-key-here
```

### Provider Not Switching

Restart the application after changing `LLM_PROVIDER`:

```bash
export LLM_PROVIDER=openai
python3 -m mcp.plugins.cursor_clone.ui.webpanel.app
```

### Model Not Found (Local)

If using local model, ensure the model file exists:

```bash
ls -lh models/gemma3-4b.gguf
```

If not found, download it or use ChatGPT instead.

## Next Steps

1. **Try the web panel** - Easiest way to get started
2. **Index your repository** - Run `--index` to index your codebase
3. **Chat about code** - Ask questions about your code
4. **Plan features** - Use planning tools to plan code changes
5. **Apply changes** - Use patch tools to apply changes

## Summary

**Easiest way to run:**

```bash
# 1. Set API key (if using ChatGPT)
export OPENAI_API_KEY=your-api-key-here

# 2. Start web panel
python3 -m mcp.plugins.cursor_clone.ui.webpanel.app

# 3. Open http://localhost:7701
```

That's it! You're ready to use the Cursor-AI Clone application.

