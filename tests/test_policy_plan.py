"""Tests for LLM policy planning."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.llm.policy import PolicyAgent
from app.llm.client import LLMClient
from app.schemas import PolicyRequest


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = AsyncMock(spec=LLMClient)
    return client


@pytest.fixture
def policy_agent(mock_llm_client):
    """Policy agent with mocked LLM client."""
    return PolicyAgent(mock_llm_client)


@pytest.fixture
def sample_event():
    """Sample event data."""
    return {
        "id": "test-event-1",
        "title": "Team Standup",
        "start_ts": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
        "end_ts": (datetime.utcnow() + timedelta(hours=2, minutes=30)).isoformat(),
        "location": "Conference Room A",
        "conf_link": "https://meet.google.com/test",
        "organizer": "manager@company.com",
        "attendees": [
            {"email": "user@company.com", "name": "User", "responseStatus": "accepted"}
        ],
        "description": "Daily team standup meeting",
        "status": "confirmed"
    }


@pytest.fixture
def sample_user_prefs():
    """Sample user preferences."""
    return {
        "channel_pref": "both",
        "quiet_start": "21:00",
        "quiet_end": "07:00",
        "max_call_attempts": 3,
        "weekend_policy": "email",
        "escalation_threshold": 60,
        "timezone": "America/New_York"
    }


@pytest.mark.asyncio
async def test_policy_planning_success(policy_agent, mock_llm_client, sample_event, sample_user_prefs):
    """Test successful policy planning."""
    # Mock LLM response
    mock_response = {
        "notify": True,
        "reasoning": "Event is in 2 hours, user prefers both channels",
        "plan": [
            {
                "offset_minutes": -30,
                "channel": "call",
                "subject": "Reminder: Team Standup",
                "tts_script": "Hello! You have a team standup meeting in 30 minutes. Press 1 to confirm, 2 to reschedule, or 3 to cancel.",
                "email_html": "<p>You have a team standup meeting in 30 minutes.</p>",
                "email_text": "You have a team standup meeting in 30 minutes.",
                "urgency": "normal"
            }
        ]
    }
    
    mock_llm_client.complete_json.return_value = mock_response
    
    # Create policy request
    request = PolicyRequest(
        event=sample_event,
        user_preferences=sample_user_prefs,
        history=[],
        timezone="America/New_York"
    )
    
    # Test policy planning
    result = await policy_agent.plan_notifications(request)
    
    # Assertions
    assert result.plan is not None
    assert len(result.plan) == 1
    assert result.plan[0]["channel"] == "call"
    assert result.plan[0]["offset_minutes"] == -30
    assert result.reasoning == "Event is in 2 hours, user prefers both channels"
    
    # Verify LLM was called
    mock_llm_client.complete_json.assert_called_once()


@pytest.mark.asyncio
async def test_policy_planning_no_notification(policy_agent, mock_llm_client, sample_event, sample_user_prefs):
    """Test policy planning when no notification is needed."""
    # Mock LLM response
    mock_response = {
        "notify": False,
        "reasoning": "Event is too far in the future",
        "plan": []
    }
    
    mock_llm_client.complete_json.return_value = mock_response
    
    # Create policy request
    request = PolicyRequest(
        event=sample_event,
        user_preferences=sample_user_prefs,
        history=[],
        timezone="America/New_York"
    )
    
    # Test policy planning
    result = await policy_agent.plan_notifications(request)
    
    # Assertions
    assert result.plan == []
    assert result.reasoning == "Event is too far in the future"


@pytest.mark.asyncio
async def test_policy_planning_llm_failure(policy_agent, mock_llm_client, sample_event, sample_user_prefs):
    """Test policy planning when LLM fails."""
    # Mock LLM failure
    mock_llm_client.complete_json.side_effect = Exception("LLM service unavailable")
    
    # Create policy request
    request = PolicyRequest(
        event=sample_event,
        user_preferences=sample_user_prefs,
        history=[],
        timezone="America/New_York"
    )
    
    # Test policy planning
    result = await policy_agent.plan_notifications(request)
    
    # Should fall back to default policy
    assert result.plan is not None
    assert result.reasoning == "Fallback policy applied due to LLM failure"


@pytest.mark.asyncio
async def test_policy_planning_quiet_hours(policy_agent, mock_llm_client, sample_event, sample_user_prefs):
    """Test policy planning respects quiet hours."""
    # Mock LLM response
    mock_response = {
        "notify": True,
        "reasoning": "Event is urgent, overriding quiet hours",
        "plan": [
            {
                "offset_minutes": -15,
                "channel": "call",
                "subject": "Urgent: Team Standup",
                "tts_script": "Urgent reminder: You have a team standup meeting in 15 minutes.",
                "email_html": "<p>Urgent: You have a team standup meeting in 15 minutes.</p>",
                "email_text": "Urgent: You have a team standup meeting in 15 minutes.",
                "urgency": "urgent"
            }
        ]
    }
    
    mock_llm_client.complete_json.return_value = mock_response
    
    # Create policy request
    request = PolicyRequest(
        event=sample_event,
        user_preferences=sample_user_prefs,
        history=[],
        timezone="America/New_York"
    )
    
    # Test policy planning
    result = await policy_agent.plan_notifications(request)
    
    # Assertions
    assert result.plan is not None
    assert len(result.plan) == 1
    assert result.plan[0]["urgency"] == "urgent"


@pytest.mark.asyncio
async def test_policy_planning_multiple_notifications(policy_agent, mock_llm_client, sample_event, sample_user_prefs):
    """Test policy planning with multiple notifications."""
    # Mock LLM response
    mock_response = {
        "notify": True,
        "reasoning": "Important event, multiple reminders needed",
        "plan": [
            {
                "offset_minutes": -60,
                "channel": "email",
                "subject": "Reminder: Team Standup",
                "tts_script": "You have a team standup meeting in 1 hour.",
                "email_html": "<p>You have a team standup meeting in 1 hour.</p>",
                "email_text": "You have a team standup meeting in 1 hour.",
                "urgency": "normal"
            },
            {
                "offset_minutes": -15,
                "channel": "call",
                "subject": "Final Reminder: Team Standup",
                "tts_script": "Final reminder: You have a team standup meeting in 15 minutes.",
                "email_html": "<p>Final reminder: You have a team standup meeting in 15 minutes.</p>",
                "email_text": "Final reminder: You have a team standup meeting in 15 minutes.",
                "urgency": "high"
            }
        ]
    }
    
    mock_llm_client.complete_json.return_value = mock_response
    
    # Create policy request
    request = PolicyRequest(
        event=sample_event,
        user_preferences=sample_user_prefs,
        history=[],
        timezone="America/New_York"
    )
    
    # Test policy planning
    result = await policy_agent.plan_notifications(request)
    
    # Assertions
    assert result.plan is not None
    assert len(result.plan) == 2
    assert result.plan[0]["channel"] == "email"
    assert result.plan[1]["channel"] == "call"
    assert result.plan[0]["offset_minutes"] == -60
    assert result.plan[1]["offset_minutes"] == -15
