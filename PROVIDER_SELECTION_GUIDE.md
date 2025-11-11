# Provider Selection Guide

## Overview

The Writer Assistant now supports **runtime provider selection** in the web UI. You can switch between OpenAI (ChatGPT) and Anthropic (Claude) without restarting the server or editing configuration files.

## Setting Up API Keys

### Environment Variables (Recommended)

API keys should be set as **environment variables**, not in the `.env` file:

```bash
# For Claude API
export ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# For OpenAI API
export OPENAI_API_KEY=sk-your-openai-key-here
```

### Making Environment Variables Persistent

**Linux/Mac:**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key
export OPENAI_API_KEY=sk-your-key
```

**Windows:**
```powershell
# PowerShell
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'sk-ant-your-key', 'User')

# Or use System Properties > Environment Variables
```

### Verify Environment Variables

```bash
# Check if set
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Test in Python
python3 -c "import os; print('ANTHROPIC_API_KEY:', 'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not set')"
```

## Using Provider Selection in UI

### Access Settings

1. Open the Writer Assistant: `http://localhost:8000/writer`
2. Look at the **AI Toolbox** on the right sidebar
3. Expand the toolbox if collapsed
4. Scroll to the **Settings** section

### Select Provider

1. Find **"AI Provider"** dropdown
2. Choose:
   - **OpenAI (ChatGPT)** - Uses your `OPENAI_API_KEY`
   - **Anthropic (Claude)** - Uses your `ANTHROPIC_API_KEY`

### Select Model

After choosing a provider, the **Model** dropdown will show available models:

**For Claude:**
- Claude 3.5 Sonnet (Latest) - Recommended
- Claude 3.5 Sonnet
- Claude 3 Opus - Most powerful
- Claude 3 Sonnet - Balanced
- Claude 3 Haiku - Fastest/cheapest

**For OpenAI:**
- GPT-4o - Latest
- GPT-4 Turbo
- GPT-4
- GPT-3.5 Turbo

### Settings Persistence

Your provider and model selection is automatically saved to browser localStorage and will persist across sessions.

## How It Works

1. **Frontend**: User selects provider/model in UI
2. **Request**: Frontend sends `provider` and `model` in LLM request
3. **Backend**: Server reads API key from environment variable based on provider
4. **LLM Client**: Creates appropriate client (OpenAI or Claude format)
5. **Response**: Streaming response sent back to frontend

## API Key Priority

The system checks environment variables in this order:

1. **For Anthropic**: `ANTHROPIC_API_KEY` environment variable
2. **For OpenAI**: `OPENAI_API_KEY` environment variable
3. **Fallback**: If not in environment, checks `.env` file (not recommended)

## Troubleshooting

### "API key not configured" Error

**Check environment variable:**
```bash
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
```

**If not set:**
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key
# Restart server after setting
```

### Provider Not Working

1. Verify API key is set correctly
2. Check server logs for errors
3. Ensure key starts with correct prefix:
   - Claude: `sk-ant-...`
   - OpenAI: `sk-...`

### Settings Not Saving

- Check browser console for errors
- Verify localStorage is enabled
- Try clearing browser cache

### Model Not Available

- Verify you have access to the model
- Check API key permissions
- Some models may require specific API tiers

## Example Workflow

1. **Set environment variables:**
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-api03-...
   export OPENAI_API_KEY=sk-...
   ```

2. **Start server:**
   ```bash
   ./start.sh
   ```

3. **Open writer:**
   ```
   http://localhost:8000/writer
   ```

4. **Select provider in UI:**
   - Open AI Toolbox
   - Choose "Anthropic (Claude)" from dropdown
   - Select "Claude 3.5 Sonnet (Latest)"
   - Settings auto-save

5. **Use AI features:**
   - All AI actions (autocomplete, continue, etc.) now use Claude
   - Switch back to OpenAI anytime from the dropdown

## Benefits

✅ **No server restart** - Switch providers instantly  
✅ **No config editing** - All done in UI  
✅ **Settings persist** - Saved in browser  
✅ **Secure** - API keys never exposed to frontend  
✅ **Flexible** - Use best model for each task  

## Security Notes

- API keys are **never** sent to the frontend
- Keys are read server-side from environment variables
- Provider selection is client-side only (no key exposure)
- All API calls go through backend proxy

