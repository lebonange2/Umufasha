# API Key Setup Guide

## Quick Fix for "401 Unauthorized" Error

If you're seeing a `401 Unauthorized` error, it means the API key is not set or is invalid.

### For Claude (Anthropic)

```bash
# Set the environment variable
export ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# Verify it's set
echo $ANTHROPIC_API_KEY

# Restart the server
./start.sh
```

### For OpenAI

```bash
# Set the environment variable
export OPENAI_API_KEY=sk-your-openai-key-here

# Verify it's set
echo $OPENAI_API_KEY

# Restart the server
./start.sh
```

## Making Environment Variables Persistent

### Linux/Mac (Bash)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export OPENAI_API_KEY=sk-your-key-here
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Linux/Mac (Zsh)

Add to `~/.zshrc`:

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export OPENAI_API_KEY=sk-your-key-here
```

Then reload:
```bash
source ~/.zshrc
```

### Windows (PowerShell)

```powershell
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'sk-ant-your-key', 'User')
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-your-key', 'User')
```

Or use System Properties:
1. Right-click "This PC" > Properties
2. Advanced system settings
3. Environment Variables
4. Add new User variable

## Verify Setup

### Check Environment Variable

```bash
# Check if set
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Test in Python
python3 -c "import os; print('ANTHROPIC_API_KEY:', 'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not set')"
```

### Check Application Settings

```bash
python3 -c "from app.core.config import settings; print('ANTHROPIC_API_KEY:', 'Set' if settings.ANTHROPIC_API_KEY else 'Not set')"
```

## Common Issues

### Issue: "ANTHROPIC_API_KEY environment variable is not set"

**Solution:**
1. Set the environment variable (see above)
2. Make sure you're setting it in the same terminal session where you run `./start.sh`
3. Or add it to your shell profile for persistence

### Issue: "401 Unauthorized" even with key set

**Possible causes:**
1. **Invalid API key** - Check that the key is correct
2. **Key not exported** - Make sure you used `export`, not just `ANTHROPIC_API_KEY=...`
3. **Server not restarted** - Restart the server after setting the variable
4. **Wrong terminal session** - Set the variable in the same terminal where you run the server

### Issue: Key works in terminal but not in application

**Solution:**
1. Check if the key is set in the environment where the server runs
2. If using systemd or a process manager, set environment variables in the service file
3. If using Docker, pass environment variables with `-e` flag

## Testing

### Test Claude API Key

```bash
# Set the key
export ANTHROPIC_API_KEY=sk-ant-your-key

# Test with curl
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-haiku-20240307",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "Hi"}]
  }'
```

### Test OpenAI API Key

```bash
# Set the key
export OPENAI_API_KEY=sk-your-key

# Test with curl
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 10
  }'
```

## Security Best Practices

1. **Never commit API keys** to git
2. **Use environment variables**, not `.env` files in production
3. **Rotate keys regularly**
4. **Use different keys** for development and production
5. **Limit key permissions** when possible

## Getting API Keys

### Claude (Anthropic)

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key
5. Copy the key (starts with `sk-ant-...`)

### OpenAI

1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new secret key
4. Copy the key (starts with `sk-...`)

## Troubleshooting Checklist

- [ ] Environment variable is set (`echo $ANTHROPIC_API_KEY`)
- [ ] Variable is exported (`export ANTHROPIC_API_KEY=...`)
- [ ] Server was restarted after setting variable
- [ ] Key is valid (test with curl)
- [ ] Key has correct format (Claude: `sk-ant-...`, OpenAI: `sk-...`)
- [ ] No extra spaces or quotes around the key
- [ ] Using the same terminal session for setting and running

