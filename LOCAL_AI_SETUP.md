# Local AI Model Setup Guide

This guide explains how to use local AI models (via Ollama) with your application, with llama3.1 as the default model.

## Overview

The application now supports local AI models using Ollama, which runs directly on your RunPod GPU instance. This provides:
- **Faster responses** (no API latency)
- **No API costs** (runs locally)
- **Privacy** (data stays on your instance)
- **GPU acceleration** (utilizes your RunPod GPU)

## Quick Start

### 1. Install and Setup Ollama

Run the setup script on your RunPod instance:

```bash
cd /path/to/ASSISTANT
./setup_ollama.sh
```

This will:
- Install Ollama if not already installed
- Start the Ollama server
- Download the llama3.1 model (~4-8GB)

### 2. Verify Installation

Test that Ollama is working:

```bash
# Test Ollama CLI
ollama run llama3.1 "Hello, how are you?"

# Test API endpoint
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "Say hello"
}'
```

### 3. Configure Application

The application is already configured to use local models by default:

- **Provider**: `local` (Ollama)
- **Model**: `llama3.1`
- **URL**: `http://localhost:11434/v1`

You can override these in your `.env` file:

```bash
# Use local model (default)
LLM_PROVIDER=local
LLM_MODEL=llama3.1
LLM_LOCAL_URL=http://localhost:11434/v1

# Or switch to OpenAI
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o
# OPENAI_API_KEY=your-key

# Or switch to Anthropic
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-3-5-sonnet-20241022
# ANTHROPIC_API_KEY=your-key
```

### 4. Start Your Application

```bash
./start_server.sh
```

The application will now use the local llama3.1 model by default!

## Available Models

Ollama supports many models. You can pull and use different models:

```bash
# List available models
ollama list

# Pull other models
ollama pull llama3.2          # Latest Llama 3.2
ollama pull mistral           # Mistral 7B
ollama pull codellama        # Code-focused model
ollama pull phi3             # Microsoft Phi-3
ollama pull gemma2           # Google Gemma 2

# Use a different model in your app
# Set in .env: LLM_MODEL=mistral
```

## Model Sizes and GPU Requirements

| Model | Size | VRAM Required | Best For |
|-------|------|---------------|----------|
| llama3.1:8b | ~4.7GB | 8GB+ | General purpose, fast |
| llama3.1:70b | ~40GB | 80GB+ | Higher quality, slower |
| mistral:7b | ~4.1GB | 8GB+ | Fast, efficient |
| codellama:13b | ~7.3GB | 16GB+ | Code generation |

**Recommendation for RunPod**: Start with `llama3.1:8b` (default) as it's a good balance of quality and speed.

## Running Ollama as a Service

To keep Ollama running in the background:

### Option 1: Using systemd (if available)

```bash
# Create service file
sudo tee /etc/systemd/system/ollama.service > /dev/null <<EOF
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable ollama
sudo systemctl start ollama
```

### Option 2: Using screen/tmux

```bash
# Start in screen session
screen -S ollama
ollama serve
# Press Ctrl+A then D to detach

# Reattach later
screen -r ollama
```

### Option 3: Using nohup

```bash
nohup ollama serve > /tmp/ollama.log 2>&1 &
```

## Performance Optimization

### GPU Acceleration

Ollama automatically uses GPU if available. Verify:

```bash
# Check GPU usage
nvidia-smi

# Should show ollama process using GPU
```

### Model Quantization

For faster inference, use quantized models:

```bash
# Pull quantized version (smaller, faster)
ollama pull llama3.1:8b-q4_0  # 4-bit quantization
```

### Batch Processing

For multiple requests, Ollama handles them efficiently. The FastAPI app will queue requests automatically.

## Troubleshooting

### Issue: Ollama not starting

```bash
# Check if port 11434 is in use
netstat -tuln | grep 11434

# Kill existing process if needed
pkill ollama

# Start fresh
ollama serve
```

### Issue: Model not found

```bash
# List installed models
ollama list

# Pull the model
ollama pull llama3.1
```

### Issue: Out of memory

```bash
# Use a smaller model
ollama pull llama3.1:8b

# Or use quantized version
ollama pull llama3.1:8b-q4_0
```

### Issue: Slow responses

1. **Check GPU usage**: `nvidia-smi` - should show Ollama using GPU
2. **Use smaller model**: Try `llama3.1:8b` instead of larger variants
3. **Check system resources**: `htop` or `top`
4. **Verify model is loaded**: First request is slower (model loading)

### Issue: API connection refused

```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Should return list of models
```

## Switching Between Providers

You can easily switch between local and cloud providers:

### Use Local (Ollama)
```bash
# In .env or environment
export LLM_PROVIDER=local
export LLM_MODEL=llama3.1
```

### Use OpenAI
```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4o
export OPENAI_API_KEY=your-key
```

### Use Anthropic
```bash
export LLM_PROVIDER=anthropic
export LLM_MODEL=claude-3-5-sonnet-20241022
export ANTHROPIC_API_KEY=your-key
```

## API Compatibility

Ollama uses OpenAI-compatible API format, so the existing code works without changes. The LLMClient automatically handles:
- OpenAI format (used by Ollama)
- Anthropic format (for Claude)
- Custom endpoints

## Monitoring

### Check Ollama Status

```bash
# List running models
ollama list

# Check API
curl http://localhost:11434/api/tags

# Monitor GPU usage
watch -n 1 nvidia-smi
```

### Application Logs

The FastAPI app logs LLM requests. Check logs for:
- Model being used
- Response times
- Any errors

## Best Practices

1. **Start with default model**: `llama3.1:8b` is a good starting point
2. **Monitor GPU memory**: Use `nvidia-smi` to ensure you have enough VRAM
3. **Keep Ollama running**: Use systemd or screen to keep it persistent
4. **Test before production**: Verify model responses meet your needs
5. **Fallback to cloud**: Keep API keys configured as backup

## Next Steps

1. Run `./setup_ollama.sh` to install and configure
2. Test with: `ollama run llama3.1 "Hello"`
3. Start your app: `./start_server.sh`
4. Access mindmapper and test AI features

Your application will now use the local llama3.1 model by default, providing fast, private, and cost-free AI responses!

