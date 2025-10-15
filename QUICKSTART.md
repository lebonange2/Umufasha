# 🚀 Unified Assistant - Quick Start Guide

Get your AI-Powered Unified Assistant (Voice Brainstorming + Personal Assistant) up and running in minutes!

## ⚡ One-Command Setup

```bash
# Clone and setup everything
git clone <your-repo-url>
cd ASSISTANT
./setup.sh
```

That's it! The setup script will:
- ✅ Install all dependencies
- ✅ Create virtual environment
- ✅ Generate secure encryption keys
- ✅ Initialize database
- ✅ Run internal tests
- ✅ Create helper scripts
- ✅ Set up both brainstorming and personal assistant modes

## 🎯 Quick Start

### 1. Start the Unified Application
```bash
./start_unified.sh
```

**Or start Personal Assistant only:**
```bash
./start.sh
```

### 2. Access the Dashboard
Open your browser and go to:
- **🏠 Unified Dashboard**: http://localhost:8000
- **🧠 Brainstorming Mode**: http://localhost:8000/brainstorm
- **📅 Personal Assistant**: http://localhost:8000/personal
- **⚙️ Admin Panel**: http://localhost:8000/admin
- **📚 API Documentation**: http://localhost:8000/docs
- **🔧 Health Check**: http://localhost:8000/health

**Login Credentials:**
- Username: `admin`
- Password: `admin123`

### 3. Try Both Modes

#### 🧠 Voice-Driven Brainstorming
1. Go to **Brainstorming Mode**: http://localhost:8000/brainstorm
2. Click **Start Recording** to speak your ideas
3. Watch as AI organizes and clusters your thoughts
4. Tag, promote, or delete ideas as needed
5. Export your session when done

#### 📅 Personal Assistant
1. Go to **Admin Panel**: http://localhost:8000/admin
2. Create a user in **Users** section
3. Add events in **Events** section
4. Test mock functionality:
   ```bash
   # Test mock call
   curl -X POST -H "Authorization: Bearer admin:admin123" \
        http://localhost:8000/testing/mock/test-call/USER_ID
   
   # Test mock email
   curl -X POST -H "Authorization: Bearer admin:admin123" \
        http://localhost:8000/testing/mock/test-email/USER_ID
   ```

### 4. Automatic Port Management
The startup scripts automatically:
- ✅ Kill any existing processes on port 8000
- ✅ Stop any running uvicorn processes
- ✅ Start fresh without conflicts
- ✅ Initialize database if needed

## 🧪 Testing Without External APIs

The application runs in **Mock Mode** by default, which means:
- ✅ **No Twilio API needed** - Mock calls simulate real phone calls
- ✅ **No SendGrid API needed** - Mock emails simulate real email sending
- ✅ **No OpenAI API needed** - Mock LLM responses for testing
- ✅ **No Google Calendar needed** - Mock calendar events for testing

### Mock Features Available:
- 📞 **Mock Phone Calls**: Simulate calls with DTMF responses
- 📧 **Mock Emails**: Generate HTML emails with RSVP links
- 🤖 **Mock LLM**: Policy decisions without real API calls
- 📅 **Mock Calendar**: Test calendar integration

## 🔧 Helper Scripts

The setup creates several helper scripts:

### `start_unified.sh` - Start Unified Application
```bash
./start_unified.sh
```
Starts the unified application with both brainstorming and personal assistant modes.

### `start.sh` - Start Personal Assistant Only
```bash
./start.sh
```
Starts only the personal assistant mode.

### `stop.sh` - Stop the Application
```bash
./stop.sh
```
Stops all running instances.

### `test.sh` - Run Tests
```bash
./test.sh
```
Runs internal tests and API health checks.

### `demo.sh` - Interactive Demo
```bash
./demo.sh
```
Shows an interactive demo of all features.

### `reset_db.sh` - Reset Database
```bash
./reset_db.sh
```
Resets the database to a clean state.

## 📊 What You Can Test

### 1. User Management
- Create, edit, delete users
- Set notification preferences
- Configure quiet hours and channels

### 2. Mock Notifications
- **Mock Calls**: Test phone call flows
- **Mock Emails**: Test email generation
- **RSVP Links**: Test email action buttons

### 3. Admin Interface
- Dashboard with system overview
- User management
- Event management
- Notification history
- Audit logs

### 4. API Endpoints
- RESTful API for all operations
- Webhook endpoints for external services
- Testing endpoints for mock functionality

## 🌐 API Endpoints

### Core API
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `GET /api/events/` - List events
- `GET /api/notifications/` - List notifications

### Testing API
- `GET /testing/status` - Check mock mode status
- `POST /testing/mock/test-call/{user_id}` - Test mock call
- `POST /testing/mock/test-email/{user_id}` - Test mock email
- `GET /testing/mock/calls` - View mock calls
- `GET /testing/mock/emails` - View mock emails

### Webhooks
- `POST /twilio/voice/answer` - Twilio call webhook
- `POST /twilio/voice/gather` - Twilio DTMF webhook
- `GET /rsvp/{token}` - Email RSVP handler

## 🔐 Security Features

- **Encrypted OAuth Tokens**: Secure storage of calendar credentials
- **HMAC RSVP Tokens**: Secure email action links
- **Admin Authentication**: Password-based admin access
- **Webhook Validation**: Signed webhook verification

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
├── .env                   # Environment configuration
├── setup.sh              # Setup script
├── start.sh              # Start script
├── stop.sh               # Stop script
└── test.sh               # Test script
```

## 🚀 Production Deployment

When ready for production:

1. **Add Real API Keys** to `.env`:
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
   ```

2. **Use PostgreSQL** instead of SQLite:
   ```bash
   DATABASE_URL=postgresql://user:pass@localhost/assistant
   ```

3. **Set up HTTPS** and proper domain configuration

4. **Configure OAuth** for Google Calendar integration

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

### Dependencies Issues
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements-app.txt
```

## 📚 Additional Resources

- **Testing Guide**: `TESTING_GUIDE.md` - Detailed testing instructions
- **API Documentation**: http://localhost:8000/docs - Interactive API docs
- **Admin Interface**: http://localhost:8000/admin - Web management interface

## 🎉 You're Ready!

Your Personal Assistant is now ready for development and testing. The mock mode allows you to:

- ✅ Test all features without external APIs
- ✅ Develop and iterate quickly
- ✅ Validate the complete workflow
- ✅ Prepare for production deployment

Start with `./start.sh` and begin building your intelligent personal assistant! 🚀