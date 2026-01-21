# Running Exam Generator Locally with OpenAI API

## Overview

The exam generator now supports running locally using OpenAI API with GPT-4o, in addition to the existing RunPod cloud GPU setup with Ollama.

## Configuration

### Option 1: Environment Variables

Set the following environment variables:

```bash
# Use OpenAI provider
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-openai-api-key-here
export OPENAI_MODEL=gpt-4o

# Or use local (Ollama) provider
# export LLM_PROVIDER=local
# export LLM_MODEL=qwen3:30b
```

**Note:** `OPENAI_API_KEY` must be set as an environment variable (not in `.env` file) for security. You can also add it to your `.env` file, but the code reads it directly from the environment.

### Option 2: UI Selection

The exam generator UI now includes a **Provider** dropdown where you can select:
- **Local (Ollama)** - Uses local Ollama models (requires RunPod GPU setup)
- **OpenAI (GPT-4o)** - Uses OpenAI API (works locally, requires API key)

## Setup Steps

### 1. Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

### 2. Configure Environment

Set environment variables:

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-key-here
export OPENAI_MODEL=gpt-4o
```

**Note:** `OPENAI_API_KEY` is read directly from environment variables for security. You can also add it to `.env` file, but it's recommended to use environment variables.

### 3. Start the Application

```bash
# Start the backend server
./start_server.sh

# Or if using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Use the UI

1. Open the exam generator UI
2. Select **Provider: OpenAI (GPT-4o)** from the dropdown
3. The model will automatically switch to `gpt-4o`
4. Create your project and start generation

## Available Models

### OpenAI Models
- `gpt-4o` (default, recommended)
- `gpt-4o-mini` (faster, lower cost)
- `gpt-4-turbo` (alternative)

### Local Models (Ollama)
- `qwen3:30b` (default)
- `llama3:latest`

## Switching Between Providers

### Via UI
- Use the **Provider** dropdown in the exam generator form
- Select "Local (Ollama)" or "OpenAI (GPT-4o)"
- Model options will update automatically

### Via Environment
- Change `LLM_PROVIDER` in `.env` file
- Restart the server
- All new projects will use the selected provider

## Cost Considerations

### OpenAI API Costs (as of 2024)
- **gpt-4o**: ~$2.50 per 1M input tokens, ~$10 per 1M output tokens
- **gpt-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **gpt-4-turbo**: ~$10 per 1M input tokens, ~$30 per 1M output tokens

### Typical Exam Generation
- 150 problems with 15 learning objectives
- Estimated: ~500K-1M tokens total
- Cost with gpt-4o: ~$3-7 per exam
- Cost with gpt-4o-mini: ~$0.20-0.40 per exam

## Benefits of OpenAI vs Local

### OpenAI (Local Computer)
✅ **Pros:**
- No GPU required
- Works on any computer
- Fast API responses
- High-quality GPT-4o model
- No setup complexity

❌ **Cons:**
- Requires API key
- Costs per request
- Requires internet connection
- Rate limits apply

### Local (Ollama on RunPod)
✅ **Pros:**
- No API costs
- Full control
- Works offline (after setup)
- No rate limits

❌ **Cons:**
- Requires GPU (RunPod)
- Setup complexity
- Slower than OpenAI API
- Model quality may vary

## Troubleshooting

### "OPENAI_API_KEY is required" Error

**Solution:**
1. Set the environment variable: `export OPENAI_API_KEY=sk-your-key`
2. Restart the server after setting the key
3. Verify the key is set: `echo $OPENAI_API_KEY`
4. Verify the key is valid at https://platform.openai.com/api-keys
5. If using `.env` file, ensure it's loaded (some systems require explicit loading)

### API Rate Limits

**Solution:**
- OpenAI has rate limits based on your account tier
- If you hit limits, wait a few minutes or upgrade your account
- Consider using `gpt-4o-mini` for faster/cheaper generation

### Model Not Available

**Solution:**
- Ensure you have access to the selected model
- Check your OpenAI account billing status
- Try `gpt-4o-mini` as an alternative

## Example Environment Configuration

### Using Environment Variables (Recommended)

```bash
# Set environment variables
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-proj-abc123...
export OPENAI_MODEL=gpt-4o

# Database and other settings (can be in .env)
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://...
```

### Using .env File

```bash
# .env file (OPENAI_API_KEY will be read from environment, not from this file)
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o

# Database and other settings
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

**Important:** `OPENAI_API_KEY` must be set as an environment variable. If you want to use `.env` file, you need to export it:
```bash
source .env  # If your .env file has export statements
# Or manually: export OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d '=' -f2)
```

## Testing

Test the OpenAI integration:

```bash
# Set environment variable
export OPENAI_API_KEY=sk-your-key-here
export LLM_PROVIDER=openai

# Start server
./start_server.sh

# Create a test project via UI or API
curl -X POST http://localhost:8000/api/exam-generator/projects \
  -H "Content-Type: application/json" \
  -d '{
    "input_content": "Test content",
    "num_problems": 2,
    "provider": "openai",
    "model": "gpt-4o"
  }'
```

## Notes

- The provider selection in the UI only affects new projects
- Existing projects continue using their original provider
- You can switch providers between projects
- OpenAI API calls are made in parallel for faster generation (similar to multi-GPU setup)
