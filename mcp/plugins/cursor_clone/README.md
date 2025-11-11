# Cursor-AI Clone Plugin

A local-first AI coding assistant that provides inline code edits, refactors, navigation, doc generation, and test writing capabilities. Integrated into the MCP server as a plugin.

## Features

- **Multiple LLM Providers**: Choose between local (gemma3:4b) or ChatGPT (OpenAI)
- **Local LLM**: Uses gemma3:4b model locally (no cloud required)
- **ChatGPT Integration**: Use OpenAI API for enhanced capabilities
- **Code Planning**: Plan → Diff → Apply workflow
- **Repository Indexing**: Local code embeddings and RAG
- **Chat Interface**: Interactive chat about code
- **Patch Management**: Generate, apply, and rollback patches
- **Test Integration**: Run tests and verify changes
- **CLI & Web UI**: Terminal and web interfaces

## Quick Start

### 1. Install Dependencies

```bash
# Install PyYAML for config
pip install pyyaml

# Optional: Install llama-cpp-python for better LLM support
pip install llama-cpp-python
```

### 2. Download Model

Download gemma3:4b model (GGUF format) and place it in `models/`:

```bash
mkdir -p models
# Download gemma3-4b.gguf to models/
```

### 3. Configure

Create or edit `mcp/plugins/cursor_clone/config/default.yaml`:

```yaml
llm:
  provider: "local"  # or "openai" / "chatgpt"
  model_path: "models/gemma3-4b.gguf"
  use_gpu: false
  context_tokens: 8192
  max_tokens: 1024

workspace:
  root: "."
  disable_network: true
```

Or use environment variables:

```bash
# Choose provider: "local" or "openai" / "chatgpt"
export LLM_PROVIDER=local  # or "openai" / "chatgpt"

# For local models
export LOCAL_LLM_MODEL_PATH=models/gemma3-4b.gguf
export LOCAL_LLM_USE_GPU=false

# For OpenAI/ChatGPT (API key is automatically read from environment variable)
export OPENAI_API_KEY=your-api-key-here
export OPENAI_MODEL=gpt-4o-mini  # optional, defaults to gpt-4o-mini

export WORKSPACE_ROOT=.
```

### 4. Use via MCP Server

The tools are automatically registered in the MCP server:

```bash
# List all tools (including Cursor tools)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
python3 -m mcp.server --transport stdio
```

### 5. Use CLI

```bash
# Chat mode (local model)
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --provider local

# Chat mode (ChatGPT)
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --provider openai

# Plan and patch
python3 -m mcp.plugins.cursor_clone.ui.cli --plan "Add JSON logging" --scope "src/logging/"

# Index repository
python3 -m mcp.plugins.cursor_clone.ui.cli --index
```

### 6. Use Web Panel

```bash
python3 -m mcp.plugins.cursor_clone.ui.webpanel.app
# Open http://localhost:7701
```

## Available MCP Tools

### cursor.planAndPatch
Plan and generate patch for a coding goal.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "cursor.planAndPatch",
    "arguments": {
      "goal": "Add pytest-based unit tests for parser",
      "scope": "src/parser/",
      "constraints": {"no_external_libs": true}
    }
  }
}
```

### cursor.applyPatch
Apply a patch (diff).

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "cursor.applyPatch",
    "arguments": {
      "diff": "diff --git a/src/parser.py b/src/parser.py\n...",
      "message": "Add unit tests",
      "dry_run": false
    }
  }
}
```

### cursor.chat
Chat with the coding assistant.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "cursor.chat",
    "arguments": {
      "messages": [
        {"role": "user", "content": "Explain this function"}
      ],
      "context_files": ["src/parser.py"],
      "selection": "def parse(...)"
    }
  }
}
```

### cursor.searchCode
Search code in repository.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "cursor.searchCode",
    "arguments": {
      "query": "def parse",
      "max_results": 10
    }
  }
}
```

### cursor.indexRefresh
Refresh repository index.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "cursor.indexRefresh",
    "arguments": {
      "full": true
    }
  }
}
```

### cursor.runTests
Run tests.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "cursor.runTests",
    "arguments": {
      "suite": "tests/",
      "pattern": "test_parser"
    }
  }
}
```

### cursor.rollbackLast
Rollback last changes.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "cursor.rollbackLast",
    "arguments": {
      "file_path": "src/parser.py",
      "git_commit": "HEAD~1"
    }
  }
}
```

## Architecture

```
mcp/plugins/cursor_clone/
├── agent/
│   ├── planner.py      # Task planning
│   ├── editor.py       # Code editing & diffs
│   ├── chat.py         # Chat interface
│   ├── repo_indexer.py # Repository indexing
│   └── tools.py        # MCP tool registration
├── llm/
│   ├── engine.py       # LLM abstraction
│   └── backends/
│       └── gemma3_local.py  # Gemma3:4b backend
├── exec/
│   └── runner.py       # Command & test runner
├── ui/
│   ├── cli.py          # CLI/TUI interface
│   └── webpanel/
│       └── app.py       # Web panel
└── config/
    ├── default.yaml    # Default config
    └── schema.json     # Config schema
```

## Configuration

### Environment Variables

#### LLM Provider Selection
- `LLM_PROVIDER` - LLM provider: `"local"` or `"openai"` / `"chatgpt"` (default: `"local"`)

#### Local Model Settings
- `LOCAL_LLM_MODEL_PATH` - Path to model file (default: `models/gemma3-4b.gguf`)
- `LOCAL_LLM_USE_GPU` - Use GPU (default: `false`)
- `LOCAL_LLM_CONTEXT_TOKENS` - Context window size (default: `8192`)
- `LOCAL_LLM_MAX_TOKENS` - Max generation tokens (default: `1024`)

#### OpenAI/ChatGPT Settings
- `OPENAI_API_KEY` - OpenAI API key (required for ChatGPT provider)
- `OPENAI_MODEL` - OpenAI model name (default: `gpt-4o-mini`)
- `OPENAI_BASE_URL` - OpenAI API base URL (default: `https://api.openai.com/v1`)

#### General Settings
- `WORKSPACE_ROOT` - Workspace root directory (default: `.`)
- `ASSISTANT_ENABLE_WEBPANEL` - Enable web panel (default: `true`)
- `ASSISTANT_PORT` - Web panel port (default: `7701`)
- `ASSISTANT_DISABLE_NETWORK` - Disable network access (default: `true`)
- `ASSISTANT_LOG_LEVEL` - Log level (default: `INFO`)

### Config File

Edit `mcp/plugins/cursor_clone/config/default.yaml` for detailed configuration.

## Examples

### Example 1: Chat About Code

```bash
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --files "src/parser.py" --question "Explain this function"
```

### Example 2: Plan a Feature

```bash
python3 -m mcp.plugins.cursor_clone.ui.cli --plan "Add JSON logging" --scope "src/logging/"
```

### Example 3: Via MCP Server

```bash
# Chat
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.chat","arguments":{"messages":[{"role":"user","content":"Explain this code"}]}}}' | \
python3 -m mcp.server --transport stdio

# Plan
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.planAndPatch","arguments":{"goal":"Add unit tests"}}}' | \
python3 -m mcp.server --transport stdio
```

## Security

- All file operations scoped to workspace root
- Path traversal prevention
- Command allowlist enforcement
- Audit logging for all file changes
- Network access disabled by default

## Testing

```bash
# Run unit tests
python3 -m pytest mcp/plugins/cursor_clone/tests/unit/

# Run E2E tests
python3 -m pytest mcp/plugins/cursor_clone/tests/e2e/

# Run acceptance tests
python3 -m pytest mcp/plugins/cursor_clone/tests/acceptance/
```

## Troubleshooting

### Model Not Found

Ensure the model file exists at the path specified in config:
```bash
ls -lh models/gemma3-4b.gguf
```

### LLM Not Loading

Check logs for errors. Ensure model format is compatible (GGUF for llama.cpp).

### Tools Not Available

Ensure the plugin is properly installed and the MCP server can import it:
```bash
python3 -c "from mcp.plugins.cursor_clone.agent.tools import CURSOR_PLAN_AND_PATCH_TOOL; print('OK')"
```

## Next Steps

1. **Download Model**: Get gemma3:4b GGUF model
2. **Configure**: Set `LOCAL_LLM_MODEL_PATH` or edit config
3. **Index**: Run `--index` to index repository
4. **Use**: Start chatting or planning via CLI, web panel, or MCP tools

## Notes

- The LLM backend currently uses a mock implementation. In production, integrate with llama.cpp or similar.
- Repository indexing is basic (text-based). For production, add proper embeddings.
- Streaming chat is supported but not fully integrated with MCP yet.

