"""Email routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Event, Notification
from app.email.sendgrid import SendGridClient
from app.security.tokens import generate_rsvp_token
from app.deps import get_admin_user

router = APIRouter()


@router.post("/test/{user_id}")
async def send_test_email(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Send a test email to a user."""
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
    
    try:
        # Create test event data
        test_event = {
            "id": "test-event-id",
            "title": "Test Meeting",
            "start_ts": "2024-01-15T10:00:00Z",
            "end_ts": "2024-01-15T11:00:00Z",
            "location": "Conference Room A",
            "conf_link": "https://meet.google.com/test",
            "organizer": "test@example.com",
            "attendees": [],
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
            event_id="test-event-id",
            notification_id="test-notification-id"
        )
        
        # Send email
        sendgrid_client = SendGridClient()
        result = await sendgrid_client.send_notification_email(
            to_email=user.email,
            event=test_event,
            notification=test_notification,
            rsvp_token=rsvp_token
        )
        
        await sendgrid_client.close()
        
        return {
            "message": "Test email sent successfully",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send test email: {str(e)}"
        )
