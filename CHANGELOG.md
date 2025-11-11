# Changelog

All notable changes to the AI Assistant project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-11-10

### Added
- **Writer Assistant Enhancements**
  - Document context feature: Upload PDF, DOCX, TXT files for AI reference
  - Provider selection UI: Switch between OpenAI (ChatGPT) and Anthropic (Claude) in real-time
  - Runtime provider switching without server restart
  - Document management: Upload, select, delete documents
  - Text context input: Add custom text as context
  - Settings persistence: Provider/model selection saved to localStorage

- **LLM Provider Support**
  - Anthropic Claude API integration
  - Runtime provider selection (OpenAI/Claude)
  - Model selection per provider (GPT-4o, Claude 3.5 Sonnet, etc.)
  - Environment variable-based API key configuration
  - Improved error handling for missing/invalid API keys

- **Document Processing**
  - PDF text extraction (PyPDF2)
  - DOCX text extraction (python-docx)
  - TXT file support
  - Automatic text extraction on upload
  - Document preview and metadata
  - File size limit: 50MB per file

- **Unified Homepage**
  - Central navigation hub
  - Links to all features (Writer, Brainstorming, Admin, etc.)
  - System status display
  - Modern, responsive design

- **Documentation**
  - Comprehensive documentation index
  - Provider selection guide
  - Document context guide
  - API key setup guide
  - Quick fix guides for common issues

### Changed
- **LLM Client**
  - Support for both OpenAI and Claude API formats
  - Automatic format detection based on provider
  - Improved streaming support for both providers
  - Better error messages for API key issues

- **Writer API**
  - Accepts `provider` and `model` parameters in requests
  - Dynamic LLM client creation per request
  - Enhanced context building with document support

- **Configuration**
  - Environment variable priority over .env file
  - Support for both OpenAI and Anthropic API keys
  - Provider selection via environment or UI

### Fixed
- API key validation before making requests
- Error handling for missing API keys
- Frontend error display for API issues
- Duplicate catch blocks in autocomplete handler
- TypeScript compilation errors

### Security
- API keys never exposed to frontend
- Server-side API key validation
- Environment variable-based configuration (recommended)

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
