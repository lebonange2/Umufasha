# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Voice-Driven Brainstorming                   │
│                      Terminal Application                        │
└─────────────────────────────────────────────────────────────────┘

                              ┌──────────┐
                              │   User   │
                              └────┬─────┘
                                   │ Voice Input
                                   ▼
                    ┌──────────────────────────┐
                    │   Terminal UI (Textual)  │
                    │  ┌────────────────────┐  │
                    │  │  Transcript Panel  │  │
                    │  ├────────────────────┤  │
                    │  │  Assistant Panel   │  │
                    │  ├────────────────────┤  │
                    │  │  Organizer Panel   │  │
                    │  └────────────────────┘  │
                    └────────┬─────────────────┘
                             │ Commands & Events
                             ▼
                    ┌─────────────────┐
                    │   Controller    │
                    │    (app.py)     │
                    └────┬────────────┘
                         │
          ┌──────────────┼──────────────┬──────────────┐
          ▼              ▼              ▼              ▼
    ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐
    │  Audio  │   │   STT    │   │   LLM   │   │  Brain   │
    │ Capture │   │ Backend  │   │ Backend │   │  Logic   │
    └─────────┘   └──────────┘   └─────────┘   └──────────┘
          │              │              │              │
          └──────────────┴──────────────┴──────────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │    Storage    │
                        │  (Files/JSON) │
                        └───────────────┘
```

## Component Architecture

### 1. Terminal UI Layer

```
┌─────────────────────────────────────────────────────────────┐
│                        TUI (Textual)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────────────────┐   │
│  │  Header          │  │  Status: Recording/Idle      │   │
│  │  Project: Name   │  │  Backends: STT/LLM          │   │
│  └──────────────────┘  └──────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────┬──────────────────────────┐   │
│  │  Left Panel (60%)        │  Right Panel (40%)       │   │
│  ├──────────────────────────┼──────────────────────────┤   │
│  │  ┌────────────────────┐  │  ┌────────────────────┐ │   │
│  │  │ Transcript         │  │  │ Organizer          │ │   │
│  │  │ - User entries     │  │  │ - Key Ideas        │ │   │
│  │  │ - Timestamps       │  │  │ - Recent Ideas     │ │   │
│  │  └────────────────────┘  │  │ - Clusters         │ │   │
│  │  ┌────────────────────┐  │  │ - Action Items     │ │   │
│  │  │ Assistant          │  │  └────────────────────┘ │   │
│  │  │ - Responses        │  │                          │   │
│  │  │ - Suggestions      │  │                          │   │
│  │  └────────────────────┘  │                          │   │
│  └──────────────────────────┴──────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Footer: Shortcuts & Audio Level Meter              │  │
│  │  [Space]=Record [Q]=Quit [:]=Command [?]=Help       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Audio Pipeline

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Micro-   │────▶│  Audio   │────▶│   VAD    │────▶│   STT    │
│  phone   │     │  Buffer  │     │ (Optional)│     │  Engine  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                      │                                   │
                      │ Raw Audio                         │ Text
                      ▼                                   ▼
                 ┌──────────┐                      ┌──────────┐
                 │  Level   │                      │  Trans-  │
                 │  Meter   │                      │  cript   │
                 └──────────┘                      └──────────┘
```

### 3. STT Backend Selection

```
                    ┌─────────────────┐
                    │  STT Interface  │
                    │   (base.py)     │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ Whisper  │      │   Vosk   │      │ Whisper  │
    │  Local   │      │  Local   │      │   API    │
    │ (faster) │      │ (small)  │      │ (cloud)  │
    └──────────┘      └──────────┘      └──────────┘
         │                 │                  │
         └─────────────────┴──────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Transcribed │
                    │    Text     │
                    └─────────────┘
```

### 4. LLM Processing Flow

```
┌──────────────┐
│ User Input   │
│ (Transcript) │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ Build Context       │
│ - Recent ideas      │
│ - Active clusters   │
│ - Action items      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Generate Prompt     │
│ - System prompt     │
│ - User input        │
│ - Context           │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐      ┌──────────┐
│   LLM Backend       │─────▶│ OpenAI   │
│   (base.py)         │      │   API    │
└──────┬──────────────┘      └──────────┘
       │                           │
       │                     ┌──────────┐
       └────────────────────▶│   HTTP   │
                             │  Server  │
                             └──────────┘
       │
       ▼
┌─────────────────────┐
│ Parse Response      │
│ - Extract ideas     │
│ - Extract tags      │
│ - Extract actions   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Update Session      │
│ - Add ideas         │
│ - Add actions       │
│ - Update organizer  │
└─────────────────────┘
```

### 5. Brain Module

```
┌───────────────────────────────────────────────────────────┐
│                      Brain Module                         │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │              Data Model (model.py)              │     │
│  ├─────────────────────────────────────────────────┤     │
│  │  • Idea (text, tags, source, score, timestamp)  │     │
│  │  • Cluster (name, tags, idea_ids)               │     │
│  │  • ActionItem (text, priority, completed)       │     │
│  │  • TranscriptEntry (speaker, text, timestamp)   │     │
│  │  • Summary (text, scope, idea_ids)              │     │
│  │  • BrainstormSession (all above + metadata)     │     │
│  └─────────────────────────────────────────────────┘     │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────┐     │
│  │           Organizer (organizer.py)              │     │
│  ├─────────────────────────────────────────────────┤     │
│  │  • add_idea()        • tag_idea()               │     │
│  │  • add_cluster()     • promote_idea()           │     │
│  │  • add_action()      • delete_idea()            │     │
│  │  • search_ideas()    • merge_ideas()            │     │
│  │  • get_context()     • find_duplicates()        │     │
│  └─────────────────────────────────────────────────┘     │
│                          │                                │
│         ┌────────────────┴────────────────┐              │
│         ▼                                 ▼              │
│  ┌──────────────┐                 ┌──────────────┐      │
│  │ Deduplicator │                 │  Assistant   │      │
│  │ (dedupe.py)  │                 │(assistant.py)│      │
│  ├──────────────┤                 ├──────────────┤      │
│  │ • Semantic   │                 │ • Process    │      │
│  │   similarity │                 │   input      │      │
│  │ • Find dupes │                 │ • Generate   │      │
│  │ • Embeddings │                 │   clusters   │      │
│  └──────────────┘                 │ • Summarize  │      │
│                                   │ • Actions    │      │
│                                   └──────────────┘      │
└───────────────────────────────────────────────────────────┘
```

### 6. Storage Layer

```
┌─────────────────────────────────────────────────────────┐
│                    Storage Layer                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────────────────────────────────────────┐        │
│  │         FileStorage (files.py)             │        │
│  ├────────────────────────────────────────────┤        │
│  │  • save_session()    • load_session()      │        │
│  │  • create_snapshot() • list_snapshots()    │        │
│  └────────────┬───────────────────────────────┘        │
│               │                                         │
│               ▼                                         │
│  ┌────────────────────────────────────────────┐        │
│  │         AutoSaver (autosave.py)            │        │
│  ├────────────────────────────────────────────┤        │
│  │  • Interval-based saving (30s default)     │        │
│  │  • Event-triggered snapshots               │        │
│  │  • Background thread                       │        │
│  └────────────┬───────────────────────────────┘        │
│               │                                         │
│               ▼                                         │
│  ┌────────────────────────────────────────────┐        │
│  │        Exporters (exporters.py)            │        │
│  ├────────────────────────────────────────────┤        │
│  │  • MarkdownExporter  → notes.md            │        │
│  │  • DOCXExporter      → notes.docx          │        │
│  │  • CSVExporter       → ideas.csv           │        │
│  │  • JSONExporter      → ledger.json         │        │
│  └────────────────────────────────────────────┘        │
│                                                         │
└─────────────────────────────────────────────────────────┘

File Structure:
brainstorm/<project>/
├── ledger.json          # Full session data
├── notes.md             # Primary document
├── ideas.csv            # Ideas export
├── notes.docx           # Word document
├── brainstorm.log       # Application logs
└── versions/
    └── snapshot_*.json  # Version history
```

### 7. Configuration System

```
┌─────────────────────────────────────────────────────────┐
│                  Configuration                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │    .env      │         │ config.yaml  │            │
│  ├──────────────┤         ├──────────────┤            │
│  │ • API keys   │         │ • Audio      │            │
│  │ • Backends   │         │ • STT        │            │
│  │ • Models     │         │ • LLM        │            │
│  │ • Intervals  │         │ • Storage    │            │
│  └──────┬───────┘         │ • UI         │            │
│         │                 └──────┬───────┘            │
│         └────────┬───────────────┘                     │
│                  ▼                                     │
│         ┌─────────────────┐                           │
│         │  Config Object  │                           │
│         │   (config.py)   │                           │
│         ├─────────────────┤                           │
│         │ • Load env vars │                           │
│         │ • Load YAML     │                           │
│         │ • Merge configs │                           │
│         │ • Provide API   │                           │
│         └─────────────────┘                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 8. Event Flow

```
User Action                Controller              Components
────────────────────────────────────────────────────────────

Press Space
    │
    ├──────────────────▶ start_recording()
    │                           │
    │                           ├──────────▶ mic.start()
    │                           │
    │                           └──────────▶ tui.set_recording(true)
    │
Release Space
    │
    ├──────────────────▶ stop_recording()
    │                           │
    │                           ├──────────▶ mic.stop()
    │                           │              │
    │                           │              ▼
    │                           │         audio_data
    │                           │              │
    │                           ├──────────▶ stt.transcribe()
    │                           │              │
    │                           │              ▼
    │                           │            text
    │                           │              │
    │                           ├──────────▶ organizer.add_idea()
    │                           │
    │                           ├──────────▶ assistant.process()
    │                           │              │
    │                           │              ▼
    │                           │          response
    │                           │              │
    │                           ├──────────▶ organizer.add_ideas()
    │                           │
    │                           ├──────────▶ tui.update_panels()
    │                           │
    │                           └──────────▶ autosaver.trigger()

Type :command
    │
    ├──────────────────▶ handle_command()
    │                           │
    │                           ├──────────▶ parse_command()
    │                           │
    │                           ├──────────▶ execute_command()
    │                           │
    │                           └──────────▶ tui.show_result()
```

### 9. Data Flow

```
┌──────────┐
│   User   │
│  Voice   │
└────┬─────┘
     │
     ▼
┌─────────────┐
│ Audio Data  │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ Transcript  │
│   (Text)    │
└─────┬───────┘
      │
      ├─────────────────────────────┐
      │                             │
      ▼                             ▼
┌──────────┐                  ┌──────────┐
│  Idea    │                  │   LLM    │
│ (User)   │                  │ Process  │
└────┬─────┘                  └────┬─────┘
     │                             │
     │                             ▼
     │                       ┌──────────┐
     │                       │  Ideas   │
     │                       │(Assistant)│
     │                       └────┬─────┘
     │                            │
     └────────────┬───────────────┘
                  │
                  ▼
           ┌──────────────┐
           │  Organizer   │
           │  - Tag       │
           │  - Cluster   │
           │  - Dedupe    │
           └──────┬───────┘
                  │
                  ▼
           ┌──────────────┐
           │   Session    │
           │   State      │
           └──────┬───────┘
                  │
                  ├──────────┬──────────┐
                  ▼          ▼          ▼
              ┌──────┐  ┌──────┐  ┌──────┐
              │  TUI │  │ Auto │  │Export│
              │Update│  │ Save │  │      │
              └──────┘  └──────┘  └──────┘
```

## Design Patterns

### 1. Strategy Pattern (Backends)

```python
# STT Backend Strategy
class STTBackend(ABC):
    @abstractmethod
    def transcribe(audio) -> str
    
class WhisperLocalSTT(STTBackend):
    def transcribe(audio) -> str
        # Whisper implementation
        
class VoskSTT(STTBackend):
    def transcribe(audio) -> str
        # Vosk implementation
```

### 2. Observer Pattern (UI Updates)

```python
# Controller notifies TUI of changes
controller.on_idea_added = lambda: tui.update_organizer()
controller.on_transcript = lambda text: tui.add_transcript(text)
```

### 3. Factory Pattern (Model Creation)

```python
# Factory methods for creating entities
idea = Idea.create(text="...", source=IdeaSource.USER)
action = ActionItem.create(text="...", priority=Priority.HIGH)
```

### 4. Singleton Pattern (Configuration)

```python
# Single config instance
config = Config(project_name="my-project")
# Shared across all components
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                     │
│                   Python 3.10+                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  UI Layer          │  Processing      │  Storage       │
│  ─────────────────────────────────────────────────────  │
│  • Textual         │  • NumPy         │  • JSON        │
│  • Rich            │  • SciPy         │  • YAML        │
│                    │  • Transformers  │  • python-docx │
│                    │                  │                 │
│  Audio Layer       │  AI Layer        │  Utils         │
│  ─────────────────────────────────────────────────────  │
│  • sounddevice     │  • OpenAI API    │  • dotenv      │
│  • webrtcvad       │  • faster-whisper│  • logging     │
│                    │  • vosk          │  • argparse    │
│                    │  • httpx         │                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User's Machine                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │         Terminal Application                  │     │
│  │         (Python Process)                      │     │
│  └───────────────┬───────────────────────────────┘     │
│                  │                                      │
│  ┌───────────────┴───────────────────────────────┐     │
│  │         Local Storage                         │     │
│  │         brainstorm/<project>/                 │     │
│  │         - ledger.json                         │     │
│  │         - notes.md                            │     │
│  │         - versions/                           │     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  OpenAI API      │    │  Local LLM       │
│  (Optional)      │    │  (Optional)      │
│  - Whisper API   │    │  - Ollama        │
│  - GPT-4         │    │  - LM Studio     │
└──────────────────┘    └──────────────────┘
```

---

**Architecture Status**: ✅ Complete and Production Ready  
**Last Updated**: 2025-01-15
