# 🧠 Voice-Driven Brainstorming Assistant

A production-ready terminal application for voice-driven brainstorming with AI assistance. Speak your ideas, get intelligent feedback, and organize your thoughts seamlessly.

## Features

### 🎤 Voice Input
- **Push-to-talk** or continuous recording with Voice Activity Detection (VAD)
- **Multiple STT backends**: Local Whisper, Vosk, or OpenAI Whisper API
- Real-time audio level visualization
- Cross-platform microphone support

### 🤖 AI Assistant
- **Intelligent brainstorming** with idea expansion and refinement
- **Automatic tagging** and categorization
- **Clustering** related ideas into themes
- **Action item generation** with priorities
- **Summaries** of sessions or specific clusters
- **Duplicate detection** using semantic similarity

### 📝 Organization
- **Structured knowledge base** with ideas, clusters, and actions
- **Tagging system** for easy categorization
- **Promote key ideas** for quick reference
- **Search** with semantic similarity
- **Transcript** of all conversations

### 💾 Storage & Export
- **Autosave** with configurable intervals
- **Version snapshots** for history tracking
- **Multiple export formats**: Markdown, DOCX, CSV, JSON
- **Local-first** with no cloud dependencies by default

### 🖥️ Dual Interface
- **Terminal UI** - Rich TUI built with Textual for power users
- **Web UI** - Modern browser-based interface for ease of use
- **Split-panel layout**: Transcript, Assistant, Organizer
- **Command palette** for all operations
- **Keyboard shortcuts** for efficient workflow
- **Real-time updates** and status indicators

## Installation

### Requirements
- Python 3.10+
- Linux, macOS, or Windows
- Microphone access

### Setup

1. **Clone or download** the repository

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment** (copy and edit):
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
OPENAI_API_KEY=your_key_here
STT_BACKEND=whisper_local
LLM_BACKEND=openai
```

4. **Download models** (for offline STT):

For Whisper (recommended):
```bash
# Models download automatically on first run
# Or pre-download: python -c "from faster_whisper import WhisperModel; WhisperModel('base')"
```

For Vosk:
```bash
# Download from https://alphacephei.com/vosk/models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d models/
```

## Usage

### Terminal Interface

Start a brainstorming session in the terminal:
```bash
python app.py --project my-project
```

### Web Interface

Start the web server and use your browser:
```bash
./run_web.sh
# Then open http://localhost:5000 in your browser
```

### Command Line Options

```bash
python app.py [OPTIONS]

Options:
  --project, -p NAME       Project name (default: "default")
  --config, -c PATH        Custom config file
  --stt BACKEND           STT backend: whisper_local|vosk|whisper_api
  --llm BACKEND           LLM backend: openai|http
  --debug                 Enable debug logging
```

### Keyboard Shortcuts

#### Recording
- `Space` - Push-to-talk (hold to record)
- `R` - Start recording
- `Enter` - Stop recording

#### Commands
- `:` - Open command palette
- `/` - Search ideas
- `?` - Show help
- `Q` - Quit

#### Other
- `↑/↓` - Scroll panels
- `Tab` - Switch focus
- `Ctrl+S` - Save now

### Commands

Type `:` to open the command palette, then:

#### Idea Management
- `:tag <id> <tag1,tag2>` - Add tags to an idea
- `:del <id>` - Delete an idea
- `:promote <id>` - Mark as key idea
- `:search <query>` - Search ideas

#### Organization
- `:cluster` - Generate thematic clusters
- `:dedupe` - Find duplicate ideas
- `:summarize [scope]` - Generate summary (session|recent|cluster:id)

#### Actions
- `:todo <text>` - Add action item

#### System
- `:save` - Save immediately
- `:export <format>` - Export (md|docx|csv)
- `:config` - Show configuration
- `:help` - Show help

## Configuration

### Environment Variables (`.env`)

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# LLM Backend (openai|http)
LLM_BACKEND=openai

# Custom HTTP LLM (for self-hosted)
LLM_HTTP_URL=http://localhost:8000/v1/chat/completions
LLM_HTTP_MODEL=local-model

# STT Backend (whisper_local|vosk|whisper_api)
STT_BACKEND=whisper_local
WHISPER_MODEL_SIZE=base

# Audio Settings
SAMPLE_RATE=16000
VAD=true

# Autosave
AUTOSAVE_INTERVAL=30
```

### Config File (`config.yaml`)

See `config.yaml` for detailed settings:
- Audio parameters (sample rate, VAD settings)
- STT/LLM configuration
- Brainstorming behavior (auto-tag, clustering, deduplication)
- Storage settings (autosave, snapshots)
- UI preferences

## Architecture

```
app.py                    # Main entry point
├── audio/
│   ├── mic.py           # Microphone recording
│   └── vad.py           # Voice Activity Detection
├── stt/
│   ├── base.py          # STT interface
│   ├── whisper_local.py # Local Whisper
│   ├── vosk_local.py    # Vosk
│   └── whisper_cloud.py # OpenAI Whisper API
├── llm/
│   ├── base.py          # LLM interface
│   ├── openai_client.py # OpenAI client
│   ├── http_client.py   # Generic HTTP client
│   └── prompts.py       # Prompt templates
├── brain/
│   ├── model.py         # Data models
│   ├── organizer.py     # Session management
│   ├── dedupe.py        # Deduplication
│   └── assistant.py     # AI assistant logic
├── storage/
│   ├── files.py         # File storage
│   ├── autosave.py      # Autosave manager
│   └── exporters.py     # Export formats
├── tui/
│   ├── main_view.py     # Main TUI app
│   ├── widgets.py       # Custom widgets
│   └── app.tcss         # Textual CSS
└── utils/
    ├── config.py        # Configuration
    └── logging.py       # Logging utilities
```

## Output Structure

```
brainstorm/
└── <project-name>/
    ├── ledger.json          # Full session data
    ├── notes.md             # Primary Markdown document
    ├── ideas.csv            # Ideas export
    ├── notes.docx           # DOCX export
    └── versions/
        └── snapshot_*.json  # Version history
```

## STT Backend Comparison

| Backend | Speed | Accuracy | Size | Offline | Cost |
|---------|-------|----------|------|---------|------|
| **whisper_local** (base) | Medium | High | ~150MB | ✅ | Free |
| **whisper_local** (small) | Medium | Higher | ~500MB | ✅ | Free |
| **vosk** | Fast | Medium | ~40MB | ✅ | Free |
| **whisper_api** | Fast | Highest | N/A | ❌ | $0.006/min |

## LLM Backend Options

### OpenAI
```bash
LLM_BACKEND=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
```

### Self-Hosted (OpenAI-compatible API)
```bash
LLM_BACKEND=http
LLM_HTTP_URL=http://localhost:8000/v1/chat/completions
LLM_HTTP_MODEL=llama-2-7b
```

Compatible with:
- LM Studio
- Ollama (with OpenAI compatibility layer)
- vLLM
- Text Generation WebUI
- Any OpenAI-compatible endpoint

## Privacy & Security

- **Local-first**: All data stored locally by default
- **No telemetry**: No usage tracking or analytics
- **API key safety**: Keys redacted in logs
- **Clear indicators**: Shows when online services are active
- **Offline mode**: Full functionality with local STT/LLM

## Troubleshooting

### Audio Issues

**No microphone detected:**
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

**Permission denied:**
- Linux: Add user to `audio` group
- macOS: Grant microphone permission in System Preferences
- Windows: Check Privacy settings

### STT Issues

**Whisper model download fails:**
```bash
# Manual download
python -c "from faster_whisper import WhisperModel; WhisperModel('base', download_root='./models')"
```

**Vosk model not found:**
- Download from https://alphacephei.com/vosk/models
- Extract to `models/` directory
- Update `VOSK_MODEL_PATH` in `.env`

### LLM Issues

**OpenAI API errors:**
- Check API key is valid
- Verify billing is active
- Check rate limits

**HTTP LLM not responding:**
- Verify endpoint URL
- Check if server is running
- Test with curl: `curl -X POST <url> -H "Content-Type: application/json" -d '{"model":"test","messages":[]}'`

## Development

### Running Tests
```bash
pytest tests/
```

### Debug Mode
```bash
python app.py --debug
```

Logs are written to `brainstorm/<project>/brainstorm.log`

## Roadmap

- [ ] Multi-language support
- [ ] Voice output (TTS)
- [ ] Collaborative sessions
- [ ] Mind map visualization
- [ ] Mobile companion app
- [ ] Plugin system
- [ ] Cloud sync (optional)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Built with**: Python, Textual, Whisper, OpenAI, and ❤️
