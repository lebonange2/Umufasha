# Running Application on RunPod GPU

This guide explains how to run the Unified Assistant application in your browser while leveraging a RunPod GPU for faster STT (Speech-to-Text) processing with Whisper.

## 🎯 Overview

The application will run in two parts:
- **Frontend & Web Server**: Runs locally on your machine (browser accessible)
- **Whisper STT Processing**: Runs on RunPod GPU for faster transcription

## 📋 Prerequisites

- RunPod account with credits
- SSH access enabled
- Local machine with Python 3.11+
- GPU-enabled RunPod pod (recommended: RTX 3090 or better)

---

## 🚀 Step-by-Step Guide

### **Part 1: Set Up RunPod GPU Instance**

#### 1. Create a RunPod Pod

1. Go to [RunPod.io](https://www.runpod.io/) and log in
2. Click **"Deploy"** → **"GPU Pods"**
3. Select a GPU template:
   - **Recommended**: RTX 3090, RTX 4090, or A5000
   - **Budget Option**: RTX 3080 or RTX 3060 Ti
4. Choose a template:
   - **Option A**: "PyTorch" or "Hugging Face" template (has CUDA pre-installed)
   - **Option B**: "RunPod PyTorch" template
5. Configure storage: At least **20GB** container disk
6. Click **"Deploy On-Demand"** or **"Deploy Spot"** (spot is cheaper)
7. Wait for pod to start and note down:
   - **Pod ID**
   - **SSH Connection String** (e.g., `ssh root@<pod-ip> -p <port> -i ~/.ssh/id_ed25519`)
   - **HTTP Service URL** (if exposed)

#### 2. Connect to Your RunPod Pod

```bash
# Use the SSH command from RunPod dashboard
ssh root@<pod-ip> -p <port> -i ~/.ssh/id_ed25519

# Or if using password authentication
ssh root@<pod-ip> -p <port>
```

#### 3. Install Dependencies on RunPod

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Python and pip (if not already installed)
apt-get install -y python3.11 python3-pip git ffmpeg

# Install PyTorch with CUDA support (if not pre-installed)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install faster-whisper with CUDA support
pip3 install faster-whisper ctranslate2

# Verify CUDA is available
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python3 -c "import torch; print(f'CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')"
```

#### 4. Set Up Whisper API Server on RunPod

Create a simple FastAPI server to handle Whisper transcription:

```bash
# Install FastAPI and uvicorn
pip3 install fastapi uvicorn[standard] python-multipart

# Create the Whisper API server
cat > /root/whisper_api.py << 'EOF'
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
import numpy as np
import io
import wave
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper API Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Whisper model
logger.info("Loading Whisper model...")
model = WhisperModel("base", device="cuda", compute_type="float16")
logger.info("Whisper model loaded successfully on GPU")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": "base",
        "device": "cuda"
    }

@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio file."""
    try:
        # Read audio data
        audio_bytes = await audio.read()
        
        # Parse WAV file
        with io.BytesIO(audio_bytes) as audio_buffer:
            with wave.open(audio_buffer, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                audio_array = np.frombuffer(frames, dtype=np.int16)
                sample_rate = wav_file.getframerate()
        
        # Convert to float32 and normalize
        audio_float = audio_array.astype(np.float32) / 32768.0
        
        logger.info(f"Transcribing audio: {len(audio_array)} samples, {sample_rate}Hz")
        
        # Transcribe
        segments, info = model.transcribe(
            audio_float,
            language="en",
            beam_size=5,
            vad_filter=True
        )
        
        # Collect transcription
        text = " ".join([segment.text for segment in segments]).strip()
        
        logger.info(f"Transcription complete: {text[:50]}...")
        
        return {
            "success": True,
            "text": text,
            "language": info.language,
            "duration": info.duration
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
EOF
```

#### 5. Start Whisper API Server on RunPod

```bash
# Run in background with nohup
nohup python3 /root/whisper_api.py > /root/whisper_api.log 2>&1 &

# Check if it's running
ps aux | grep whisper_api

# Check logs
tail -f /root/whisper_api.log
```

#### 6. Expose the Service

**Option A: Using RunPod's HTTP Service**
1. Go to RunPod dashboard
2. Click on your pod
3. Under "TCP Port Mappings", expose port `8080`
4. Note the public URL (e.g., `https://<pod-id>-8080.proxy.runpod.net`)

**Option B: Using SSH Tunnel (if HTTP not available)**
```bash
# On your local machine, create SSH tunnel
ssh -L 8080:localhost:8080 root@<pod-ip> -p <port> -i ~/.ssh/id_ed25519 -N -f
```

---

### **Part 2: Configure Local Application**

#### 1. Update Local Configuration

Create or update `.env` file in your local project:

```bash
# On your local machine
cd /home/uwisiyose/ASSISTANT

# Create/edit .env file
cat > .env << 'EOF'
# OpenAI API (for LLM features)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=sk-ant-your_claude_key_here

# RunPod Whisper API
WHISPER_API_URL=https://<pod-id>-8080.proxy.runpod.net
# Or if using SSH tunnel:
# WHISPER_API_URL=http://localhost:8080

# Mock mode (disable for production)
MOCK_MODE=false
EOF
```

#### 2. Update STT Configuration

Update `config.yaml` to use the remote Whisper API:

```yaml
# STT settings
stt:
  backend: whisper_api  # Use API instead of local
  whisper_api_url: ${WHISPER_API_URL}/transcribe
  language: en
```

#### 3. Create Custom STT Backend (if needed)

If the application doesn't support remote Whisper API, create a custom backend:

```bash
cat > stt/whisper_remote.py << 'EOF'
"""Remote Whisper API STT backend."""
import os
import httpx
import numpy as np
import io
import wave
from typing import Optional
from .base import STTBackend
from utils.logging import get_logger

logger = get_logger('whisper_remote')

class WhisperRemoteSTT(STTBackend):
    """Whisper Remote API STT backend."""
    
    def __init__(self, api_url: str, sample_rate: int = 16000):
        self.api_url = api_url.rstrip('/') + '/transcribe'
        self.sample_rate = sample_rate
        self._available = self._check_availability()
        logger.info(f"Initialized Whisper Remote STT: {self.api_url}")
    
    def _check_availability(self) -> bool:
        """Check if remote API is available."""
        try:
            health_url = self.api_url.replace('/transcribe', '/health')
            response = httpx.get(health_url, timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Remote Whisper API not available: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if backend is available."""
        return self._available
    
    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio using remote API."""
        try:
            # Convert numpy array to WAV bytes
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio.astype(np.int16).tobytes())
            
            wav_bytes = wav_buffer.getvalue()
            
            # Send to remote API
            logger.info(f"Sending {len(wav_bytes)} bytes to remote API")
            
            files = {'audio': ('audio.wav', wav_bytes, 'audio/wav')}
            response = httpx.post(
                self.api_url,
                files=files,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                text = result.get('text', '')
                logger.info(f"Transcription received: {text[:50]}...")
                return text
            else:
                logger.error(f"API error: {result}")
                return ""
                
        except Exception as e:
            logger.error(f"Remote transcription error: {e}")
            return ""
EOF
```

---

### **Part 3: Run the Application**

#### 1. Test RunPod Connection

```bash
# Test the Whisper API
curl https://<pod-id>-8080.proxy.runpod.net/health

# Or if using SSH tunnel
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "model": "base",
  "device": "cuda"
}
```

#### 2. Start Local Application

```bash
# On your local machine
cd /home/uwisiyose/ASSISTANT

# Run the setup (if needed)
./setup.sh

# Start the application
./start.sh

# Or run directly with Python
python3 unified_app.py --host 0.0.0.0 --port 8000
```

#### 3. Access in Browser

Open your browser and navigate to:
```
http://localhost:8000
```

Or to access from other devices on your network:
```
http://<your-local-ip>:8000
```

#### 4. Test Brainstorming Mode

1. Go to **Brainstorming Mode**: `http://localhost:8000/brainstorm`
2. Click **"Start Session"**
3. Click the microphone icon or use the record button
4. Speak and watch the transcription appear (processed on RunPod GPU)

---

## 🔧 Advanced Configuration

### Using Larger Whisper Models

For better accuracy, use larger models (requires more GPU memory):

```bash
# On RunPod pod, edit whisper_api.py
# Change this line:
model = WhisperModel("base", device="cuda", compute_type="float16")

# To one of these:
model = WhisperModel("small", device="cuda", compute_type="float16")   # ~2GB VRAM
model = WhisperModel("medium", device="cuda", compute_type="float16")  # ~5GB VRAM
model = WhisperModel("large-v2", device="cuda", compute_type="float16") # ~10GB VRAM

# Restart the service
pkill -f whisper_api.py
nohup python3 /root/whisper_api.py > /root/whisper_api.log 2>&1 &
```

### Performance Optimization

```python
# In whisper_api.py, optimize transcription settings:
segments, info = model.transcribe(
    audio_float,
    language="en",
    beam_size=5,           # Increase for better quality (default: 5)
    vad_filter=True,       # Voice Activity Detection
    vad_parameters={
        "threshold": 0.5,
        "min_silence_duration_ms": 500
    },
    condition_on_previous_text=True,
    temperature=0.0        # More deterministic
)
```

### Monitoring GPU Usage

```bash
# On RunPod pod
watch -n 1 nvidia-smi
```

---

## 📊 Cost Optimization

### Using Spot Instances
- RunPod spot instances are ~70% cheaper
- Good for development and testing
- May be interrupted (save work frequently)

### Auto-Shutdown
```bash
# On RunPod pod, add auto-shutdown after inactivity
cat > /root/auto_shutdown.sh << 'EOF'
#!/bin/bash
TIMEOUT=3600  # 1 hour
while true; do
    IDLE=$(curl -s http://localhost:8080/stats 2>/dev/null | grep -o '"requests":0')
    if [ "$IDLE" ]; then
        echo "Idle detected, shutting down in $TIMEOUT seconds..."
        sleep $TIMEOUT
        poweroff
    fi
    sleep 300  # Check every 5 minutes
done
EOF
chmod +x /root/auto_shutdown.sh
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused" to RunPod API

**Solution**:
```bash
# Check if service is running on RunPod
ssh root@<pod-ip> -p <port>
ps aux | grep whisper_api

# Check firewall
ufw status

# Check logs
tail -f /root/whisper_api.log
```

### Issue: CUDA out of memory

**Solution**:
```python
# Use smaller model or int8 quantization
model = WhisperModel("base", device="cuda", compute_type="int8")
```

### Issue: Slow transcription

**Diagnosis**:
```bash
# Check GPU utilization
nvidia-smi

# If GPU is idle, model might be running on CPU
# Check logs for device placement
```

**Solution**:
- Verify CUDA is available
- Use larger batch sizes
- Reduce beam_size parameter

### Issue: Local app can't connect to RunPod

**Solution**:
```bash
# Test connectivity
curl -v https://<pod-id>-8080.proxy.runpod.net/health

# Check DNS resolution
nslookup <pod-id>-8080.proxy.runpod.net

# Try SSH tunnel instead
ssh -L 8080:localhost:8080 root@<pod-ip> -p <port> -N -f
```

---

## 🎯 Quick Reference Commands

### Start RunPod Service
```bash
ssh root@<pod-ip> -p <port>
cd /root
nohup python3 whisper_api.py > whisper_api.log 2>&1 &
```

### Start Local Application
```bash
cd /home/uwisiyose/ASSISTANT
./start.sh
```

### View Logs
```bash
# RunPod logs
ssh root@<pod-ip> -p <port> "tail -f /root/whisper_api.log"

# Local logs
tail -f logs/unified_app.log
```

### Stop Services
```bash
# Stop RunPod service
ssh root@<pod-ip> -p <port> "pkill -f whisper_api.py"

# Stop local app
./stop.sh
```

---

## 📚 Additional Resources

- [RunPod Documentation](https://docs.runpod.io/)
- [Faster Whisper GitHub](https://github.com/guillaumekln/faster-whisper)
- [Whisper Model Sizes](https://github.com/openai/whisper#available-models-and-languages)

---

## ✅ Checklist

- [ ] RunPod pod created and running
- [ ] SSH access configured
- [ ] Whisper API server running on RunPod
- [ ] Port 8080 exposed via RunPod or SSH tunnel
- [ ] Local `.env` configured with API URL
- [ ] Local application running
- [ ] Browser can access `http://localhost:8000`
- [ ] Brainstorm mode tested and working
- [ ] GPU utilization confirmed with `nvidia-smi`

---

**You're now ready to use GPU-accelerated Whisper transcription in your browser!** 🚀
