# RunPod Quick Start - Core Devices Research

Quick guide to run the Core Devices Research & Discovery phase on RunPod with Mock LLM.

## 🚀 Quick Setup (5 minutes)

### On RunPod Container:

```bash
# 1. Clone the repository
cd /workspace
git clone https://github.com/lebonange2/Umufasha.git
cd Umufasha

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Initialize database
python3 scripts/init_db.py

# 4. Start with Mock LLM (instant responses, no real AI needed)
./start_runpod.sh
```

That's it! The server will start on `http://localhost:8000`

---

## 🌐 Access from Browser

### Option A: RunPod Web Interface (Easiest)
1. Go to your RunPod dashboard
2. Click on your pod
3. Under "TCP Port Mappings", find port `8000`
4. Click the link (e.g., `https://<pod-id>-8000.proxy.runpod.net`)
5. Navigate to Core Devices: `/core-devices`

### Option B: SSH Tunnel
```bash
# On your local machine
ssh -L 8000:localhost:8000 root@<pod-ip> -p <port> -N -f

# Then open in browser:
# http://localhost:8000/core-devices
```

---

## 🧪 Test Research Phase

```bash
# Inside the RunPod container
cd /workspace/Umufasha
python3 test_research_simple.py
```

Expected output:
```
✅ Project created
✅ Research execution started
✅ Research phase completed!
✅ Product Concept: AI-Powered Universal Smart Charger
✅ Primary Need: energy
✅ ALL TESTS PASSED!
```

---

## 🔍 What is Mock LLM?

Mock LLM provides **instant, deterministic AI responses** without requiring:
- ❌ Ollama installation
- ❌ Model downloads (GBs of data)
- ❌ GPU for inference
- ❌ API keys

Perfect for:
- ✅ Development
- ✅ Testing
- ✅ Demos
- ✅ Learning the system

---

## 📊 View in Browser

1. Open: `http://localhost:8000/core-devices` (or RunPod URL)
2. Click **"Create New Project"**
3. Select **"Research Mode"**
4. Click **"Start Research"**
5. Watch the AI agents brainstorm product ideas in real-time!

---

## 🐛 Troubleshooting

### "Connection refused" when testing
**Solution**: Make sure the server is running
```bash
ps aux | grep uvicorn
# If not running:
./start_runpod.sh
```

### Can't access from browser
**Solution**: Expose port 8000 in RunPod dashboard
1. Go to pod settings
2. Under "TCP Port Mappings" → Add port 8000
3. Use the generated URL

### Missing dependencies
```bash
pip3 install -r requirements.txt
```

---

## 🔄 Switch to Real AI (Optional)

To use real Ollama LLM instead of Mock:

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Start Ollama
ollama serve &

# 3. Pull a model
ollama pull gemma2:2b

# 4. Edit .env file
nano .env
# Change: USE_MOCK_LLM=false

# 5. Restart server
pkill -f uvicorn
./start.sh
```

---

## 📝 Files You Created

- `start_runpod.sh` - RunPod-optimized startup script
- `.env` - Environment configuration (auto-created)
- `assistant.db` - SQLite database (auto-created)

---

## ⚡ Quick Commands

```bash
# Start server
./start_runpod.sh

# Stop server
pkill -f uvicorn

# View logs
tail -f /tmp/test_server.log

# Test API
curl http://localhost:8000/health

# Run tests
python3 test_research_simple.py
```

---

## 🎯 What You Get

The Research & Discovery phase will:
1. **Brainstorm** 5+ industries (Consumer Electronics, Smart Home, etc.)
2. **Generate** 4+ product ideas with descriptions
3. **Tag** each idea with a primary human need (energy, health, etc.)
4. **Synthesize** top opportunities
5. **Recommend** a final product concept

All happening in **real-time** with live chat log updates!

---

## 📚 Next Steps

Once Research phase is working:
- Explore other phases (Strategy & Idea Intake, Concept & Differentiation, etc.)
- Switch to real AI for more creative responses
- Customize product ideas by editing prompts

---

**Ready to innovate!** 🚀
