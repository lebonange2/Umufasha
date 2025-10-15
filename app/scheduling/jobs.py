"""Notification job execution."""
from typing import Dict, Any
import structlog

from app.telephony.twilio import TwilioClient, TwilioWebhookHandler
from app.email.sendgrid import SendGridClient
from app.security.tokens import generate_rsvp_token

logger = structlog.get_logger(__name__)


async def execute_notification_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a notification job.
    
    Args:
        job_data: Job data containing notification details
        
    Returns:
        Execution result
    """
    try:
        notification_id = job_data.get("notification_id")
        user_id = job_data.get("user_id")
        event_id = job_data.get("event_id")
        channel = job_data.get("channel")
        event = job_data.get("event")
        user = job_data.get("user")
        notification = job_data.get("notification")
        
        logger.info(
            "Executing notification job",
            notification_id=notification_id,
            channel=channel,
            user_id=user_id,
            event_id=event_id
        )
        
        result = {"status": "failed", "error": "Unknown channel"}
        
        if channel == "call":
            result = await _execute_call_notification(job_data)
        elif channel == "email":
            result = await _execute_email_notification(job_data)
        elif channel == "both":
            # Execute both call and email
            call_result = await _execute_call_notification(job_data)
            email_result = await _execute_email_notification(job_data)
            result = {
                "status": "completed",
                "call": call_result,
                "email": email_result
            }
        
        logger.info(
            "Notification job completed",
            notification_id=notification_id,
            result=result
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Notification job failed",
            notification_id=job_data.get("notification_id"),
            error=str(e)
        )
        return {"status": "failed", "error": str(e)}


async def _execute_call_notification(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a call notification."""
    try:
        user = job_data.get("user")
        event = job_data.get("event")
        notification = job_data.get("notification")
        
        if not user or not user.get("phone_e164"):
            return {"status": "failed", "error": "No phone number available"}
        
        # Initialize Twilio client
        twilio_client = TwilioClient()
        webhook_handler = TwilioWebhookHandler(twilio_client)
        
        # Generate TwiML URL
        from app.core.config import settings
        twiml_url = f"{settings.BASE_URL}/twilio/voice/answer"
        status_callback = f"{settings.BASE_URL}/twilio/voice/status"
        
        # Make the call
        call_result = await twilio_client.make_call(
            to=user["phone_e164"],
            from_=settings.TWILIO_CALLER_ID,
            twiml_url=twiml_url,
            status_callback=status_callback
        )
        
        await twilio_client.close()
        
        return {
            "status": "sent",
            "call_sid": call_result.get("sid"),
            "provider": "twilio"
        }
        
    except Exception as e:
        logger.error("Call notification failed", error=str(e))
        return {"status": "failed", "error": str(e)}


async def _execute_email_notification(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an email notification."""
    try:
        user = job_data.get("user")
        event = job_data.get("event")
        notification = job_data.get("notification")
        notification_id = job_data.get("notification_id")
        
        if not user or not user.get("email"):
            return {"status": "failed", "error": "No email address available"}
        
        # Generate RSVP token
        rsvp_token = generate_rsvp_token(
            user_id=user["id"],
            event_id=event["id"],
            notification_id=notification_id
        )
        
        # Initialize SendGrid client
        sendgrid_client = SendGridClient()
        
        # Send email
        email_result = await sendgrid_client.send_notification_email(
            to_email=user["email"],
            event=event,
            notification=notification,
            rsvp_token=rsvp_token
        )
        
        await sendgrid_client.close()
        
        return email_result
        
    except Exception as e:
        logger.error("Email notification failed", error=str(e))
        return {"status": "failed", "error": str(e)}
