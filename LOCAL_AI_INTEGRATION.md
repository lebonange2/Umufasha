# Local AI Model Integration (Ollama)

## Overview
Added support for local AI models using Ollama, allowing you to run models like Gemma, Llama, Mistral locally without API costs. Users can switch between OpenAI (ChatGPT) and local models via a dropdown in the UI.

## Features

### ✅ Dual AI Backend Support
- **OpenAI (ChatGPT)** - Cloud-based, requires API key
- **Ollama (Local)** - Runs on your machine, free & private

### ✅ UI Model Selector
- Dropdown in brainstorming header
- Shows available models
- Indicates which is active
- One-click switching

### ✅ Automatic Fallback
- If OpenAI key not configured → uses Ollama
- If Ollama not running → uses OpenAI
- Graceful degradation

---

## Installing Ollama

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS
```bash
brew install ollama
```

### Windows
Download from https://ollama.com/download

### Verify Installation
```bash
ollama --version
```

---

## Installing Models

### Gemma 2 (2B) - Fast & Lightweight
```bash
ollama pull gemma2:2b
```

### Gemma 2 (9B) - More Capable
```bash
ollama pull gemma2:9b
```

### Other Popular Models
```bash
ollama pull llama3.2       # Meta's Llama 3.2
ollama pull mistral        # Mistral 7B
ollama pull phi3           # Microsoft Phi-3
ollama pull qwen2.5        # Alibaba Qwen 2.5
```

### List Installed Models
```bash
ollama list
```

---

## Configuration

### 1. Update config.yaml (Optional)
```yaml
llm:
  ollama_model: "gemma2:2b"  # Default model
  ollama_url: "http://localhost:11434"  # Ollama server URL
```

### 2. Environment Variables (Alternative)
```bash
export OLLAMA_MODEL="gemma2:2b"
export OLLAMA_URL="http://localhost:11434"
```

### 3. Default Settings (Auto-detected)
- Model: `gemma2:2b`
- URL: `http://localhost:11434`

---

## Usage

### Starting Ollama Service

**Linux/macOS:**
```bash
ollama serve
```

**Or as systemd service (Linux):**
```bash
systemctl start ollama
```

**Check if running:**
```bash
curl http://localhost:11434/api/tags
```

### Using in Brainstorming Mode

1. **Open Brainstorming:**
   - Go to http://localhost:8000/brainstorm

2. **Find Model Selector:**
   - Located in header next to project name
   - Dropdown shows available models

3. **Choose Model:**
   - Select "🌐 ChatGPT (OpenAI)" for cloud AI
   - Select "🏠 Local (Ollama)" for local AI

4. **Confirmation:**
   - Alert shows which model is active
   - Model name displayed

5. **Use AI:**
   - Type idea → Click "Add with AI"
   - Or click 🤖 on existing idea
   - AI response uses selected model

---

## Model Comparison

| Model | Type | Size | Speed | Quality | Cost |
|-------|------|------|-------|---------|------|
| **ChatGPT (gpt-4o)** | Cloud | N/A | ~8s | Excellent | $$ API |
| **Gemma 2 (2B)** | Local | 1.6GB | ~5s | Good | Free |
| **Gemma 2 (9B)** | Local | 5.5GB | ~15s | Excellent | Free |
| **Llama 3.2** | Local | 2-90GB | Varies | Excellent | Free |
| **Mistral** | Local | 4.1GB | ~10s | Very Good | Free |

### When to Use Each

**ChatGPT (OpenAI):**
- ✅ Best quality responses
- ✅ Fastest with good internet
- ✅ No local resources needed
- ❌ Costs money per request
- ❌ Requires internet
- ❌ Data sent to OpenAI

**Local (Ollama):**
- ✅ Completely free
- ✅ Works offline
- ✅ Private - data stays local
- ✅ No API limits
- ❌ Requires good hardware (GPU recommended)
- ❌ Slower on CPU
- ❌ Takes disk space

---

## Hardware Requirements

### Minimum (CPU Only)
- **RAM:** 8GB
- **Disk:** 5GB free
- **Model:** gemma2:2b
- **Speed:** ~20-30s per response

### Recommended (With GPU)
- **RAM:** 16GB
- **GPU VRAM:** 6GB+
- **Disk:** 10GB free
- **Model:** gemma2:9b or llama3.2
- **Speed:** ~5-10s per response

### Optimal
- **RAM:** 32GB+
- **GPU VRAM:** 16GB+
- **Disk:** 50GB free
- **Model:** Any
- **Speed:** ~3-5s per response

---

## Technical Implementation

### Backend Architecture

**File:** `llm/ollama_client.py` (NEW)
- Implements `LLMBackend` interface
- Communicates with Ollama HTTP API
- Supports chat and completion modes
- Auto-detects available models

**File:** `unified_app.py` (MODIFIED)
- Initializes both OpenAI and Ollama backends
- Stores backends in `llm_backends` dict
- Tracks current backend in `current_llm_type`
- Provides `switch_llm_backend()` function

### API Endpoints

**GET /api/llm/backends**
- Returns available LLM backends
- Shows which models are active
- Indicates online/offline status

**Response:**
```json
{
  "success": true,
  "backends": {
    "openai": {
      "available": true,
      "model": "gpt-4o",
      "active": true
    },
    "ollama": {
      "available": true,
      "model": "gemma2:2b",
      "active": false
    }
  },
  "current": "openai"
}
```

**POST /api/llm/switch**
- Switches active LLM backend
- Validates backend is available
- Updates global `llm_backend`

**Request:**
```json
{
  "backend_type": "ollama"
}
```

**Response:**
```json
{
  "success": true,
  "current": "ollama",
  "model": "gemma2:2b"
}
```

### Frontend Implementation

**File:** `app/templates/brainstorm_mode.html` (MODIFIED)
- Added model selector dropdown
- `loadLLMBackends()` - Populates dropdown
- `switchLLMBackend()` - Switches model
- Shows emoji icons (🌐 for cloud, 🏠 for local)
- Displays model name
- Disables offline models

---

## Testing

### Test Ollama Installation
```bash
# Start Ollama
ollama serve

# In another terminal
ollama run gemma2:2b "Hello, how are you?"
```

### Test API Endpoint
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "gemma2:2b",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

### Test in Application
1. Start application: `./start_unified.sh`
2. Open: http://localhost:8000/brainstorm
3. Check dropdown shows both models
4. Switch to "Local (Ollama)"
5. Add idea with AI
6. Verify local model responds

---

## Troubleshooting

### Ollama Not Showing in Dropdown

**Problem:** Only OpenAI appears

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Restart application
./start_unified.sh
```

### Model Offline Error

**Problem:** Model shows "(offline)"

**Cause:** Model not pulled yet

**Solution:**
```bash
# Pull the model
ollama pull gemma2:2b

# Refresh browser
```

### Slow Responses

**Problem:** Local model takes 30+ seconds

**Cause:** Running on CPU

**Solutions:**
1. Install smaller model: `ollama pull gemma2:2b`
2. Enable GPU support (install CUDA/ROCm)
3. Use OpenAI instead for this session

### Connection Refused

**Problem:** "Failed to connect to Ollama"

**Solution:**
```bash
# Check Ollama status
systemctl status ollama  # Linux
# or
ps aux | grep ollama

# Start if not running
ollama serve
```

---

## Advanced Configuration

### Custom Ollama Port
```yaml
# config.yaml
llm:
  ollama_url: "http://localhost:8080"
```

### Different Model
```yaml
# config.yaml
llm:
  ollama_model: "llama3.2:3b"
```

### GPU Selection (Multi-GPU)
```bash
# Use specific GPU
CUDA_VISIBLE_DEVICES=0 ollama serve
```

### Model Parameters
```yaml
# config.yaml
llm:
  temperature: 0.7
  max_tokens: 2000
```

---

## Model Recommendations

### For Brainstorming
1. **gemma2:2b** - Fast, good quality, small
2. **mistral** - Balanced speed/quality
3. **llama3.2** - Best quality, slower

### For Quick Ideas
- **gemma2:2b** or **phi3**

### For Deep Analysis
- **gemma2:9b** or **llama3.2:8b**

---

## Benefits of Local AI

### ✅ Privacy
- All data stays on your machine
- No data sent to third parties
- HIPAA/GDPR compliant

### ✅ Cost
- No API charges
- Unlimited requests
- One-time setup cost

### ✅ Availability
- Works offline
- No rate limits
- No quota restrictions

### ✅ Customization
- Fine-tune models
- Adjust parameters
- Control behavior

---

## Files Modified/Created

**New Files:**
- `llm/ollama_client.py` - Ollama backend implementation

**Modified Files:**
- `unified_app.py` - Added Ollama support, model switching
- `app/templates/brainstorm_mode.html` - Added UI selector

**Functions Added:**
- `init_backends()` - Initialize both backends
- `switch_llm_backend()` - Switch between backends
- `loadLLMBackends()` (JS) - Load model selector
- `switchLLMBackend()` (JS) - Handle model switching

---

## Summary

✅ **Ollama integration complete**
✅ **Local models supported** (Gemma, Llama, Mistral, etc.)
✅ **UI model selector** in brainstorming mode
✅ **API endpoints** for model management
✅ **Automatic fallback** between OpenAI/Ollama
✅ **Zero API costs** with local models
✅ **Complete privacy** with local processing

**Get Started:**
1. Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
2. Pull model: `ollama pull gemma2:2b`
3. Start Ollama: `ollama serve`
4. Refresh brainstorm page
5. Select "🏠 Local (Ollama)" from dropdown
6. Enjoy free, private AI brainstorming!
