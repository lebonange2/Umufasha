# 🧪 Internal Testing Guide

This guide shows you how to test the Personal Assistant application internally without needing real Twilio or SendGrid API keys.

## 🚀 Quick Start for Testing

### 1. Setup Testing Environment

```bash
# Copy testing configuration
cp env.testing .env

# Start services
docker compose up -d

# Wait for services to start
sleep 10

# Run internal tests
python scripts/test_internal.py
```

### 2. Access the Application

- **Admin Interface**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/docs
- **Testing Endpoints**: http://localhost:8000/testing

**Login Credentials:**
- Username: `admin`
- Password: `admin123`

## 🔧 Mock Mode Features

### Mock Twilio Client
- **Simulates phone calls** without real API calls
- **Tracks call status** and webhook interactions
- **Generates realistic TwiML** responses
- **Handles DTMF input** for testing user responses

### Mock SendGrid Client
- **Simulates email sending** without real API calls
- **Stores sent emails** for inspection
- **Generates HTML and text** email content
- **Creates ICS attachments** for calendar events

## 📋 Testing Workflows

### 1. Basic Application Test

```bash
# Start the application
./run_assistant.sh

# Check health
curl http://localhost:8000/health

# Check mock status
curl -H "Authorization: Bearer admin:admin123" \
     http://localhost:8000/testing/status
```

### 2. User Management Test

1. Go to http://localhost:8000/admin/users
2. Click "Add User"
3. Fill in test user details:
   - Name: Test User
   - Email: test@example.com
   - Phone: +1234567890
   - Channel Preference: Both
4. Save the user

### 3. Mock Call Testing

```bash
# Test a mock call (replace USER_ID with actual user ID)
curl -X POST \
     -H "Authorization: Bearer admin:admin123" \
     http://localhost:8000/testing/mock/test-call/USER_ID

# View mock calls
curl -H "Authorization: Bearer admin:admin123" \
     http://localhost:8000/testing/mock/calls

# Simulate DTMF input
curl -X POST \
     -H "Authorization: Bearer admin:admin123" \
     -H "Content-Type: application/json" \
     -d '{"digits": "1"}' \
     http://localhost:8000/testing/mock/simulate-dtmf/CALL_SID
```

### 4. Mock Email Testing

```bash
# Test a mock email (replace USER_ID with actual user ID)
curl -X POST \
     -H "Authorization: Bearer admin:admin123" \
     http://localhost:8000/testing/mock/test-email/USER_ID

# View mock emails
curl -H "Authorization: Bearer admin:admin123" \
     http://localhost:8000/testing/mock/emails
```

### 5. Webhook Testing

```bash
# Test Twilio webhook endpoints
curl -X POST \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "CallSid=CA123&From=%2B1234567890&To=%2B0987654321&CallStatus=ringing" \
     http://localhost:8000/twilio/voice/answer

# Test DTMF webhook
curl -X POST \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "CallSid=CA123&Digits=1&From=%2B1234567890" \
     http://localhost:8000/twilio/voice/gather
```

## 🎯 Testing Scenarios

### Scenario 1: Complete User Journey

1. **Create User**: Add a test user with phone and email
2. **Create Event**: Add a test event for the user
3. **Plan Notifications**: Use the LLM policy to plan notifications
4. **Test Call**: Send a mock call and simulate DTMF responses
5. **Test Email**: Send a mock email and test RSVP links
6. **Verify Results**: Check mock data and audit logs

### Scenario 2: Policy Testing

1. **Create Different Event Types**:
   - Urgent meeting (1 hour away)
   - Regular meeting (1 day away)
   - Weekend meeting
   - Meeting during quiet hours

2. **Test Policy Decisions**:
   - Check if LLM makes appropriate channel choices
   - Verify timing offsets are reasonable
   - Confirm quiet hours are respected

### Scenario 3: Error Handling

1. **Test Invalid Inputs**:
   - Invalid phone numbers
   - Invalid email addresses
   - Missing user data

2. **Test Edge Cases**:
   - Past events
   - Very short notice meetings
   - Multiple notifications for same event

## 🔍 Monitoring and Debugging

### View Mock Data

```bash
# View all mock calls
curl -H "Authorization: Bearer admin:admin123" \
     http://localhost:8000/testing/mock/calls

# View all mock emails
curl -H "Authorization: Bearer admin:admin123" \
     http://localhost:8000/testing/mock/emails

# View webhook interactions
curl -H "Authorization: Bearer admin:admin123" \
     http://localhost:8000/testing/mock/interactions
```

### Clear Mock Data

```bash
# Clear all mock data
curl -X POST \
     -H "Authorization: Bearer admin:admin123" \
     http://localhost:8000/testing/mock/clear
```

### View Logs

```bash
# View application logs
docker compose logs -f web

# View worker logs
docker compose logs -f worker

# View database logs
docker compose logs -f db
```

## 🧪 Automated Testing

### Run Internal Tests

```bash
# Run comprehensive internal tests
python scripts/test_internal.py

# Run specific test categories
pytest tests/test_policy_plan.py
pytest tests/test_twilio_webhooks.py
```

### Test Coverage

The internal tests cover:
- ✅ Database operations (CRUD)
- ✅ RSVP token generation/validation
- ✅ Mock Twilio call simulation
- ✅ Mock SendGrid email simulation
- ✅ LLM policy decision making
- ✅ Webhook handling
- ✅ Security features

## 🚨 Troubleshooting

### Common Issues

1. **Services not starting**:
   ```bash
   docker compose down
   docker compose up --build
   ```

2. **Database connection issues**:
   ```bash
   docker compose logs db
   docker compose restart db
   ```

3. **Mock mode not working**:
   - Check `.env` file has `MOCK_MODE=true`
   - Restart the application
   - Check `/testing/status` endpoint

4. **Authentication issues**:
   - Use `admin:admin123` for basic auth
   - Check Authorization header format: `Bearer admin:admin123`

### Debug Mode

Enable debug logging by setting in `.env`:
```bash
LOG_LEVEL=DEBUG
```

## 📊 Expected Results

### Mock Call Flow
1. Call initiated → Status: "initiated"
2. Call ringing → Status: "ringing"
3. Call answered → Status: "in-progress"
4. Call completed → Status: "completed"
5. Status callback sent to webhook URL

### Mock Email Flow
1. Email composed with HTML/text content
2. ICS attachment generated
3. RSVP links created with secure tokens
4. Email stored in mock client for inspection

### Policy Decisions
- **Urgent meetings** (< 1 hour): Call + Email
- **Regular meetings** (1+ hours): Email only
- **Quiet hours**: Email only (unless urgent)
- **Weekend meetings**: Based on user preference

## 🎉 Success Criteria

Your internal testing is successful when:
- ✅ All mock services work without external APIs
- ✅ User management functions properly
- ✅ Mock calls simulate real Twilio behavior
- ✅ Mock emails generate proper content
- ✅ RSVP tokens work for email actions
- ✅ LLM policy makes reasonable decisions
- ✅ Audit logs track all activities
- ✅ Admin UI is functional and responsive

## 🔄 Next Steps

After successful internal testing:
1. **Add real API keys** to `.env` for production testing
2. **Test with real phone numbers** (use Twilio trial account)
3. **Test with real email addresses** (use SendGrid trial account)
4. **Deploy to staging environment**
5. **Run end-to-end tests** with real external services

This internal testing approach allows you to develop and test the entire application without any external dependencies or costs! 🚀
