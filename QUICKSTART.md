# 🚀 Quick Start Guide

Get up and running with the Voice-Driven Brainstorming Assistant in 5 minutes!

## Step 1: Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

## Step 2: Configure

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your preferred editor
nano .env  # or vim, code, etc.
```

**Minimum configuration** (for local-only setup):
```bash
STT_BACKEND=whisper_local
LLM_BACKEND=openai
OPENAI_API_KEY=your_key_here
```

**For fully offline** (no API key needed):
```bash
STT_BACKEND=vosk
LLM_BACKEND=http
LLM_HTTP_URL=http://localhost:8000/v1/chat/completions
```

## Step 3: Test Audio

```bash
# Check microphone
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

You should see your microphone listed. Note the device index if you need to specify it.

## Step 4: Run!

```bash
# Start with default project
python3 app.py

# Or specify a project name
python3 app.py --project my-brainstorm
```

## Step 5: Use It!

### Basic Workflow

1. **Press `Space`** to start recording (push-to-talk)
2. **Speak your idea** into the microphone
3. **Release `Space`** to stop recording
4. **Wait** for transcription and AI response
5. **Repeat!**

### Try These Commands

Press `:` to open command mode, then try:

```
:todo Review the ideas tomorrow
:summarize
:export md
:help
```

## Common Issues

### "No microphone detected"
- Check microphone is plugged in
- Grant microphone permissions to terminal
- Try: `python -c "import sounddevice as sd; sd.default.device = 0"`

### "STT backend not available"
- **Whisper**: First run downloads model (~150MB), be patient
- **Vosk**: Download model from https://alphacephei.com/vosk/models

### "LLM backend not available"
- Check your `OPENAI_API_KEY` is correct
- Verify you have API credits
- Try: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore [config.yaml](config.yaml) for customization options
- Check out example workflows below

## Example Workflows

### Product Brainstorming
```bash
python3 app.py --project product-ideas

# Speak: "I want to build a mobile app for tracking habits"
# AI will expand on this with variations and action items
# Use :cluster to organize related ideas
# Use :export docx to create a presentation
```

### Writing Session
```bash
python3 app.py --project novel-outline

# Speak your plot ideas
# Use :tag <id> character,plot to categorize
# Use :summarize to get chapter outlines
# Use :todo to track writing tasks
```

### Meeting Notes
```bash
python3 app.py --project team-meeting

# Record discussion points
# AI extracts action items automatically
# Use :export md for shareable notes
```

## Tips & Tricks

### Keyboard Shortcuts
- `Space` - Quick record (push-to-talk)
- `R` then `Enter` - Longer recording with auto-stop
- `:save` - Force save immediately
- `Ctrl+S` - Same as :save
- `Q` - Quit (auto-saves first)

### Voice Tips
- Speak clearly and at normal pace
- Pause briefly between ideas
- If VAD is enabled, silence auto-stops recording
- Check audio level meter in status bar

### Organization Tips
- Tag ideas as you go: `:tag <id> important,urgent`
- Promote key ideas: `:promote <id>`
- Run `:cluster` every 10-15 ideas
- Use `:summarize recent` for quick recaps

### Export Tips
- `:export md` - Beautiful Markdown with emojis
- `:export docx` - For Word/Google Docs
- `:export csv` - For spreadsheet analysis
- Files saved to `brainstorm/<project>/`

## Advanced Configuration

### Use Local LLM (No API Key)

1. Install Ollama or LM Studio
2. Start local server on port 8000
3. Configure:
```bash
LLM_BACKEND=http
LLM_HTTP_URL=http://localhost:8000/v1/chat/completions
LLM_HTTP_MODEL=llama2
```

### Optimize for Speed

```yaml
# In config.yaml
stt:
  backend: vosk  # Faster than Whisper
  
audio:
  vad_enabled: true  # Auto-stop on silence
  
llm:
  temperature: 0.5  # Faster, more focused responses
  max_tokens: 500   # Shorter responses
```

### Optimize for Quality

```yaml
stt:
  backend: whisper_local
  whisper_model: medium  # Better accuracy
  
llm:
  model: gpt-4-turbo-preview  # Best reasoning
  temperature: 0.7
  max_tokens: 1000
```

## Getting Help

- Press `?` in the app for help overlay
- Type `:help` for command reference
- Check logs: `brainstorm/<project>/brainstorm.log`
- Run with debug: `python app.py --debug`

## What's Next?

Now that you're set up, try:
1. Record 5-10 ideas on any topic
2. Run `:cluster` to see AI organization
3. Run `:summarize` to get an overview
4. Export with `:export md` to see the output

Happy brainstorming! 🧠✨
