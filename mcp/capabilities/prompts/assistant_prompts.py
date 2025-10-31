"""Assistant application prompts for MCP."""
from typing import Dict, Any, List
from pathlib import Path

from mcp.capabilities.prompts.base import Prompt


class NotificationPolicyPrompt(Prompt):
    """Notification policy prompt template."""
    
    def __init__(self):
        # Load prompt template from file
        template_path = Path(__file__).parent.parent.parent.parent.parent / "prompts" / "policy.md"
        if template_path.exists():
            self.template = template_path.read_text()
        else:
            self.template = """# Notification Policy Agent

You are a scheduling policy agent for a personal assistant. Your job is to decide when and how to notify users about their upcoming appointments.

## Your Role
Given user preferences, event metadata, and history, you must decide:
1. Whether to notify (yes/no)
2. Channel: call or email (or both)
3. Timing offsets (e.g., T-24h, T-2h, T-30m, T-5m)
4. Tone and script for TTS / email body

## Critical Rules
- **Respect quiet hours**: No calls during quiet hours unless urgent (<12h)
- **Never schedule more than 3 attempts** per event
- **Be concise, courteous, and actionable**
- **Include RSVP options**: 1=Confirm, 2=Reschedule, 3=Cancel for calls
- **Never leak sensitive information**
- **Consider travel time and location**
- **Escalate to calls for urgent meetings** (<1h)

Output strictly as JSON with the structure specified in the context.
"""
    
    @property
    def name(self) -> str:
        return "notificationPolicy"
    
    @property
    def description(self) -> str:
        return "LLM prompt template for notification planning policy decisions"
    
    @property
    def arguments(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "event_data",
                "description": "Event data (JSON string)",
                "required": True
            },
            {
                "name": "user_preferences",
                "description": "User preferences (JSON string)",
                "required": True
            },
            {
                "name": "history",
                "description": "Notification history (JSON string, optional)",
                "required": False
            },
            {
                "name": "timezone",
                "description": "User timezone (e.g., 'America/New_York')",
                "required": False
            }
        ]
    
    async def render(
        self,
        arguments: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Render notification policy prompt."""
        import json
        
        event_data = arguments.get("event_data", "{}")
        user_preferences = arguments.get("user_preferences", "{}")
        history = arguments.get("history", "[]")
        timezone = arguments.get("timezone", "UTC")
        
        # Parse JSON strings
        try:
            event_obj = json.loads(event_data) if isinstance(event_data, str) else event_data
            user_prefs_obj = json.loads(user_preferences) if isinstance(user_preferences, str) else user_preferences
            history_obj = json.loads(history) if isinstance(history, str) else history
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in arguments: {e}")
        
        # Build context
        context = f"""Event Data:
{json.dumps(event_obj, indent=2)}

User Preferences:
{json.dumps(user_prefs_obj, indent=2)}

Notification History:
{json.dumps(history_obj, indent=2)}

Timezone: {timezone}

Based on the above context, decide when and how to notify the user about this event.
"""
        
        return [
            {
                "role": "system",
                "content": self.template
            },
            {
                "role": "user",
                "content": context
            }
        ]


class EmailTemplatePrompt(Prompt):
    """Email template prompt."""
    
    def __init__(self):
        template_path = Path(__file__).parent.parent.parent.parent.parent / "prompts" / "email_style.md"
        if template_path.exists():
            self.template = template_path.read_text()
        else:
            self.template = """# Email Style Guidelines

## Design Principles
- **Mobile-first**: Most emails are read on mobile devices
- **Scannable**: Use clear headings and bullet points
- **Action-oriented**: Make it easy to take action
- **Professional**: Maintain a business-appropriate tone
"""
    
    @property
    def name(self) -> str:
        return "emailTemplate"
    
    @property
    def description(self) -> str:
        return "Email notification template with styling guidelines"
    
    @property
    def arguments(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "event_title",
                "description": "Event title",
                "required": True
            },
            {
                "name": "event_time",
                "description": "Event start time (ISO format)",
                "required": True
            },
            {
                "name": "event_location",
                "description": "Event location (optional)",
                "required": False
            },
            {
                "name": "urgency",
                "description": "Urgency level (low, normal, high, urgent)",
                "required": False
            }
        ]
    
    async def render(
        self,
        arguments: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Render email template prompt."""
        event_title = arguments.get("event_title", "Meeting")
        event_time = arguments.get("event_time", "")
        event_location = arguments.get("event_location", "")
        urgency = arguments.get("urgency", "normal")
        
        content = f"""Generate an email notification for:
- Title: {event_title}
- Time: {event_time}
- Location: {event_location or 'Not specified'}
- Urgency: {urgency}

Follow the email style guidelines to create a professional, mobile-friendly email.
"""
        
        return [
            {
                "role": "system",
                "content": self.template
            },
            {
                "role": "user",
                "content": content
            }
        ]


class TTSScriptPrompt(Prompt):
    """TTS script prompt."""
    
    def __init__(self):
        template_path = Path(__file__).parent.parent.parent.parent.parent / "prompts" / "tts_style.md"
        if template_path.exists():
            self.template = template_path.read_text()
        else:
            self.template = """# TTS Script Guidelines

## Voice and Tone
- **Professional but friendly**: Sound like a helpful assistant, not a robot
- **Clear and concise**: Get to the point quickly
- **Natural pacing**: Speak at a comfortable speed
- **Polite and respectful**: Always be courteous
"""
    
    @property
    def name(self) -> str:
        return "ttsScript"
    
    @property
    def description(self) -> str:
        return "TTS script template for phone calls"
    
    @property
    def arguments(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "event_title",
                "description": "Event title",
                "required": True
            },
            {
                "name": "event_time",
                "description": "Event start time (human-readable, e.g., 'tomorrow at 2 PM')",
                "required": True
            },
            {
                "name": "event_location",
                "description": "Event location (optional)",
                "required": False
            },
            {
                "name": "urgency",
                "description": "Urgency level (low, normal, high, urgent)",
                "required": False
            }
        ]
    
    async def render(
        self,
        arguments: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Render TTS script prompt."""
        event_title = arguments.get("event_title", "Meeting")
        event_time = arguments.get("event_time", "")
        event_location = arguments.get("event_location", "")
        urgency = arguments.get("urgency", "normal")
        
        content = f"""Generate a TTS script for a phone call about:
- Title: {event_title}
- Time: {event_time}
- Location: {event_location or 'Not specified'}
- Urgency: {urgency}

Follow the TTS script guidelines to create a natural, concise phone script.
"""
        
        return [
            {
                "role": "system",
                "content": self.template
            },
            {
                "role": "user",
                "content": content
            }
        ]


# Export prompt instances
NOTIFICATION_POLICY_PROMPT = NotificationPolicyPrompt()
EMAIL_TEMPLATE_PROMPT = EmailTemplatePrompt()
TTS_SCRIPT_PROMPT = TTSScriptPrompt()

