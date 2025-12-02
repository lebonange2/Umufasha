# Book Writer Setup Guide

## Quick Setup for Runpod/Cloud Environments

If you're running in a cloud environment (like Runpod) and encounter missing dependencies:

### Install Required Dependencies

```bash
# Install core dependencies
pip install structlog httpx

# Or install all app requirements
pip install -r requirements-app.txt

# Or install just book writer requirements
pip install -r app/book_writer/requirements.txt
```

### Verify Installation

```bash
python3 -c "from app.book_writer.ferrari_company import FerrariBookCompany; print('✓ Setup successful')"
```

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'structlog'`

**Solution:**
```bash
pip install structlog
```

### Issue: `ModuleNotFoundError: No module named 'httpx'`

**Solution:**
```bash
pip install httpx
```

### Issue: Import errors from app modules

**Solution:**
Make sure you're running from the project root directory:
```bash
cd /path/to/ASSISTANT
python3 -m app.book_writer.ferrari_company
```

### Issue: LLM connection errors

**Solution:**
- For local Ollama: Make sure Ollama is running
- For cloud: Update `LLM_LOCAL_URL` in config to point to your LLM service

## Cloud GPU Setup (Runpod)

1. **Install dependencies:**
   ```bash
   pip install structlog httpx
   ```

2. **Configure LLM endpoint:**
   - If using Runpod's LLM service, update the base URL
   - Or use OpenAI/Anthropic by changing provider in config

3. **Run:**
   ```bash
   python3 -m app.book_writer.ferrari_company
   ```

## Dependencies

### Required
- `structlog>=23.2.0` - Structured logging
- `httpx>=0.25.0` - HTTP client for LLM API calls

### Optional (for full app)
- See `requirements-app.txt` for complete list

