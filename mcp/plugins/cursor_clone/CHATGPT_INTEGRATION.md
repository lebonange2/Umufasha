# ChatGPT Integration - Complete ✅

## Overview

The Cursor-AI Clone plugin now supports **multiple LLM providers**, allowing you to choose between:
- **Local Model** (gemma3:4b) - No API key required, runs locally
- **ChatGPT** (OpenAI) - Enhanced capabilities via OpenAI API

## Quick Start

### 1. Set OpenAI API Key (Automatically Read from Environment)

The API key is **automatically read from the `OPENAI_API_KEY` environment variable**. Just set it:

```bash
export OPENAI_API_KEY=your-api-key-here
```

The system will automatically detect and use this environment variable - no configuration file needed!

### 2. Choose Provider

#### Option A: Environment Variable

```bash
export LLM_PROVIDER=openai  # or "local" or "chatgpt"
```

#### Option B: Config File

Edit `mcp/plugins/cursor_clone/config/default.yaml`:

```yaml
llm:
  provider: "openai"  # or "local" or "chatgpt"
  model: "gpt-4o-mini"
  base_url: "https://api.openai.com/v1"
```

### 3. Use It

#### Via CLI

```bash
# Use ChatGPT
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --provider openai

# Use local model
python3 -m mcp.plugins.cursor_clone.ui.cli --chat --provider local
```

#### Via Web Panel

1. Start web panel: `python3 -m mcp.plugins.cursor_clone.ui.webpanel.app`
2. Open http://localhost:7701
3. Use the provider dropdown to switch between providers

#### Via MCP Server

```bash
# Set provider
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-api-key-here

# Use Cursor tools (will use ChatGPT)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.chat","arguments":{"messages":[{"role":"user","content":"Hello"}]}}}' | \
python3 -m mcp.server --transport stdio
```

## Configuration

### Environment Variables

#### Provider Selection
- `LLM_PROVIDER` - Provider: `"local"`, `"openai"`, or `"chatgpt"` (default: `"local"`)

#### OpenAI/ChatGPT Settings
- `OPENAI_API_KEY` - **Required** for ChatGPT provider
- `OPENAI_MODEL` - Model name (default: `gpt-4o-mini`)
- `OPENAI_BASE_URL` - API base URL (default: `https://api.openai.com/v1`)

### Config File

Edit `mcp/plugins/cursor_clone/config/default.yaml`:

```yaml
llm:
  provider: "${LLM_PROVIDER:-local}"
  # For OpenAI/ChatGPT
  model: "${OPENAI_MODEL:-gpt-4o-mini}"
  base_url: "${OPENAI_BASE_URL:-https://api.openai.com/v1}"
  # Common settings
  max_tokens: "${LOCAL_LLM_MAX_TOKENS:-1024}"
  temperature: 0.7
  top_p: 0.9
```

## Features

### ✅ Provider Selection
- Choose between local and ChatGPT
- Automatic fallback to local if API key not set
- Runtime provider switching (web panel)

### ✅ API Key Management
- API key via environment variable (`OPENAI_API_KEY`)
- Secure handling (never logged)
- Validation on startup

### ✅ Model Configuration
- Configurable model (default: `gpt-4o-mini`)
- Custom base URL support
- Same interface for both providers

### ✅ Streaming Support
- Both providers support streaming
- Real-time token generation
- Web panel integration

## Architecture

```
LLM Engine Factory
├── Local Provider (gemma3:4b)
│   └── Gemma3LocalEngine
└── OpenAI Provider (ChatGPT)
    └── OpenAIClient
        ├── HTTP Client (httpx)
        ├── API Key (from env)
        └── Streaming Support
```

## Usage Examples

### Example 1: Chat with ChatGPT

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-api-key-here

python3 -m mcp.plugins.cursor_clone.ui.cli --chat --provider openai
```

### Example 2: Plan with ChatGPT

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-api-key-here

python3 -m mcp.plugins.cursor_clone.ui.cli --plan "Add unit tests" --provider openai
```

### Example 3: Web Panel Provider Switching

1. Start web panel
2. Use dropdown to select "ChatGPT (OpenAI)"
3. Chat will use ChatGPT
4. Switch back to "Local (gemma3:4b)" anytime

### Example 4: MCP Server with ChatGPT

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-api-key-here

# All Cursor tools will use ChatGPT
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cursor.planAndPatch","arguments":{"goal":"Add error handling"}}}' | \
python3 -m mcp.server --transport stdio
```

## Troubleshooting

### API Key Not Set

If `OPENAI_API_KEY` is not set, the system will:
1. Log a warning
2. Fall back to local model
3. Continue working with local provider

### Invalid API Key

If the API key is invalid:
1. Error will be logged
2. Request will fail with error message
3. Check API key in OpenAI dashboard

### Provider Not Switching

If provider doesn't switch:
1. Restart the application
2. Check environment variables
3. Verify config file settings

## Security

- ✅ API key never logged
- ✅ API key only in environment variables
- ✅ Secure HTTP client (httpx)
- ✅ No key storage in code

## Status

✅ **ChatGPT Integration Complete** - Full support for OpenAI/ChatGPT provider!

- ✅ Provider selection (local or ChatGPT)
- ✅ API key management via environment variables
- ✅ Web panel provider switching
- ✅ CLI provider selection
- ✅ MCP server integration
- ✅ Streaming support
- ✅ Error handling and fallback

