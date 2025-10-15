"""Twilio voice integration."""
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class TwilioClient:
    """Twilio Programmable Voice client."""
    
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.caller_id = settings.TWILIO_CALLER_ID
        self.client = httpx.AsyncClient(
            auth=(self.account_sid, self.auth_token),
            timeout=30.0
        )
    
    async def make_call(
        self,
        to: str,
        from_: str,
        twiml_url: str,
        status_callback: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make an outbound call.
        
        Args:
            to: Phone number to call (E.164 format)
            from_: Phone number to call from (E.164 format)
            twiml_url: URL to TwiML instructions
            status_callback: Optional status callback URL
            
        Returns:
            Call response data
        """
        data = {
            "To": to,
            "From": from_ or self.caller_id,
            "Url": twiml_url
        }
        
        if status_callback:
            data["StatusCallback"] = status_callback
        
        response = await self.client.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Calls.json",
            data=data
        )
        response.raise_for_status()
        
        return response.json()
    
    def generate_twiml(
        self,
        script: str,
        gather_url: Optional[str] = None,
        timeout: int = 5,
        num_digits: int = 1
    ) -> str:
        """Generate TwiML for voice call.
        
        Args:
            script: Text to speak
            gather_url: URL to handle DTMF input
            timeout: Timeout for gathering digits
            num_digits: Number of digits to gather
            
        Returns:
            TwiML XML string
        """
        twiml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<Response>'
        ]
        
        if gather_url:
            # Add gather element for DTMF input
            twiml_lines.extend([
                f'<Gather action="{gather_url}" timeout="{timeout}" numDigits="{num_digits}">',
                f'<Say voice="Polly.Joanna">{script}</Say>',
                '</Gather>',
                # Fallback if no input
                '<Say voice="Polly.Joanna">I didn\'t receive any input. Goodbye.</Say>'
            ])
        else:
            # Just speak the script
            twiml_lines.append(f'<Say voice="Polly.Joanna">{script}</Say>')
        
        twiml_lines.append('</Response>')
        
        return '\n'.join(twiml_lines)
    
    def generate_confirmation_twiml(self, message: str) -> str:
        """Generate TwiML for confirmation message."""
        return self.generate_twiml(message)
    
    def generate_reschedule_twiml(self, options: list) -> str:
        """Generate TwiML for reschedule options."""
        script = "Here are your reschedule options. "
        for i, option in enumerate(options, 1):
            script += f"Press {i} for {option}. "
        script += "Press 0 to cancel."
        
        return self.generate_twiml(script)
    
    def verify_webhook_signature(
        self,
        signature: str,
        url: str,
        params: Dict[str, Any]
    ) -> bool:
        """Verify Twilio webhook signature.
        
        Args:
            signature: X-Twilio-Signature header value
            url: Full URL of the webhook
            params: Request parameters
            
        Returns:
            True if signature is valid
        """
        if not self.auth_token:
            logger.warning("No auth token configured for signature verification")
            return False
        
        # Create the signature string
        signature_string = url
        
        # Sort parameters and append to signature string
        for key in sorted(params.keys()):
            signature_string += key + params[key]
        
        # Create HMAC signature
        expected_signature = hmac.new(
            self.auth_token.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # Encode as base64
        expected_signature_b64 = expected_signature.hex()
        
        # Compare signatures
        return hmac.compare_digest(signature, expected_signature_b64)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class TwilioWebhookHandler:
    """Handle Twilio webhook callbacks."""
    
    def __init__(self, twilio_client: TwilioClient):
        self.twilio_client = twilio_client
    
    def handle_voice_answer(self, call_sid: str, from_number: str, to_number: str) -> str:
        """Handle voice answer webhook.
        
        Args:
            call_sid: Twilio call SID
            from_number: Caller's phone number
            to_number: Called phone number
            
        Returns:
            TwiML response
        """
        # This would typically look up the notification by call_sid
        # and generate appropriate script based on the event
        
        script = """Hello! This is your personal assistant calling about an upcoming appointment. 
        Press 1 to confirm, 2 to reschedule, or 3 to cancel. Press 9 to repeat this message, 
        or press 0 to have details sent to your email."""
        
        return self.twilio_client.generate_twiml(
            script=script,
            gather_url=f"{settings.BASE_URL}/twilio/voice/gather",
            timeout=10,
            num_digits=1
        )
    
    def handle_voice_gather(
        self,
        call_sid: str,
        digits: str,
        from_number: str
    ) -> str:
        """Handle DTMF input from voice call.
        
        Args:
            call_sid: Twilio call SID
            digits: DTMF digits received
            from_number: Caller's phone number
            
        Returns:
            TwiML response
        """
        if digits == "1":
            # Confirm
            message = "Thank you for confirming. Your appointment is confirmed. Goodbye!"
            return self.twilio_client.generate_confirmation_twiml(message)
        
        elif digits == "2":
            # Reschedule - offer options
            options = [
                "tomorrow at 2 PM",
                "day after tomorrow at 10 AM",
                "next Monday at 3 PM"
            ]
            return self.twilio_client.generate_reschedule_twiml(options)
        
        elif digits == "3":
            # Cancel
            message = "Your appointment has been cancelled. Goodbye!"
            return self.twilio_client.generate_confirmation_twiml(message)
        
        elif digits == "9":
            # Repeat
            return self.handle_voice_answer(call_sid, from_number, "")
        
        elif digits == "0":
            # Send email
            message = "I'll send the details to your email. Goodbye!"
            return self.twilio_client.generate_confirmation_twiml(message)
        
        else:
            # Invalid input
            message = "I didn't understand that. Please press 1 to confirm, 2 to reschedule, or 3 to cancel."
            return self.twilio_client.generate_twiml(
                script=message,
                gather_url=f"{settings.BASE_URL}/twilio/voice/gather",
                timeout=5,
                num_digits=1
            )
    
    def handle_voice_status(
        self,
        call_sid: str,
        call_status: str,
        answered_by: Optional[str] = None,
        duration: Optional[int] = None
    ) -> None:
        """Handle call status callback.
        
        Args:
            call_sid: Twilio call SID
            call_status: Call status (completed, busy, no-answer, etc.)
            answered_by: Who answered (human, machine, etc.)
            duration: Call duration in seconds
        """
        logger.info(
            "Call status update",
            call_sid=call_sid,
            status=call_status,
            answered_by=answered_by,
            duration=duration
        )
        
        # Update notification status in database
        # This would typically update the notifications table
        # with the call result and status
