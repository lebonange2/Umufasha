# Claude API Setup Guide

## Overview

The Writer Assistant now supports **Claude API (Anthropic)** in addition to OpenAI. You can switch between providers using environment variables.

## Quick Setup

### 1. Get Your Claude API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-...`)

### 2. Add to Environment Variables

Edit your `.env` file in the project root:

```bash
# Option 1: Use Claude API
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022

# Option 2: Use OpenAI (default)
OPENAI_API_KEY=sk-your-openai-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o

# Option 3: Custom endpoint (OpenAI-compatible)
LLM_PROVIDER=openai
LLM_BASE_URL=https://your-custom-endpoint.com/v1
LLM_MODEL=your-model-name
```

### 3. Restart the Server

After updating `.env`, restart the FastAPI server:

```bash
./start.sh
```

## Available Claude Models

- `claude-3-5-sonnet-20241022` - Latest and most capable (recommended)
- `claude-3-5-sonnet-20240620` - Previous version
- `claude-3-opus-20240229` - Most powerful (slower)
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-haiku-20240307` - Fastest and cheapest

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Claude API key | None |
| `OPENAI_API_KEY` | Your OpenAI API key | None |
| `LLM_PROVIDER` | Provider: `openai`, `anthropic`, or `custom` | `openai` |
| `LLM_BASE_URL` | Custom API endpoint (optional) | Provider default |
| `LLM_MODEL` | Model name | `gpt-4o` or `claude-3-5-sonnet-20241022` |

### Example Configurations

#### Use Claude (Anthropic)
```bash
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
```

#### Use OpenAI
```bash
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
```

#### Use Custom OpenAI-Compatible Endpoint
```bash
OPENAI_API_KEY=your-key
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=your-model
```

## How It Works

The `LLMClient` automatically detects the provider and uses the appropriate API format:

- **OpenAI**: Uses `/chat/completions` endpoint with `Authorization: Bearer` header
- **Claude**: Uses `/messages` endpoint with `x-api-key` header and different message format
- **Custom**: Uses OpenAI-compatible format with your custom base URL

## Testing

### Test Claude API Connection

```bash
# Check if Claude is configured
python3 -c "
from app.core.config import settings
from app.llm.client import LLMClient

client = LLMClient(
    api_key=settings.ANTHROPIC_API_KEY,
    provider='anthropic',
    model='claude-3-5-sonnet-20241022'
)
print('Claude client created successfully')
"
```

### Test in Writer

1. Set `LLM_PROVIDER=anthropic` in `.env`
2. Set `ANTHROPIC_API_KEY=your-key`
3. Restart server
4. Open http://localhost:8000/writer
5. Try "Continue Writing" - should use Claude

## API Differences

### OpenAI Format
```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ]
}
```

### Claude Format
```json
{
  "model": "claude-3-5-sonnet-20241022",
  "system": "...",
  "messages": [
    {"role": "user", "content": "..."}
  ]
}
```

The `LLMClient` handles these differences automatically based on the `provider` setting.

## Troubleshooting

### "Invalid API key"
- Verify your `ANTHROPIC_API_KEY` is correct
- Check it starts with `sk-ant-`
- Ensure no extra spaces or quotes

### "Provider not supported"
- Ensure `LLM_PROVIDER` is set to `anthropic` (lowercase)
- Check `.env` file is loaded correctly

### "Model not found"
- Verify the model name is correct
- Check Anthropic's [model list](https://docs.anthropic.com/claude/docs/models-overview)

### Still Using OpenAI
- Check `LLM_PROVIDER` is set correctly
- Restart the server after changing `.env`
- Check server logs for initialization messages

## Cost Comparison

| Provider | Model | Cost per 1M tokens (input) | Cost per 1M tokens (output) |
|----------|-------|----------------------------|-----------------------------|
| OpenAI | gpt-4o | $2.50 | $10.00 |
| Claude | claude-3-5-sonnet | $3.00 | $15.00 |
| Claude | claude-3-haiku | $0.25 | $1.25 |

Choose based on your needs:
- **Claude**: Better for long context, nuanced writing
- **OpenAI**: Faster, more cost-effective for simple tasks

## Switching Providers

You can switch providers without code changes:

1. Update `.env` file
2. Restart server
3. All AI features will use the new provider

The Writer Assistant will automatically use the configured provider for:
- Autocomplete
- Continue Writing
- Expand
- Summarize
- Outline
- Rewrite
- Q&A

## Security Notes

- Never commit `.env` file to git
- API keys are stored server-side only
- Keys are never exposed to the frontend
- Use environment variables, not hardcoded keys

