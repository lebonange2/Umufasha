# 🤖 Unified Assistant

A comprehensive AI-powered workspace combining **Voice-Driven Brainstorming** and **LLM-Powered Personal Assistant** in a single, unified application.

## ✨ What's Included

### 🧠 Voice-Driven Brainstorming Assistant
- **Voice-to-Text**: Real-time speech transcription using Whisper
- **AI Organization**: Intelligent idea clustering and organization
- **Smart Tagging**: Automatic tagging and categorization
- **Action Items**: Generate actionable tasks from ideas
- **Export Options**: Multiple format exports (Markdown, JSON, etc.)

### 📅 LLM-Powered Personal Assistant
- **Calendar Integration**: Google Calendar sync with OAuth
- **Smart Notifications**: LLM-powered decision making for reminders
- **Phone Calls**: Twilio-powered voice calls with TTS and DTMF
- **Email Notifications**: Rich HTML emails with ICS attachments
- **RSVP Handling**: Secure email action links
- **Mock Mode**: Test everything without external APIs

## 🚀 Quick Start

### One-Command Setup
```bash
./setup.sh
```

### Start Unified Application
```bash
./start_unified.sh
```

### Access the Dashboard
- **Unified Dashboard**: http://localhost:8000
- **Brainstorming Mode**: http://localhost:8000/brainstorm
- **Personal Assistant**: http://localhost:8000/personal
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/docs

## 🎯 Key Features

### Unified Interface
- **Single Dashboard**: Access both modes from one interface
- **Seamless Switching**: Switch between brainstorming and personal assistant
- **Shared Resources**: Common LLM and STT backends
- **Unified Authentication**: Single admin login for both modes

### Voice-Driven Brainstorming
- **Real-time Transcription**: Speak your ideas and see them transcribed
- **AI-Powered Organization**: Automatic clustering and tagging
- **Interactive Management**: Tag, promote, and delete ideas
- **Export Capabilities**: Export sessions in multiple formats
- **Action Item Generation**: Convert ideas into actionable tasks

### Personal Assistant
- **Calendar Sync**: Connect Google Calendar for appointment management
- **Smart Reminders**: LLM decides when and how to remind you
- **Multi-Channel Notifications**: Phone calls and email reminders
- **RSVP Handling**: Secure email action links for confirmations
- **Mock Testing**: Test all features without external APIs

## 🔧 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Assistant                        │
├─────────────────────────────────────────────────────────────┤
│  🧠 Brainstorming Mode    │    📅 Personal Assistant Mode   │
│  • Voice Transcription    │    • Calendar Integration       │
│  • Idea Organization      │    • Smart Notifications        │
│  • AI Clustering          │    • Phone & Email              │
│  • Export Functions       │    • RSVP Handling              │
├─────────────────────────────────────────────────────────────┤
│                    Shared Services                          │
│  • LLM Backend (OpenAI)   • STT Backend (Whisper)          │
│  • Database (SQLite)      • Authentication                  │
│  • File Storage           • Configuration Management        │
└─────────────────────────────────────────────────────────────┘
```

## 📊 System Components

### Backend Services
- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: Database ORM with async support
- **APScheduler**: Background task scheduling
- **Redis**: Caching and session storage (optional)

### AI Services
- **OpenAI GPT-4**: LLM for brainstorming and policy decisions
- **Whisper**: Speech-to-text transcription
- **Custom Prompts**: Specialized prompts for different tasks

### External Integrations
- **Google Calendar API**: Calendar synchronization
- **Twilio**: Phone call notifications
- **SendGrid**: Email notifications
- **Mock Services**: Testing without external APIs

## 🧪 Testing & Development

### Mock Mode
The application runs in **Mock Mode** by default, allowing you to:
- ✅ Test all features without external APIs
- ✅ Simulate phone calls and emails
- ✅ Develop and iterate quickly
- ✅ Validate complete workflows

### Testing Scripts
```bash
# Run internal tests
./test.sh

# Run demo
./demo.sh

# Reset database
./reset_db.sh
```

### Development Mode
```bash
# Start with auto-reload
./start_unified.sh

# Or start personal assistant only
./start.sh
```

## 📚 API Endpoints

### Unified Endpoints
- `GET /` - Unified dashboard
- `GET /brainstorm` - Brainstorming interface
- `GET /personal` - Personal assistant interface
- `GET /health` - System health check

### Brainstorming API
- `POST /api/brainstorm/session/create` - Create session
- `GET /api/brainstorm/session/data` - Get session data
- `POST /api/brainstorm/transcribe` - Transcribe audio
- `POST /api/brainstorm/idea/tag` - Tag idea
- `POST /api/brainstorm/idea/promote` - Promote idea
- `POST /api/brainstorm/idea/delete` - Delete idea

### Personal Assistant API
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `GET /api/events/` - List events
- `GET /api/notifications/` - List notifications
- `POST /testing/mock/test-call/{user_id}` - Test mock call
- `POST /testing/mock/test-email/{user_id}` - Test mock email

## 🔐 Security Features

- **Encrypted Tokens**: OAuth and RSVP tokens encrypted at rest
- **HMAC Signatures**: Secure email action links
- **Admin Authentication**: Password-based admin access
- **Webhook Validation**: Signed webhook verification
- **Audit Logging**: Complete system activity trail

## 🚀 Production Deployment

### Environment Configuration
```bash
# Real API keys
OPENAI_API_KEY=your_real_openai_key
TWILIO_ACCOUNT_SID=your_real_twilio_sid
TWILIO_AUTH_TOKEN=your_real_twilio_token
SENDGRID_API_KEY=your_real_sendgrid_key

# Disable mock mode
MOCK_MODE=false
MOCK_TWILIO=false
MOCK_SENDGRID=false

# Use PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/assistant
```

### Deployment Steps
1. **Add Real API Keys**: Configure external service credentials
2. **Database Setup**: Use PostgreSQL for production
3. **HTTPS Configuration**: Set up SSL certificates
4. **Domain Configuration**: Configure proper domains
5. **OAuth Setup**: Configure Google Calendar OAuth

## 📁 Project Structure

```
ASSISTANT/
├── unified_app.py              # Main unified application
├── app/                        # Personal Assistant components
│   ├── main.py                # FastAPI application
│   ├── models.py              # Database models
│   ├── routes/                # API routes
│   ├── llm/                   # LLM integration
│   ├── calendar/              # Calendar integration
│   ├── telephony/             # Phone call handling
│   ├── email/                 # Email handling
│   └── templates/             # Web templates
├── brain/                     # Brainstorming components
│   ├── model.py              # Session models
│   ├── organizer.py          # Idea organization
│   └── assistant.py          # AI assistant
├── audio/                     # Audio processing
├── stt/                       # Speech-to-text
├── llm/                       # LLM backends
├── storage/                   # File storage
├── web/                       # Original web interface
├── scripts/                   # Utility scripts
├── tests/                     # Test files
├── start_unified.sh           # Unified startup script
├── start.sh                   # Personal assistant only
└── setup.sh                   # Setup script
```

## 🎉 Getting Started

1. **Setup**: `./setup.sh`
2. **Start**: `./start_unified.sh`
3. **Access**: http://localhost:8000
4. **Explore**: Try both brainstorming and personal assistant modes
5. **Test**: Use the testing endpoints to validate functionality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Ready to experience the power of unified AI assistance?** Start with `./setup.sh` and begin your journey with both voice-driven brainstorming and intelligent personal assistance! 🚀
