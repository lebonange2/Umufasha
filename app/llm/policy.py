"""LLM-powered notification policy agent."""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog

from app.llm.client import LLMClient
from app.schemas import PolicyRequest, PolicyResponse

logger = structlog.get_logger(__name__)


class PolicyAgent:
    """LLM-powered policy agent for notification planning."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt for the policy agent."""
        return """You are a scheduling policy agent for a personal assistant. Your job is to decide when and how to notify users about their upcoming appointments.

Given user preferences, event metadata, and history, you must decide:
1. Whether to notify (yes/no)
2. Channel: call or email (or both)
3. Timing offsets (e.g., T-24h, T-2h, T-30m, T-5m)
4. Tone and script for TTS / email body

CRITICAL RULES:
- Respect quiet hours (no calls during quiet hours unless urgent <12h)
- Never schedule more than 3 attempts per event
- Be concise, courteous, and actionable
- Include RSVP options (1=Confirm, 2=Reschedule, 3=Cancel for calls)
- Never leak sensitive information
- Consider travel time and location
- Escalate to calls for urgent meetings (<1h)

Output strictly as JSON with this structure:
{
  "notify": true/false,
  "reasoning": "brief explanation",
  "plan": [
    {
      "offset_minutes": -1440,
      "channel": "email",
      "subject": "Meeting Reminder: Team Standup",
      "tts_script": "Hello, this is your assistant. You have a team standup meeting tomorrow at 9 AM. Press 1 to confirm, 2 to reschedule, or 3 to cancel.",
      "email_html": "<p>You have a meeting tomorrow...</p>",
      "email_text": "You have a meeting tomorrow...",
      "urgency": "normal"
    }
  ]
}

Urgency levels: low, normal, high, urgent
Channels: email, call, both
Offset is minutes before event start (negative = before, positive = after)"""

    async def plan_notifications(self, request: PolicyRequest) -> PolicyResponse:
        """Plan notifications for an event.
        
        Args:
            request: Policy request with event and user data
            
        Returns:
            Policy response with notification plan
        """
        try:
            # Build context for the LLM
            context = self._build_context(request)
            
            # Get policy decision from LLM
            response = await self.llm_client.complete_json(
                system=self.system_prompt,
                user=context
            )
            
            # Validate and clean response
            plan = self._validate_response(response)
            
            return PolicyResponse(
                plan=plan,
                reasoning=response.get("reasoning", "")
            )
            
        except Exception as e:
            logger.error("Policy planning failed", error=str(e), event_id=request.event.get("id"))
            # Fallback to default policy
            return self._fallback_policy(request)
    
    def _build_context(self, request: PolicyRequest) -> str:
        """Build context string for the LLM."""
        event = request.event
        prefs = request.user_preferences
        
        # Format event data
        start_time = event.get("start_ts", "")
        title = event.get("title", "Untitled Event")
        location = event.get("location", "")
        organizer = event.get("organizer", "")
        attendees = event.get("attendees", [])
        
        # Calculate time until event
        if isinstance(start_time, str):
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = start_time
        
        now = datetime.now(start_dt.tzinfo)
        time_until = start_dt - now
        hours_until = time_until.total_seconds() / 3600
        
        context = f"""Event Details:
- Title: {title}
- Start: {start_time}
- Duration: {hours_until:.1f} hours from now
- Location: {location or 'Not specified'}
- Organizer: {organizer or 'Unknown'}
- Attendees: {len(attendees)} people
- Status: {event.get('status', 'confirmed')}

User Preferences:
- Channel preference: {prefs.get('channel_pref', 'email')}
- Quiet hours: {prefs.get('quiet_start', '21:00')} - {prefs.get('quiet_end', '07:00')}
- Max call attempts: {prefs.get('max_call_attempts', 3)}
- Weekend policy: {prefs.get('weekend_policy', 'email')}
- Escalation threshold: {prefs.get('escalation_threshold', 60)} minutes
- Timezone: {request.timezone}

Context:
- Current time: {now.isoformat()}
- Time until event: {hours_until:.1f} hours
- Is weekend: {now.weekday() >= 5}
- Is quiet hours: {self._is_quiet_hours(now, prefs)}
- Is urgent: {hours_until < (prefs.get('escalation_threshold', 60) / 60)}

History: {request.history or 'No previous notifications for this event'}

Please decide on the notification plan for this event."""

        return context
    
    def _is_quiet_hours(self, now: datetime, prefs: Dict[str, Any]) -> bool:
        """Check if current time is within quiet hours."""
        try:
            quiet_start = prefs.get('quiet_start', '21:00')
            quiet_end = prefs.get('quiet_end', '07:00')
            
            current_time = now.strftime('%H:%M')
            
            # Handle overnight quiet hours (e.g., 21:00 - 07:00)
            if quiet_start > quiet_end:
                return current_time >= quiet_start or current_time <= quiet_end
            else:
                return quiet_start <= current_time <= quiet_end
        except Exception:
            return False
    
    def _validate_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate and clean the LLM response."""
        if not isinstance(response, dict):
            raise ValueError("Response must be a dictionary")
        
        if not response.get("notify", False):
            return []
        
        plan = response.get("plan", [])
        if not isinstance(plan, list):
            raise ValueError("Plan must be a list")
        
        # Validate each notification in the plan
        validated_plan = []
        for item in plan:
            if not isinstance(item, dict):
                continue
            
            # Ensure required fields
            validated_item = {
                "offset_minutes": item.get("offset_minutes", -60),
                "channel": item.get("channel", "email"),
                "subject": item.get("subject", "Meeting Reminder"),
                "tts_script": item.get("tts_script", "You have a meeting coming up."),
                "email_html": item.get("email_html", "<p>You have a meeting coming up.</p>"),
                "email_text": item.get("email_text", "You have a meeting coming up."),
                "urgency": item.get("urgency", "normal")
            }
            
            # Validate channel
            if validated_item["channel"] not in ["email", "call", "both"]:
                validated_item["channel"] = "email"
            
            # Validate urgency
            if validated_item["urgency"] not in ["low", "normal", "high", "urgent"]:
                validated_item["urgency"] = "normal"
            
            validated_plan.append(validated_item)
        
        # Limit to 3 notifications max
        return validated_plan[:3]
    
    def _fallback_policy(self, request: PolicyRequest) -> PolicyResponse:
        """Fallback policy when LLM fails."""
        event = request.event
        prefs = request.user_preferences
        
        # Simple fallback: email 1 hour before, call 15 minutes before if urgent
        start_time = event.get("start_ts", "")
        if isinstance(start_time, str):
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = start_time
        
        now = datetime.now(start_dt.tzinfo)
        time_until = start_dt - now
        hours_until = time_until.total_seconds() / 3600
        
        plan = []
        
        # Email reminder 1 hour before
        if hours_until > 1:
            plan.append({
                "offset_minutes": -60,
                "channel": "email",
                "subject": f"Reminder: {event.get('title', 'Meeting')}",
                "tts_script": f"You have {event.get('title', 'a meeting')} in 1 hour.",
                "email_html": f"<p>You have <strong>{event.get('title', 'a meeting')}</strong> in 1 hour.</p>",
                "email_text": f"You have {event.get('title', 'a meeting')} in 1 hour.",
                "urgency": "normal"
            })
        
        # Call 15 minutes before if urgent
        if hours_until < 1 and prefs.get('channel_pref') in ['call', 'both']:
            plan.append({
                "offset_minutes": -15,
                "channel": "call",
                "subject": f"Urgent: {event.get('title', 'Meeting')}",
                "tts_script": f"Urgent reminder: You have {event.get('title', 'a meeting')} in 15 minutes. Press 1 to confirm, 2 to reschedule, or 3 to cancel.",
                "email_html": f"<p><strong>Urgent:</strong> You have {event.get('title', 'a meeting')} in 15 minutes.</p>",
                "email_text": f"Urgent: You have {event.get('title', 'a meeting')} in 15 minutes.",
                "urgency": "urgent"
            })
        
        return PolicyResponse(
            plan=plan,
            reasoning="Fallback policy applied due to LLM failure"
        )
