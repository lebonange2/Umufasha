"""Telephony webhook routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.telephony.twilio import TwilioClient, TwilioWebhookHandler
from app.core.config import settings

router = APIRouter()


@router.post("/voice/answer")
async def voice_answer(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...)
):
    """Handle Twilio voice answer webhook."""
    try:
        # Verify webhook signature
        twilio_client = TwilioClient()
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        
        # Get form data for signature verification
        form_data = await request.form()
        params = {k: v for k, v in form_data.items()}
        
        if not twilio_client.verify_webhook_signature(signature, url, params):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Handle the voice answer
        webhook_handler = TwilioWebhookHandler(twilio_client)
        twiml = webhook_handler.handle_voice_answer(CallSid, From, To)
        
        await twilio_client.close()
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        # Return error TwiML
        error_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Sorry, there was an error processing your call. Please try again later.</Say>
</Response>"""
        return Response(content=error_twiml, media_type="application/xml")


@router.post("/voice/gather")
async def voice_gather(
    request: Request,
    CallSid: str = Form(...),
    Digits: str = Form(...),
    From: str = Form(...)
):
    """Handle Twilio voice gather webhook (DTMF input)."""
    try:
        # Verify webhook signature
        twilio_client = TwilioClient()
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        
        # Get form data for signature verification
        form_data = await request.form()
        params = {k: v for k, v in form_data.items()}
        
        if not twilio_client.verify_webhook_signature(signature, url, params):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Handle the DTMF input
        webhook_handler = TwilioWebhookHandler(twilio_client)
        twiml = webhook_handler.handle_voice_gather(CallSid, Digits, From)
        
        await twilio_client.close()
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        # Return error TwiML
        error_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Sorry, there was an error processing your input. Goodbye.</Say>
</Response>"""
        return Response(content=error_twiml, media_type="application/xml")


@router.post("/voice/status")
async def voice_status(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    AnsweredBy: str = Form(None),
    Duration: int = Form(None)
):
    """Handle Twilio voice status callback."""
    try:
        # Verify webhook signature
        twilio_client = TwilioClient()
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        
        # Get form data for signature verification
        form_data = await request.form()
        params = {k: v for k, v in form_data.items()}
        
        if not twilio_client.verify_webhook_signature(signature, url, params):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Handle the status callback
        webhook_handler = TwilioWebhookHandler(twilio_client)
        webhook_handler.handle_voice_status(
            CallSid=CallSid,
            call_status=CallStatus,
            answered_by=AnsweredBy,
            duration=Duration
        )
        
        await twilio_client.close()
        
        return {"status": "received"}
        
    except Exception as e:
        # Log error but don't fail the webhook
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("Voice status webhook error", error=str(e))
        
        return {"status": "error", "message": str(e)}
