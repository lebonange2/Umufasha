#!/usr/bin/env python3
"""Internal testing script for the Personal Assistant."""
import asyncio
import sys
import json
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models import User, Event, Notification
from app.telephony.mock import MockTwilioClient, MockTwilioWebhookHandler
from app.email.mock import MockSendGridClient
from app.llm.policy import PolicyAgent
from app.llm.client import LLMClient
from app.schemas import PolicyRequest
from app.security.tokens import generate_rsvp_token
from sqlalchemy import select


async def test_mock_twilio():
    """Test mock Twilio functionality."""
    print("🔧 Testing Mock Twilio...")
    
    # Create mock client
    twilio_client = MockTwilioClient()
    webhook_handler = MockTwilioWebhookHandler(twilio_client)
    
    # Test making a call
    call_result = await twilio_client.make_call(
        to="+1234567890",
        from_="+0987654321",
        twiml_url="http://localhost:8000/twilio/voice/answer",
        status_callback="http://localhost:8000/twilio/voice/status"
    )
    
    print(f"✅ Mock call created: {call_result['sid']}")
    
    # Test webhook handling
    twiml = webhook_handler.handle_voice_answer(
        call_sid=call_result['sid'],
        from_number="+1234567890",
        to_number="+0987654321"
    )
    
    print("✅ Voice answer TwiML generated")
    
    # Test DTMF handling
    dtmf_twiml = webhook_handler.handle_voice_gather(
        call_sid=call_result['sid'],
        digits="1",
        from_number="+1234567890"
    )
    
    print("✅ DTMF handling works")
    
    # Check call status
    call_status = twilio_client.get_call_status(call_result['sid'])
    print(f"✅ Call status: {call_status['status']}")
    
    await twilio_client.close()
    print("✅ Mock Twilio test completed\n")


async def test_mock_sendgrid():
    """Test mock SendGrid functionality."""
    print("📧 Testing Mock SendGrid...")
    
    # Create mock client
    sendgrid_client = MockSendGridClient()
    
    # Test sending email
    test_event = {
        "id": "test-event",
        "title": "Test Meeting",
        "start_ts": "2024-01-15T10:00:00Z",
        "end_ts": "2024-01-15T11:00:00Z",
        "location": "Test Room",
        "organizer": "test@example.com"
    }
    
    test_notification = {
        "subject": "Test Reminder",
        "tts_script": "Test script",
        "email_html": "<p>Test email</p>",
        "email_text": "Test email"
    }
    
    rsvp_token = generate_rsvp_token("test-user", "test-event", "test-notification")
    
    result = await sendgrid_client.send_notification_email(
        to_email="test@example.com",
        event=test_event,
        notification=test_notification,
        rsvp_token=rsvp_token
    )
    
    print(f"✅ Mock email sent: {result['message_id']}")
    
    # Check sent emails
    emails = sendgrid_client.get_sent_emails()
    print(f"✅ Total emails sent: {len(emails)}")
    
    await sendgrid_client.close()
    print("✅ Mock SendGrid test completed\n")


async def test_database():
    """Test database functionality."""
    print("🗄️ Testing Database...")
    
    async with AsyncSessionLocal() as db:
        # Check if test user already exists
        existing_user = await db.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = existing_user.scalar_one_or_none()
        
        if user:
            print(f"✅ Test user already exists: {user.name} ({user.email})")
        else:
            # Test user creation
            user = User(
                name="Test User",
                email="test@example.com",
                phone_e164="+1234567890",
                timezone="UTC",
                channel_pref="both"
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            print(f"✅ User created: {user.name} ({user.email})")
        
        # Test event creation
        from datetime import datetime, timedelta
        
        # Check if test event already exists
        existing_event = await db.execute(
            select(Event).where(
                Event.user_id == user.id,
                Event.provider == "test",
                Event.provider_event_id == "test-event-1"
            )
        )
        event = existing_event.scalar_one_or_none()
        
        if event:
            print(f"✅ Test event already exists: {event.title}")
        else:
            event = Event(
                user_id=user.id,
                provider="test",
                provider_event_id="test-event-1",
                title="Test Event",
                start_ts=datetime.utcnow() + timedelta(hours=1),
                end_ts=datetime.utcnow() + timedelta(hours=2),
                status="confirmed"
            )
            
            db.add(event)
            await db.commit()
            await db.refresh(event)
            
            print(f"✅ Event created: {event.title}")
        
        # Test notification creation
        # Check if test notification already exists
        existing_notification = await db.execute(
            select(Notification).where(
                Notification.user_id == user.id,
                Notification.event_id == event.id,
                Notification.channel == "email"
            )
        )
        notification = existing_notification.scalar_one_or_none()
        
        if notification:
            print(f"✅ Test notification already exists: {notification.channel}")
        else:
            notification = Notification(
                user_id=user.id,
                event_id=event.id,
                channel="email",
                plan_time=datetime.utcnow() + timedelta(minutes=30),
                status="planned"
            )
            
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
            
            print(f"✅ Notification created: {notification.channel}")
        
        # Test queries
        users_result = await db.execute(select(User))
        users = users_result.scalars().all()
        print(f"✅ Total users: {len(users)}")
        
        events_result = await db.execute(select(Event))
        events = events_result.scalars().all()
        print(f"✅ Total events: {len(events)}")
        
        notifications_result = await db.execute(select(Notification))
        notifications = notifications_result.scalars().all()
        print(f"✅ Total notifications: {len(notifications)}")
        
        print("✅ Database test completed\n")


async def test_llm_policy():
    """Test LLM policy functionality."""
    print("🤖 Testing LLM Policy...")
    
    # Create mock LLM client
    class MockLLMClient:
        async def complete_json(self, system: str, user: str):
            # Return a mock policy response
            return {
                "notify": True,
                "reasoning": "Test event needs notification",
                "plan": [
                    {
                        "offset_minutes": -30,
                        "channel": "email",
                        "subject": "Test Reminder",
                        "tts_script": "Test call script",
                        "email_html": "<p>Test email</p>",
                        "email_text": "Test email",
                        "urgency": "normal"
                    }
                ]
            }
    
    # Test policy agent
    mock_llm = MockLLMClient()
    policy_agent = PolicyAgent(mock_llm)
    
    # Create test request
    request = PolicyRequest(
        event={
            "id": "test-event",
            "title": "Test Meeting",
            "start_ts": "2024-01-15T10:00:00Z",
            "end_ts": "2024-01-15T11:00:00Z",
            "status": "confirmed"
        },
        user_preferences={
            "channel_pref": "both",
            "quiet_start": "21:00",
            "quiet_end": "07:00",
            "timezone": "UTC"
        },
        history=[],
        timezone="UTC"
    )
    
    # Test policy planning
    result = await policy_agent.plan_notifications(request)
    
    print(f"✅ Policy planning completed")
    print(f"   Notifications planned: {len(result.plan)}")
    print(f"   Reasoning: {result.reasoning}")
    
    print("✅ LLM Policy test completed\n")


async def test_rsvp_tokens():
    """Test RSVP token functionality."""
    print("🔐 Testing RSVP Tokens...")
    
    from app.security.tokens import validate_rsvp_token
    
    # Generate token
    token = generate_rsvp_token("test-user", "test-event", "test-notification")
    print(f"✅ RSVP token generated: {token[:20]}...")
    
    # Validate token
    token_data = validate_rsvp_token(token)
    if token_data:
        print(f"✅ Token validated: {token_data['user_id']}")
    else:
        print("❌ Token validation failed")
    
    # Test invalid token
    invalid_data = validate_rsvp_token("invalid-token")
    if not invalid_data:
        print("✅ Invalid token correctly rejected")
    
    print("✅ RSVP token test completed\n")


async def main():
    """Run all internal tests."""
    print("🧪 Starting Internal Tests for Personal Assistant\n")
    
    try:
        await test_database()
        await test_rsvp_tokens()
        await test_mock_twilio()
        await test_mock_sendgrid()
        await test_llm_policy()
        
        print("🎉 All internal tests completed successfully!")
        print("\n📋 Next steps:")
        print("1. Start the application: ./start.sh")
        print("2. Go to http://localhost:8000/admin")
        print("3. Login with admin:admin123")
        print("4. Create a test user")
        print("5. Use the testing endpoints to simulate calls/emails")
        print("6. Run demo: ./demo.sh")
        print("7. Reset database if needed: ./reset_db.sh")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
