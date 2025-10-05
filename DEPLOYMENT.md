# Deployment Guide

Complete guide for deploying and running the Voice-Driven Brainstorming Assistant.

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows
- **Python**: 3.10 or higher
- **RAM**: 2GB minimum (4GB recommended)
- **Disk**: 500MB for application + models
- **Microphone**: Any USB or built-in microphone

### Required Accounts (Optional)
- **OpenAI API**: For cloud LLM (or use local alternative)
- **OpenAI Whisper API**: For cloud STT (or use local alternative)

## Installation Methods

### Method 1: Quick Install (Recommended)

```bash
# Clone or download the repository
cd ASSISTANT

# Run the setup script
./run.sh

# This will:
# - Create virtual environment
# - Install dependencies
# - Create .env from template
# - Prompt you to configure
```

### Method 2: Manual Install

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# 4. Verify setup
python scripts/verify_setup.py
```

### Method 3: System-wide Install

```bash
# Install as package
pip install -e .

# Run from anywhere
brainstorm --project my-project
```

## Configuration

### Step 1: Environment Variables

Edit `.env` file:

```bash
# For cloud-based (requires API key)
OPENAI_API_KEY=sk-your-key-here
STT_BACKEND=whisper_local
LLM_BACKEND=openai

# For fully offline (no API key needed)
STT_BACKEND=vosk
LLM_BACKEND=http
LLM_HTTP_URL=http://localhost:8000/v1/chat/completions
```

### Step 2: Download Models (if using local STT)

```bash
# For Whisper (recommended)
python scripts/download_models.py whisper --size base

# For Vosk (lightweight)
# Download from: https://alphacephei.com/vosk/models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d models/
```

### Step 3: Test Audio

```bash
# Check microphone
python scripts/check_audio.py

# Should show your microphone and test recording
```

### Step 4: Verify Setup

```bash
# Run verification
python scripts/verify_setup.py

# Should show all green checkmarks
```

## Running

### Basic Usage

```bash
# Default project
python app.py

# Named project
python app.py --project my-brainstorm

# With specific backends
python app.py --stt whisper_local --llm openai

# Debug mode
python app.py --debug
```

### Using Make

```bash
# Run with default project
make run

# Run with specific project
make run PROJECT=my-project

# Other commands
make test          # Run tests
make audio         # Check audio
make models        # Download models
make clean         # Clean temp files
```

### Using Run Script

```bash
# Simple run
./run.sh

# With arguments
./run.sh --project my-project --debug
```

## Deployment Scenarios

### Scenario 1: Personal Use (Local Machine)

**Configuration**:
```bash
STT_BACKEND=whisper_local
LLM_BACKEND=openai
OPENAI_API_KEY=your-key
```

**Pros**: Best accuracy, easy setup
**Cons**: Requires internet for LLM

### Scenario 2: Fully Offline

**Configuration**:
```bash
STT_BACKEND=vosk
LLM_BACKEND=http
LLM_HTTP_URL=http://localhost:8000/v1/chat/completions
```

**Setup Local LLM**:
```bash
# Option A: Ollama
curl https://ollama.ai/install.sh | sh
ollama serve
ollama run llama2

# Option B: LM Studio
# Download from: https://lmstudio.ai/
# Start server on port 8000
```

**Pros**: Complete privacy, no internet needed
**Cons**: Requires more setup, lower quality

### Scenario 3: Team Server

**Setup**:
```bash
# On server
cd ASSISTANT
python app.py --project team-session

# Team members SSH in
ssh user@server
cd ASSISTANT
python app.py --project team-session
```

**Pros**: Shared sessions, centralized storage
**Cons**: Requires SSH access

### Scenario 4: Docker Container (Future)

```bash
# Build image
docker build -t brainstorm-assistant .

# Run container
docker run -it \
  -v $(pwd)/brainstorm:/app/brainstorm \
  -e OPENAI_API_KEY=your-key \
  --device /dev/snd \
  brainstorm-assistant
```

## Production Considerations

### Performance Optimization

**For Speed**:
```yaml
# config.yaml
stt:
  backend: vosk  # Faster than Whisper
  
audio:
  vad_enabled: true  # Auto-stop on silence
  
llm:
  temperature: 0.5
  max_tokens: 500
```

**For Quality**:
```yaml
stt:
  backend: whisper_local
  whisper_model: medium  # or large
  
llm:
  model: gpt-4-turbo-preview
  temperature: 0.7
  max_tokens: 1000
```

### Storage Management

```bash
# Sessions stored in:
brainstorm/<project-name>/

# Backup strategy
tar -czf backup-$(date +%Y%m%d).tar.gz brainstorm/

# Clean old snapshots
find brainstorm/*/versions -name "*.json" -mtime +30 -delete
```

### Security

**API Key Protection**:
```bash
# Never commit .env
echo ".env" >> .gitignore

# Use environment variables in production
export OPENAI_API_KEY=your-key
```

**File Permissions**:
```bash
# Restrict access to session data
chmod 700 brainstorm/
chmod 600 .env
```

**Network Security**:
- Use HTTPS for API calls (default)
- Consider VPN for remote access
- Firewall rules for local LLM servers

## Monitoring

### Logs

```bash
# Application logs
tail -f brainstorm/<project>/brainstorm.log

# Debug mode
python app.py --debug 2>&1 | tee debug.log
```

### Health Checks

```bash
# Verify components
python scripts/verify_setup.py

# Test audio
python scripts/check_audio.py

# Test STT
python -c "from stt.whisper_local import WhisperLocalSTT; print('OK')"

# Test LLM
python -c "from llm.openai_client import OpenAIClient; print('OK')"
```

## Troubleshooting

### Installation Issues

**Problem**: `pip install` fails
```bash
# Solution: Upgrade pip
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Problem**: Python version too old
```bash
# Solution: Use pyenv or conda
pyenv install 3.11
pyenv local 3.11
```

### Runtime Issues

**Problem**: No audio detected
```bash
# Check permissions (Linux)
sudo usermod -a -G audio $USER
# Logout and login

# Check permissions (macOS)
# System Preferences > Security & Privacy > Microphone
```

**Problem**: STT model not found
```bash
# Re-download
python scripts/download_models.py whisper --size base
```

**Problem**: LLM API errors
```bash
# Check API key
echo $OPENAI_API_KEY

# Test connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Performance Issues

**Problem**: Slow transcription
```bash
# Use smaller model
WHISPER_MODEL_SIZE=tiny python app.py

# Or switch to Vosk
STT_BACKEND=vosk python app.py
```

**Problem**: High memory usage
```bash
# Use smaller Whisper model
WHISPER_MODEL_SIZE=base  # instead of large

# Or use Vosk (lower memory)
STT_BACKEND=vosk
```

## Maintenance

### Updates

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update models
python scripts/download_models.py whisper --size base
```

### Backups

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf backups/brainstorm-$DATE.tar.gz brainstorm/
find backups/ -name "*.tar.gz" -mtime +30 -delete
```

### Cleanup

```bash
# Remove old snapshots
find brainstorm/*/versions -name "*.json" -mtime +30 -delete

# Clean temp files
make clean

# Remove old projects
rm -rf brainstorm/old-project-name
```

## Scaling

### Multiple Users

```bash
# Each user gets own project
python app.py --project user1-session
python app.py --project user2-session
```

### Large Sessions

```bash
# For sessions with 1000+ ideas:
# - Increase autosave interval
AUTOSAVE_INTERVAL=60

# - Disable real-time deduplication
# - Run :dedupe manually when needed
```

### Batch Processing

```bash
# Process multiple audio files
for file in recordings/*.wav; do
  python -c "
from stt.whisper_local import WhisperLocalSTT
import numpy as np
stt = WhisperLocalSTT()
# Process $file
"
done
```

## Advanced Deployment

### Systemd Service (Linux)

```ini
# /etc/systemd/system/brainstorm.service
[Unit]
Description=Brainstorming Assistant
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/ASSISTANT
ExecStart=/path/to/venv/bin/python app.py --project server
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable brainstorm
sudo systemctl start brainstorm
```

### Reverse Proxy (for HTTP LLM)

```nginx
# nginx.conf
server {
    listen 80;
    server_name brainstorm.example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Load Balancing (Multiple LLM Backends)

```python
# Custom load balancer
from llm.http_client import HTTPClient

backends = [
    HTTPClient("http://server1:8000/v1/chat/completions", "model1"),
    HTTPClient("http://server2:8000/v1/chat/completions", "model2"),
]

# Round-robin or least-loaded
```

## Support

### Getting Help

1. **Check documentation**: README.md, QUICKSTART.md
2. **Run verification**: `python scripts/verify_setup.py`
3. **Check logs**: `brainstorm/<project>/brainstorm.log`
4. **GitHub issues**: Report bugs or ask questions
5. **Debug mode**: `python app.py --debug`

### Reporting Issues

Include:
- OS and Python version
- Output of `python scripts/verify_setup.py`
- Relevant log excerpts
- Steps to reproduce

---

**Deployment Checklist**:
- [ ] Python 3.10+ installed
- [ ] Dependencies installed
- [ ] .env configured
- [ ] Models downloaded
- [ ] Audio tested
- [ ] Setup verified
- [ ] First session successful

**Next Steps**: See [QUICKSTART.md](QUICKSTART.md) for first run!
