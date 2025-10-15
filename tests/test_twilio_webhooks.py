"""Tests for Twilio webhook handling."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.telephony.twilio import TwilioClient, TwilioWebhookHandler


@pytest.fixture
def twilio_client():
    """Twilio client for testing."""
    return TwilioClient()


@pytest.fixture
def webhook_handler(twilio_client):
    """Webhook handler for testing."""
    return TwilioWebhookHandler(twilio_client)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_voice_answer_webhook(webhook_handler):
    """Test voice answer webhook handling."""
    call_sid = "CA1234567890abcdef"
    from_number = "+1234567890"
    to_number = "+0987654321"
    
    twiml = webhook_handler.handle_voice_answer(call_sid, from_number, to_number)
    
    # Check that TwiML is generated
    assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" in twiml
    assert "<Response>" in twiml
    assert "<Say" in twiml
    assert "<Gather" in twiml
    assert "Press 1 to confirm" in twiml
    assert "Press 2 to reschedule" in twiml
    assert "Press 3 to cancel" in twiml


def test_voice_gather_confirm(webhook_handler):
    """Test voice gather with confirm action."""
    call_sid = "CA1234567890abcdef"
    digits = "1"
    from_number = "+1234567890"
    
    twiml = webhook_handler.handle_voice_gather(call_sid, digits, from_number)
    
    # Check that confirmation TwiML is generated
    assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" in twiml
    assert "<Response>" in twiml
    assert "<Say" in twiml
    assert "Thank you for confirming" in twiml
    assert "Goodbye" in twiml


def test_voice_gather_reschedule(webhook_handler):
    """Test voice gather with reschedule action."""
    call_sid = "CA1234567890abcdef"
    digits = "2"
    from_number = "+1234567890"
    
    twiml = webhook_handler.handle_voice_gather(call_sid, digits, from_number)
    
    # Check that reschedule TwiML is generated
    assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" in twiml
    assert "<Response>" in twiml
    assert "<Say" in twiml
    assert "reschedule options" in twiml
    assert "Press 1 for" in twiml
    assert "Press 2 for" in twiml
    assert "Press 3 for" in twiml


def test_voice_gather_cancel(webhook_handler):
    """Test voice gather with cancel action."""
    call_sid = "CA1234567890abcdef"
    digits = "3"
    from_number = "+1234567890"
    
    twiml = webhook_handler.handle_voice_gather(call_sid, digits, from_number)
    
    # Check that cancellation TwiML is generated
    assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" in twiml
    assert "<Response>" in twiml
    assert "<Say" in twiml
    assert "cancelled" in twiml
    assert "Goodbye" in twiml


def test_voice_gather_repeat(webhook_handler):
    """Test voice gather with repeat action."""
    call_sid = "CA1234567890abcdef"
    digits = "9"
    from_number = "+1234567890"
    
    twiml = webhook_handler.handle_voice_gather(call_sid, digits, from_number)
    
    # Should return to the original message
    assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" in twiml
    assert "<Response>" in twiml
    assert "<Say" in twiml


def test_voice_gather_email(webhook_handler):
    """Test voice gather with email action."""
    call_sid = "CA1234567890abcdef"
    digits = "0"
    from_number = "+1234567890"
    
    twiml = webhook_handler.handle_voice_gather(call_sid, digits, from_number)
    
    # Check that email TwiML is generated
    assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" in twiml
    assert "<Response>" in twiml
    assert "<Say" in twiml
    assert "send the details to your email" in twiml


def test_voice_gather_invalid_input(webhook_handler):
    """Test voice gather with invalid input."""
    call_sid = "CA1234567890abcdef"
    digits = "5"  # Invalid digit
    from_number = "+1234567890"
    
    twiml = webhook_handler.handle_voice_gather(call_sid, digits, from_number)
    
    # Check that error TwiML is generated
    assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" in twiml
    assert "<Response>" in twiml
    assert "<Say" in twiml
    assert "didn't understand" in twiml
    assert "<Gather" in twiml  # Should ask for input again


def test_voice_status_callback(webhook_handler):
    """Test voice status callback handling."""
    call_sid = "CA1234567890abcdef"
    call_status = "completed"
    answered_by = "human"
    duration = 45
    
    # Should not raise an exception
    webhook_handler.handle_voice_status(
        call_sid=call_sid,
        call_status=call_status,
        answered_by=answered_by,
        duration=duration
    )


def test_twiml_generation(twilio_client):
    """Test TwiML generation."""
    script = "Hello, this is a test message."
    gather_url = "https://example.com/gather"
    
    twiml = twilio_client.generate_twiml(
        script=script,
        gather_url=gather_url,
        timeout=10,
        num_digits=1
    )
    
    # Check TwiML structure
    assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" in twiml
    assert "<Response>" in twiml
    assert "<Gather" in twiml
    assert f'action="{gather_url}"' in twiml
    assert 'timeout="10"' in twiml
    assert 'numDigits="1"' in twiml
    assert "<Say" in twiml
    assert script in twiml


def test_twiml_without_gather(twilio_client):
    """Test TwiML generation without gather."""
    script = "Hello, this is a test message."
    
    twiml = twilio_client.generate_twiml(script=script)
    
    # Check TwiML structure
    assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" in twiml
    assert "<Response>" in twiml
    assert "<Say" in twiml
    assert script in twiml
    assert "<Gather" not in twiml  # Should not have gather


@patch('app.telephony.twilio.settings')
def test_webhook_signature_verification(mock_settings, twilio_client):
    """Test webhook signature verification."""
    mock_settings.TWILIO_AUTH_TOKEN = "test_auth_token"
    
    # Test with valid signature (simplified test)
    signature = "test_signature"
    url = "https://example.com/webhook"
    params = {"CallSid": "CA123", "From": "+1234567890"}
    
    # This is a simplified test - in reality, you'd need to generate
    # a proper HMAC signature for testing
    result = twilio_client.verify_webhook_signature(signature, url, params)
    
    # Should return False for invalid signature
    assert result is False


def test_webhook_endpoints(client):
    """Test webhook endpoints return proper responses."""
    # Test voice answer endpoint
    response = client.post(
        "/twilio/voice/answer",
        data={
            "CallSid": "CA1234567890abcdef",
            "From": "+1234567890",
            "To": "+0987654321",
            "CallStatus": "ringing"
        }
    )
    
    # Should return TwiML
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<?xml" in response.text
    
    # Test voice gather endpoint
    response = client.post(
        "/twilio/voice/gather",
        data={
            "CallSid": "CA1234567890abcdef",
            "Digits": "1",
            "From": "+1234567890"
        }
    )
    
    # Should return TwiML
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<?xml" in response.text
    
    # Test voice status endpoint
    response = client.post(
        "/twilio/voice/status",
        data={
            "CallSid": "CA1234567890abcdef",
            "CallStatus": "completed",
            "AnsweredBy": "human",
            "Duration": "45"
        }
    )
    
    # Should return JSON
    assert response.status_code == 200
    assert response.json()["status"] == "received"
