# 🤖 LLM-Powered Personal Assistant

An intelligent personal assistant that calls or emails you about appointments, powered by LLM decision-making and integrated with your calendars.

## ✨ Features

- 📅 **Calendar Integration**: Sync with Google Calendar (OAuth)
- 🤖 **LLM-Powered Policy**: Smart decisions on when/how to notify you
- 📞 **Phone Calls**: Twilio-powered voice calls with TTS and DTMF
- 📧 **Email Notifications**: Rich HTML emails with ICS attachments
- 🔄 **Two-Way Updates**: Confirm/reschedule/cancel via calls or email
- 🛡️ **Security**: Encrypted tokens, HMAC signatures, audit trails
- 🎛️ **Admin Interface**: Web-based management dashboard
- 🧪 **Mock Mode**: Test everything without external APIs

## 🚀 Quick Start

### One-Command Setup
```bash
./setup.sh
```

### Start the Application
```bash
./start.sh
```

### Access Admin Interface
- **URL**: http://localhost:8000/admin
- **Login**: admin / admin123

## 🧪 Testing Without External APIs

The application runs in **Mock Mode** by default:
- ✅ No Twilio API needed - Mock calls simulate real phone calls
- ✅ No SendGrid API needed - Mock emails simulate real email sending  
- ✅ No OpenAI API needed - Mock LLM responses for testing
- ✅ No Google Calendar needed - Mock calendar events for testing

## 📚 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in minutes
- **[Testing Guide](TESTING_GUIDE.md)** - Comprehensive testing instructions
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs

## 🔧 Helper Scripts

| Script | Purpose |
|--------|---------|
| `./setup.sh` | Complete setup and installation |
| `./start.sh` | Start the application |
| `./stop.sh` | Stop the application |
| `./test.sh` | Run tests and health checks |
| `./demo.sh` | Interactive demo of all features |
| `./reset_db.sh` | Reset database to clean state |

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin UI      │    │   FastAPI       │    │   Database      │
│   (Jinja2)      │◄──►│   Backend       │◄──►│   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Mock Services │
                       │   • Twilio      │
                       │   • SendGrid    │
                       │   • LLM         │
                       └─────────────────┘
```

## 🎯 Core Workflows

### 1. Calendar Sync
- OAuth integration with Google Calendar
- Delta sync for efficient updates
- Event normalization and storage

### 2. Notification Planning
- LLM analyzes events and user preferences
- Decides notification channel (call/email/both)
- Determines optimal timing and content

### 3. Notification Delivery
- **Calls**: Twilio TTS with DTMF menu (1=Confirm, 2=Reschedule, 3=Cancel)
- **Emails**: HTML emails with ICS attachments and RSVP links

### 4. User Response Handling
- DTMF input processing for calls
- RSVP link handling for emails
- Calendar updates and organizer notifications

## 🔐 Security Features

- **OAuth Token Encryption**: AES-GCM encryption for calendar credentials
- **HMAC RSVP Tokens**: Secure email action links with expiration
- **Webhook Validation**: Signed webhook verification for Twilio
- **Admin Authentication**: Password-based admin access
- **Audit Logging**: Complete trail of all system actions

## 📊 API Endpoints

### Core API
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `GET /api/events/` - List events
- `GET /api/notifications/` - List notifications

### Testing API
- `GET /testing/status` - Check mock mode status
- `POST /testing/mock/test-call/{user_id}` - Test mock call
- `POST /testing/mock/test-email/{user_id}` - Test mock email

### Webhooks
- `POST /twilio/voice/answer` - Twilio call webhook
- `POST /twilio/voice/gather` - Twilio DTMF webhook
- `GET /rsvp/{token}` - Email RSVP handler

## 🛠️ Technology Stack

- **Backend**: Python 3.11 + FastAPI
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Scheduler**: APScheduler
- **Telephony**: Twilio Programmable Voice
- **Email**: SendGrid
- **Calendar**: Google Calendar API
- **LLM**: OpenAI GPT-4 (pluggable)
- **Frontend**: Jinja2 templates
- **Security**: Cryptography, HMAC, OAuth 2.0

## 🧪 Testing

### Internal Tests
```bash
./test.sh
```

### Mock Functionality
- **Mock Twilio**: Simulates phone calls with realistic TwiML
- **Mock SendGrid**: Generates HTML emails with ICS attachments
- **Mock LLM**: Provides policy decisions without API calls
- **Mock Calendar**: Test calendar integration

### Test Coverage
- ✅ Database operations (CRUD)
- ✅ RSVP token generation/validation
- ✅ Mock service simulation
- ✅ Webhook handling
- ✅ Security features
- ✅ Admin interface

## 🚀 Production Deployment

### 1. Add Real API Keys
```bash
# Edit .env file
OPENAI_API_KEY=your_real_openai_key
TWILIO_ACCOUNT_SID=your_real_twilio_sid
TWILIO_AUTH_TOKEN=your_real_twilio_token
SENDGRID_API_KEY=your_real_sendgrid_key

# Disable mock mode
MOCK_MODE=false
MOCK_TWILIO=false
MOCK_SENDGRID=false
```

### 2. Use PostgreSQL
```bash
DATABASE_URL=postgresql://user:pass@localhost/assistant
```

### 3. Set up HTTPS and proper domain configuration

### 4. Configure OAuth for Google Calendar integration

## 📁 Project Structure

```
ASSISTANT/
├── app/                    # Main application code
│   ├── main.py            # FastAPI application
│   ├── models.py          # Database models
│   ├── schemas.py         # Pydantic schemas
│   ├── routes/            # API routes
│   ├── llm/               # LLM integration
│   ├── calendar/          # Calendar integration
│   ├── telephony/         # Phone call handling
│   ├── email/             # Email handling
│   └── templates/         # Admin UI templates
├── scripts/               # Utility scripts
├── tests/                 # Test files
├── prompts/               # LLM prompts
├── setup.sh              # Setup script
├── start.sh              # Start script
├── stop.sh               # Stop script
├── test.sh               # Test script
├── QUICKSTART.md         # Quick start guide
├── TESTING_GUIDE.md      # Testing guide
└── README.md             # This file
```

## 🆘 Troubleshooting

### Application Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing processes
./stop.sh

# Start fresh
./start.sh
```

### Database Issues
```bash
# Reinitialize database
rm assistant.db
python3 scripts/init_db.py
```

### Permission Issues
```bash
# Make scripts executable
chmod +x *.sh
```

## 🎉 Getting Started

1. **Setup**: `./setup.sh`
2. **Start**: `./start.sh`
3. **Access**: http://localhost:8000/admin
4. **Test**: `./test.sh`
5. **Stop**: `./stop.sh`

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**Ready to build your intelligent personal assistant?** Start with `./setup.sh` and begin testing! 🚀