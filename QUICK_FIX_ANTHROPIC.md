# Quick Fix: ANTHROPIC_API_KEY Not Set

## The Error

You're seeing `400 Bad Request` because the `ANTHROPIC_API_KEY` environment variable is not set.

## Quick Solution

### Option 1: Set in Current Terminal (Temporary)

```bash
# Set the API key
export ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here

# Verify it's set
echo $ANTHROPIC_API_KEY

# Restart the server
./start.sh
```

### Option 2: Set in Shell Profile (Permanent)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

Then restart the server:
```bash
./start.sh
```

## Verify It's Working

### Check Environment Variable

```bash
echo $ANTHROPIC_API_KEY
```

Should show: `sk-ant-...` (your actual key)

### Test in Python

```bash
python3 -c "import os; key = os.getenv('ANTHROPIC_API_KEY'); print('Set' if key else 'Not set')"
```

Should show: `Set`

### Test the API

```bash
curl -X POST http://localhost:8000/api/llm \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "test",
    "mode": "autocomplete",
    "provider": "anthropic",
    "model": "claude-3-haiku-20240307",
    "stream": false
  }'
```

Should NOT return: `"ANTHROPIC_API_KEY environment variable is not set"`

## Important Notes

1. **The environment variable must be set BEFORE starting the server**
2. **If you set it after starting, you must restart the server**
3. **The variable must be exported** (`export ANTHROPIC_API_KEY=...`)
4. **No quotes needed** around the key value

## Getting Your API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-...`)
6. Use it in the export command above

## Troubleshooting

### "Still getting 400 error after setting"

1. **Check the variable is set:**
   ```bash
   echo $ANTHROPIC_API_KEY
   ```

2. **Make sure you exported it:**
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-your-key
   # NOT just: ANTHROPIC_API_KEY=sk-ant-your-key
   ```

3. **Restart the server:**
   ```bash
   # Stop the server (Ctrl+C)
   # Then restart
   ./start.sh
   ```

4. **Check in the same terminal:**
   - The variable must be set in the terminal where you run `./start.sh`
   - Or set it in your shell profile for persistence

### "Variable is set but still not working"

1. **Check for typos:**
   ```bash
   echo $ANTHROPIC_API_KEY
   # Should show your key, not empty
   ```

2. **Check the key format:**
   - Should start with `sk-ant-`
   - Should be a long string

3. **Verify the server can see it:**
   ```bash
   # In the server terminal, check:
   python3 -c "import os; print(os.getenv('ANTHROPIC_API_KEY'))"
   ```

## Example Workflow

```bash
# 1. Set the API key
export ANTHROPIC_API_KEY=sk-ant-api03-abc123xyz...

# 2. Verify
echo $ANTHROPIC_API_KEY

# 3. Start server
./start.sh

# 4. Open browser
# http://localhost:8000/writer

# 5. Select "Anthropic (Claude)" in settings
# 6. Try autocomplete or continue writing
```

## Making It Permanent

To avoid setting it every time, add to your shell profile:

**For Bash (`~/.bashrc`):**
```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-your-key' >> ~/.bashrc
source ~/.bashrc
```

**For Zsh (`~/.zshrc`):**
```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-your-key' >> ~/.zshrc
source ~/.zshrc
```

Then restart your terminal or run `source ~/.bashrc` / `source ~/.zshrc`.

