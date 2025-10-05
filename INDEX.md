# 🧠 Voice-Driven Brainstorming Assistant - Complete Index

## Quick Navigation

### 🚀 Getting Started
1. **[README.md](README.md)** - Main documentation and overview
2. **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
3. **[EXAMPLES.md](EXAMPLES.md)** - Real-world usage examples

### 📚 Documentation
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Technical overview and architecture
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[LICENSE](LICENSE)** - MIT License

### 🔧 Configuration
- **[.env.example](.env.example)** - Environment variables template
- **[config.yaml](config.yaml)** - Application configuration
- **[requirements.txt](requirements.txt)** - Python dependencies

### 🏃 Running
```bash
# Quick start
./run.sh

# Or directly
python app.py --project my-project

# With make
make run PROJECT=my-project
```

### 🛠️ Utilities
```bash
# Verify setup
python scripts/verify_setup.py

# Check audio
python scripts/check_audio.py

# Download models
python scripts/download_models.py whisper --size base
```

## Project Structure

```
ASSISTANT/
├── 📄 Core Application
│   ├── app.py                      # Main entry point
│   ├── setup.py                    # Package setup
│   └── Makefile                    # Build commands
│
├── 🎤 Audio Module
│   └── audio/
│       ├── mic.py                  # Microphone recording
│       └── vad.py                  # Voice Activity Detection
│
├── 🗣️ Speech-to-Text
│   └── stt/
│       ├── base.py                 # STT interface
│       ├── whisper_local.py        # Local Whisper
│       ├── vosk_local.py           # Vosk offline
│       └── whisper_cloud.py        # OpenAI Whisper API
│
├── 🤖 LLM Integration
│   └── llm/
│       ├── base.py                 # LLM interface
│       ├── openai_client.py        # OpenAI API
│       ├── http_client.py          # Generic HTTP
│       └── prompts.py              # Prompt templates
│
├── 🧠 Brain (Core Logic)
│   └── brain/
│       ├── model.py                # Data models
│       ├── organizer.py            # Session management
│       ├── dedupe.py               # Deduplication
│       └── assistant.py            # AI assistant
│
├── 💾 Storage
│   └── storage/
│       ├── files.py                # File I/O
│       ├── autosave.py             # Autosave manager
│       └── exporters.py            # Export formats
│
├── 🖥️ Terminal UI
│   └── tui/
│       ├── main_view.py            # Main application
│       ├── widgets.py              # Custom widgets
│       └── app.tcss                # Textual CSS
│
├── 🔧 Utilities
│   └── utils/
│       ├── config.py               # Configuration
│       └── logging.py              # Logging
│
├── 🧪 Tests
│   └── tests/
│       ├── test_brain.py           # Brain module tests
│       └── test_storage.py         # Storage tests
│
├── 📜 Scripts
│   └── scripts/
│       ├── check_audio.py          # Audio device checker
│       ├── download_models.py      # Model downloader
│       └── verify_setup.py         # Setup verification
│
└── 📚 Documentation
    ├── README.md                   # Main documentation
    ├── QUICKSTART.md               # Quick start guide
    ├── EXAMPLES.md                 # Usage examples
    ├── PROJECT_SUMMARY.md          # Technical overview
    ├── CONTRIBUTING.md             # Development guide
    ├── CHANGELOG.md                # Version history
    └── INDEX.md                    # This file
```

## Feature Map

### Voice Input
- **Files**: `audio/mic.py`, `audio/vad.py`
- **Features**: Push-to-talk, VAD, audio level meter
- **Commands**: `Space` (record), `R` (start), `Enter` (stop)

### Speech Recognition
- **Files**: `stt/*.py`
- **Backends**: Whisper (local/cloud), Vosk
- **Config**: `STT_BACKEND`, `WHISPER_MODEL_SIZE`

### AI Assistant
- **Files**: `brain/assistant.py`, `llm/*.py`
- **Features**: Idea expansion, tagging, clustering, summarization
- **Config**: `LLM_BACKEND`, `OPENAI_API_KEY`

### Organization
- **Files**: `brain/organizer.py`, `brain/model.py`
- **Features**: Ideas, clusters, actions, tags, search
- **Commands**: `:tag`, `:promote`, `:cluster`, `:search`

### Storage
- **Files**: `storage/*.py`
- **Features**: Autosave, snapshots, exports
- **Formats**: Markdown, DOCX, CSV, JSON
- **Commands**: `:save`, `:export`

### Terminal UI
- **Files**: `tui/*.py`
- **Features**: Three-panel layout, command palette, status bar
- **Shortcuts**: See keyboard shortcuts section

## Command Reference

### Recording
| Key | Action |
|-----|--------|
| `Space` | Push-to-talk (hold to record) |
| `R` | Start recording |
| `Enter` | Stop recording |

### Navigation
| Key | Action |
|-----|--------|
| `↑/↓` | Scroll panels |
| `Tab` | Switch focus |
| `Q` | Quit |
| `?` | Help |

### Commands (type `:` first)
| Command | Description |
|---------|-------------|
| `:tag <id> <tags>` | Add tags to idea |
| `:promote <id>` | Mark as key idea |
| `:del <id>` | Delete idea |
| `:todo <text>` | Add action item |
| `:cluster` | Generate clusters |
| `:dedupe` | Find duplicates |
| `:search <query>` | Search ideas |
| `:summarize [scope]` | Generate summary |
| `:export <format>` | Export (md/docx/csv) |
| `:save` | Save now |
| `:config` | Show configuration |

## Configuration Guide

### Environment Variables (.env)
```bash
# Required for OpenAI
OPENAI_API_KEY=sk-...

# Backend selection
STT_BACKEND=whisper_local    # whisper_local|vosk|whisper_api
LLM_BACKEND=openai           # openai|http

# Optional
WHISPER_MODEL_SIZE=base      # tiny|base|small|medium|large
SAMPLE_RATE=16000
VAD=true
AUTOSAVE_INTERVAL=30
```

### Config File (config.yaml)
- **Audio**: Sample rate, VAD settings, silence detection
- **STT**: Model paths, languages
- **LLM**: Temperature, max tokens, endpoints
- **Brainstorming**: Auto-tag, clustering, deduplication
- **Storage**: Autosave interval, snapshots
- **UI**: Theme, keybindings, panel layout

## Development

### Setup Development Environment
```bash
# Clone and setup
git clone <repo>
cd ASSISTANT
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install dev dependencies
pip install pytest black flake8 mypy

# Verify setup
python scripts/verify_setup.py
```

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test
pytest tests/test_brain.py -v
```

### Code Quality
```bash
# Format code
black .

# Lint
flake8 .

# Type check
mypy app.py brain/ llm/ storage/

# All checks
make check
```

### Adding Features
1. **New STT Backend**: Inherit from `stt/base.py:STTBackend`
2. **New LLM Backend**: Inherit from `llm/base.py:LLMBackend`
3. **New Export Format**: Add to `storage/exporters.py`
4. **New Widget**: Add to `tui/widgets.py`

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Troubleshooting

### Common Issues

**No audio detected**
```bash
# Check devices
python scripts/check_audio.py

# Test microphone
python -c "import sounddevice as sd; print(sd.query_devices())"
```

**STT not working**
```bash
# Download models
python scripts/download_models.py whisper --size base

# Check backend
python -c "from faster_whisper import WhisperModel; print('OK')"
```

**LLM errors**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Import errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Debug Mode
```bash
# Run with debug logging
python app.py --debug

# Check logs
tail -f brainstorm/<project>/brainstorm.log
```

## Use Cases

1. **Product Development**: Feature brainstorming, roadmap planning
2. **Content Creation**: Article outlines, video scripts, course planning
3. **Problem Solving**: Bug investigation, solution exploration
4. **Meeting Notes**: Discussion capture, action item extraction
5. **Creative Writing**: Plot development, character creation
6. **Research**: Note collection, literature review
7. **Personal**: Voice journaling, goal planning
8. **Event Planning**: Task organization, timeline creation

See [EXAMPLES.md](EXAMPLES.md) for detailed workflows.

## Resources

### Documentation
- [README.md](README.md) - Complete guide
- [QUICKSTART.md](QUICKSTART.md) - Fast setup
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Architecture

### External Links
- **Textual**: https://textual.textualize.io/
- **Whisper**: https://github.com/openai/whisper
- **Vosk**: https://alphacephei.com/vosk/
- **OpenAI API**: https://platform.openai.com/docs

### Community
- **Issues**: GitHub issue tracker
- **Discussions**: GitHub discussions
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## Quick Commands

```bash
# Installation
pip install -r requirements.txt
cp .env.example .env
# Edit .env

# Verification
python scripts/verify_setup.py

# Run
python app.py --project my-project

# Development
make test          # Run tests
make format        # Format code
make lint          # Lint code
make check         # All checks

# Utilities
make audio         # Check audio
make models        # Download models
make clean         # Clean temp files
```

## Version Information

- **Current Version**: 1.0.0
- **Python Required**: 3.10+
- **Platform**: Linux, macOS, Windows
- **License**: MIT

## Support

- **Documentation**: This repository
- **Issues**: GitHub issue tracker
- **Questions**: GitHub discussions
- **Email**: See CONTRIBUTING.md

---

**Last Updated**: 2025-01-15  
**Status**: Production Ready ✅
