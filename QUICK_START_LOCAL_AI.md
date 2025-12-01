# Quick Start: Local AI with Llama3.1

## 3-Step Setup

### Step 1: Install Ollama and Download Model

On your RunPod instance:

```bash
cd /path/to/ASSISTANT
./setup_ollama.sh
```

This installs Ollama and downloads llama3.1 (~5 minutes depending on connection).

### Step 2: Verify It Works

```bash
# Test Ollama directly
ollama run llama3.1 "Hello, test"

# Test via Python
python test_local_llm.py
```

### Step 3: Start Your App

```bash
./start_server.sh
```

Your app now uses llama3.1 by default! 🚀

## Configuration

The app is **already configured** to use local models:
- ✅ Provider: `local` (default)
- ✅ Model: `llama3.1` (default)
- ✅ URL: `http://localhost:11434/v1` (default)

No configuration needed unless you want to change it!

## Switching Models

Want to use a different model?

```bash
# Pull a different model
ollama pull mistral
ollama pull codellama

# Update .env
LLM_MODEL=mistral
```

## Switching Back to Cloud

Need to use OpenAI/Anthropic instead?

```bash
# In .env file:
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=your-key
```

## Troubleshooting

**Ollama not starting?**
```bash
ollama serve
```

**Model not found?**
```bash
ollama pull llama3.1
```

**Test connection:**
```bash
python test_local_llm.py
```

That's it! Your app now runs faster with local AI. 🎉

