# Changelog

All notable changes to the Brainstorming Assistant will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-15

### Added
- **Core Features**
  - Voice input with push-to-talk and continuous recording
  - Multiple STT backends: Whisper (local), Vosk, OpenAI Whisper API
  - Voice Activity Detection (VAD) for auto-stop
  - Real-time audio level visualization
  
- **AI Assistant**
  - LLM-powered brainstorming with idea expansion
  - Automatic tagging and categorization
  - Idea clustering by themes
  - Action item generation
  - Session and cluster summarization
  - Semantic duplicate detection
  
- **Organization**
  - Structured data model (ideas, clusters, actions, transcript)
  - Tag-based categorization
  - Key idea promotion
  - Semantic search
  - Idea merging and deduplication
  
- **Storage**
  - Autosave with configurable intervals
  - Version snapshots
  - Multiple export formats: Markdown, DOCX, CSV, JSON
  - Local-first storage
  
- **Terminal UI**
  - Rich TUI built with Textual
  - Split-panel layout (Transcript, Assistant, Organizer)
  - Command palette
  - Keyboard shortcuts
  - Real-time status indicators
  - Help overlay
  
- **LLM Backends**
  - OpenAI API support
  - Generic HTTP client for self-hosted models
  - Pluggable architecture
  
- **Documentation**
  - Comprehensive README
  - Quick start guide
  - Usage examples
  - Contributing guidelines
  - API documentation
  
- **Utilities**
  - Audio device checker
  - Model downloader
  - Run scripts
  - Test suite

### Technical Details
- Python 3.10+ support
- Cross-platform (Linux, macOS, Windows)
- Modular architecture
- Type hints throughout
- Comprehensive logging with key redaction
- Configuration via .env and YAML

## [Unreleased]

### Planned
- Multi-language support
- Voice output (TTS)
- Collaborative sessions
- Mind map visualization
- Mobile companion app
- Plugin system
- Optional cloud sync
- Web interface
- API server mode

---

## Version History

### Version Numbering
- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, backward compatible

### Release Notes Format
- **Added**: New features
- **Changed**: Changes to existing features
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements
