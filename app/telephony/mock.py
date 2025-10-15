"""Mock Twilio client for testing without real API calls."""
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class MockTwilioClient:
    """Mock Twilio client for testing and development."""
    
    def __init__(self):
        self.calls = {}  # Store mock call data
        self.call_counter = 0
    
    async def make_call(
        self,
        to: str,
        from_: str,
        twiml_url: str,
        status_callback: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock making an outbound call."""
        self.call_counter += 1
        call_sid = f"CA{self.call_counter:012d}abcdef"
        
        # Store call data
        self.calls[call_sid] = {
            "sid": call_sid,
            "to": to,
            "from": from_,
            "status": "initiated",
            "twiml_url": twiml_url,
            "status_callback": status_callback,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Mock call initiated",
            call_sid=call_sid,
            to=to,
            from_=from_,
            twiml_url=twiml_url
        )
        
        # Simulate call progression
        await self._simulate_call_progression(call_sid)
        
        return {
            "sid": call_sid,
            "status": "initiated",
            "to": to,
            "from": from_
        }
    
    async def _simulate_call_progression(self, call_sid: str):
        """Simulate call progression for testing."""
        call_data = self.calls[call_sid]
        
        # Simulate call being answered
        await asyncio.sleep(1)
        call_data["status"] = "ringing"
        logger.info("Mock call ringing", call_sid=call_sid)
        
        # Simulate call being answered
        await asyncio.sleep(2)
        call_data["status"] = "in-progress"
        call_data["answered_by"] = "human"
        logger.info("Mock call answered", call_sid=call_sid)
        
        # Simulate call completion
        await asyncio.sleep(5)
        call_data["status"] = "completed"
        call_data["duration"] = 5
        logger.info("Mock call completed", call_sid=call_sid)
        
        # Send status callback if configured
        if call_data.get("status_callback"):
            await self._send_status_callback(call_sid, call_data)
    
    async def _send_status_callback(self, call_sid: str, call_data: Dict[str, Any]):
        """Send mock status callback."""
        import httpx
        
        callback_data = {
            "CallSid": call_sid,
            "CallStatus": call_data["status"],
            "From": call_data["from"],
            "To": call_data["to"],
            "AnsweredBy": call_data.get("answered_by"),
            "Duration": call_data.get("duration")
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    call_data["status_callback"],
                    data=callback_data,
                    timeout=10.0
                )
                logger.info(
                    "Mock status callback sent",
                    call_sid=call_sid,
                    status_code=response.status_code
                )
        except Exception as e:
            logger.error(
                "Mock status callback failed",
                call_sid=call_sid,
                error=str(e)
            )
    
    def generate_twiml(
        self,
        script: str,
        gather_url: Optional[str] = None,
        timeout: int = 5,
        num_digits: int = 1
    ) -> str:
        """Generate TwiML for voice call (same as real client)."""
        twiml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<Response>'
        ]
        
        if gather_url:
            twiml_lines.extend([
                f'<Gather action="{gather_url}" timeout="{timeout}" numDigits="{num_digits}">',
                f'<Say voice="Polly.Joanna">{script}</Say>',
                '</Gather>',
                '<Say voice="Polly.Joanna">I didn\'t receive any input. Goodbye.</Say>'
            ])
        else:
            twiml_lines.append(f'<Say voice="Polly.Joanna">{script}</Say>')
        
        twiml_lines.append('</Response>')
        
        return '\n'.join(twiml_lines)
    
    def verify_webhook_signature(
        self,
        signature: str,
        url: str,
        params: Dict[str, Any]
    ) -> bool:
        """Mock webhook signature verification (always returns True for testing)."""
        logger.info("Mock webhook signature verification", signature=signature)
        return True  # Always return True for testing
    
    def get_call_status(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get mock call status."""
        return self.calls.get(call_sid)
    
    def get_all_calls(self) -> Dict[str, Dict[str, Any]]:
        """Get all mock calls."""
        return self.calls.copy()
    
    async def close(self):
        """Close the mock client."""
        logger.info("Mock Twilio client closed")


class MockTwilioWebhookHandler:
    """Mock webhook handler for testing."""
    
    def __init__(self, mock_client: MockTwilioClient):
        self.mock_client = mock_client
        self.interactions = []  # Store webhook interactions
    
    def handle_voice_answer(self, call_sid: str, from_number: str, to_number: str) -> str:
        """Handle voice answer webhook."""
        interaction = {
            "type": "voice_answer",
            "call_sid": call_sid,
            "from_number": from_number,
            "to_number": to_number,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.interactions.append(interaction)
        
        script = """Hello! This is your personal assistant calling about an upcoming appointment. 
        Press 1 to confirm, 2 to reschedule, or 3 to cancel. Press 9 to repeat this message, 
        or press 0 to have details sent to your email."""
        
        return self.mock_client.generate_twiml(
            script=script,
            gather_url=f"http://localhost:8000/twilio/voice/gather",
            timeout=10,
            num_digits=1
        )
    
    def handle_voice_gather(
        self,
        call_sid: str,
        digits: str,
        from_number: str
    ) -> str:
        """Handle DTMF input from voice call."""
        interaction = {
            "type": "voice_gather",
            "call_sid": call_sid,
            "digits": digits,
            "from_number": from_number,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.interactions.append(interaction)
        
        if digits == "1":
            message = "Thank you for confirming. Your appointment is confirmed. Goodbye!"
            return self.mock_client.generate_twiml(message)
        
        elif digits == "2":
            options = [
                "tomorrow at 2 PM",
                "day after tomorrow at 10 AM",
                "next Monday at 3 PM"
            ]
            script = "Here are your reschedule options. "
            for i, option in enumerate(options, 1):
                script += f"Press {i} for {option}. "
            script += "Press 0 to cancel."
            return self.mock_client.generate_twiml(script)
        
        elif digits == "3":
            message = "Your appointment has been cancelled. Goodbye!"
            return self.mock_client.generate_twiml(message)
        
        elif digits == "9":
            return self.handle_voice_answer(call_sid, from_number, "")
        
        elif digits == "0":
            message = "I'll send the details to your email. Goodbye!"
            return self.mock_client.generate_twiml(message)
        
        else:
            message = "I didn't understand that. Please press 1 to confirm, 2 to reschedule, or 3 to cancel."
            return self.mock_client.generate_twiml(
                script=message,
                gather_url=f"http://localhost:8000/twilio/voice/gather",
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
        """Handle call status callback."""
        interaction = {
            "type": "voice_status",
            "call_sid": call_sid,
            "call_status": call_status,
            "answered_by": answered_by,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.interactions.append(interaction)
        
        logger.info(
            "Mock call status update",
            call_sid=call_sid,
            status=call_status,
            answered_by=answered_by,
            duration=duration
        )
    
    def get_interactions(self) -> list:
        """Get all webhook interactions."""
        return self.interactions.copy()
    
    def clear_interactions(self):
        """Clear interaction history."""
        self.interactions.clear()
