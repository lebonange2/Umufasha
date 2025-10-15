"""Testing and mock endpoints for internal testing."""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_admin_user, get_twilio_client, get_sendgrid_client
from app.models import User, Event
from app.security.tokens import generate_rsvp_token
from sqlalchemy import select

router = APIRouter()


@router.get("/mock/calls")
async def get_mock_calls(
    admin_user: dict = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Get all mock Twilio calls for testing."""
    twilio_client = get_twilio_client()
    
    if hasattr(twilio_client, 'get_all_calls'):
        calls = twilio_client.get_all_calls()
        return {
            "total_calls": len(calls),
            "calls": calls
        }
    else:
        return {
            "error": "Not in mock mode",
            "message": "This endpoint only works with mock Twilio client"
        }


@router.get("/mock/emails")
async def get_mock_emails(
    admin_user: dict = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Get all mock emails for testing."""
    sendgrid_client = get_sendgrid_client()
    
    if hasattr(sendgrid_client, 'get_sent_emails'):
        emails = sendgrid_client.get_sent_emails()
        return {
            "total_emails": len(emails),
            "emails": emails
        }
    else:
        return {
            "error": "Not in mock mode",
            "message": "This endpoint only works with mock SendGrid client"
        }


@router.post("/mock/test-call/{user_id}")
async def test_mock_call(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Test a mock call to a user."""
    # Get user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.phone_e164:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no phone number"
        )
    
    # Get mock Twilio client
    twilio_client = get_twilio_client()
    
    if not hasattr(twilio_client, 'make_call'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not in mock mode"
        )
    
    # Create test event
    test_event = {
        "id": "test-event-call",
        "title": "Test Call Meeting",
        "start_ts": "2024-01-15T10:00:00Z",
        "end_ts": "2024-01-15T11:00:00Z",
        "location": "Test Location",
        "organizer": "test@example.com"
    }
    
    # Make mock call
    result = await twilio_client.make_call(
        to=user.phone_e164,
        from_="+1234567890",
        twiml_url="http://localhost:8000/twilio/voice/answer",
        status_callback="http://localhost:8000/twilio/voice/status"
    )
    
    return {
        "message": "Mock call initiated",
        "call_sid": result.get("sid"),
        "to": user.phone_e164,
        "user": user.name
    }


@router.post("/mock/test-email/{user_id}")
async def test_mock_email(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Test a mock email to a user."""
    # Get user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no email address"
        )
    
    # Get mock SendGrid client
    sendgrid_client = get_sendgrid_client()
    
    if not hasattr(sendgrid_client, 'send_notification_email'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not in mock mode"
        )
    
    # Create test event
    test_event = {
        "id": "test-event-email",
        "title": "Test Email Meeting",
        "start_ts": "2024-01-15T14:00:00Z",
        "end_ts": "2024-01-15T15:00:00Z",
        "location": "Test Conference Room",
        "conf_link": "https://meet.google.com/test",
        "organizer": "test@example.com",
        "attendees": [
            {"email": user.email, "name": user.name, "responseStatus": "accepted"}
        ],
        "description": "This is a test meeting to verify email functionality."
    }
    
    test_notification = {
        "subject": "Test: Meeting Reminder",
        "tts_script": "This is a test call script.",
        "email_html": "<p>This is a test email.</p>",
        "email_text": "This is a test email."
    }
    
    # Generate RSVP token
    rsvp_token = generate_rsvp_token(
        user_id=user_id,
        event_id="test-event-email",
        notification_id="test-notification-email"
    )
    
    # Send mock email
    result = await sendgrid_client.send_notification_email(
        to_email=user.email,
        event=test_event,
        notification=test_notification,
        rsvp_token=rsvp_token
    )
    
    return {
        "message": "Mock email sent",
        "message_id": result.get("message_id"),
        "to": user.email,
        "user": user.name,
        "rsvp_token": rsvp_token
    }


@router.post("/mock/simulate-dtmf/{call_sid}")
async def simulate_dtmf_input(
    call_sid: str,
    digits: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Simulate DTMF input for testing."""
    twilio_client = get_twilio_client()
    
    if not hasattr(twilio_client, 'interactions'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not in mock mode"
        )
    
    # Simulate webhook call
    from app.telephony.mock import MockTwilioWebhookHandler
    webhook_handler = MockTwilioWebhookHandler(twilio_client)
    
    twiml = webhook_handler.handle_voice_gather(
        call_sid=call_sid,
        digits=digits,
        from_number="+1234567890"
    )
    
    return {
        "message": "DTMF input simulated",
        "call_sid": call_sid,
        "digits": digits,
        "twiml": twiml
    }


@router.get("/mock/interactions")
async def get_mock_interactions(
    admin_user: dict = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Get all mock webhook interactions."""
    twilio_client = get_twilio_client()
    
    if hasattr(twilio_client, 'interactions'):
        interactions = twilio_client.interactions
        return {
            "total_interactions": len(interactions),
            "interactions": interactions
        }
    else:
        return {
            "error": "Not in mock mode",
            "message": "This endpoint only works with mock Twilio client"
        }


@router.post("/mock/clear")
async def clear_mock_data(
    admin_user: dict = Depends(get_admin_user)
):
    """Clear all mock data."""
    twilio_client = get_twilio_client()
    sendgrid_client = get_sendgrid_client()
    
    cleared = []
    
    if hasattr(twilio_client, 'calls'):
        twilio_client.calls.clear()
        cleared.append("Twilio calls")
    
    if hasattr(twilio_client, 'interactions'):
        twilio_client.interactions.clear()
        cleared.append("Twilio interactions")
    
    if hasattr(sendgrid_client, 'emails'):
        sendgrid_client.emails.clear()
        cleared.append("SendGrid emails")
    
    return {
        "message": "Mock data cleared",
        "cleared": cleared
    }


@router.get("/status")
async def get_testing_status(
    admin_user: dict = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Get testing/mock status."""
    from app.core.config import settings
    
    return {
        "mock_mode": settings.MOCK_MODE,
        "mock_twilio": settings.MOCK_TWILIO,
        "mock_sendgrid": settings.MOCK_SENDGRID,
        "base_url": settings.BASE_URL,
        "scheduler": settings.SCHEDULER
    }
