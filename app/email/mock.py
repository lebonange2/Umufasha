"""Mock email client for testing without real API calls."""
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger(__name__)


class MockSendGridClient:
    """Mock SendGrid client for testing and development."""
    
    def __init__(self):
        self.emails = []  # Store sent emails
        self.email_counter = 0
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        ics_content: Optional[str] = None,
        tracking: bool = True
    ) -> Dict[str, Any]:
        """Mock sending an email."""
        self.email_counter += 1
        message_id = f"mock-{self.email_counter:06d}"
        
        email_data = {
            "message_id": message_id,
            "to_email": to_email,
            "subject": subject,
            "html_content": html_content,
            "text_content": text_content,
            "ics_content": ics_content,
            "tracking": tracking,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "sent"
        }
        
        self.emails.append(email_data)
        
        logger.info(
            "Mock email sent",
            message_id=message_id,
            to_email=to_email,
            subject=subject
        )
        
        return {
            "status": "sent",
            "message_id": message_id,
            "provider": "mock_sendgrid"
        }
    
    async def send_notification_email(
        self,
        to_email: str,
        event: Dict[str, Any],
        notification: Dict[str, Any],
        rsvp_token: str
    ) -> Dict[str, Any]:
        """Mock sending a notification email."""
        # Generate subject
        subject = notification.get("subject", f"Reminder: {event.get('title', 'Meeting')}")
        
        # Generate HTML content
        html_content = self._generate_html_email(event, notification, rsvp_token)
        
        # Generate text content
        text_content = self._generate_text_email(event, notification, rsvp_token)
        
        # Generate ICS content
        ics_content = None
        if event:
            from app.calendar.ics import ICSGenerator
            ics_content = ICSGenerator.generate_ics(event)
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            ics_content=ics_content
        )
    
    def _generate_html_email(
        self,
        event: Dict[str, Any],
        notification: Dict[str, Any],
        rsvp_token: str
    ) -> str:
        """Generate HTML email content."""
        title = event.get("title", "Untitled Event")
        start_time = event.get("start_ts", "")
        location = event.get("location", "")
        conf_link = event.get("conf_link", "")
        description = event.get("description", "")
        
        # Format start time
        from datetime import datetime
        if isinstance(start_time, str):
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                formatted_time = start_dt.strftime("%A, %B %d, %Y at %I:%M %p")
            except:
                formatted_time = start_time
        else:
            formatted_time = str(start_time)
        
        # Generate RSVP links
        base_url = "http://localhost:8000"
        confirm_url = f"{base_url}/rsvp/{rsvp_token}?action=confirm"
        reschedule_url = f"{base_url}/rsvp/{rsvp_token}?action=reschedule"
        cancel_url = f"{base_url}/rsvp/{rsvp_token}?action=cancel"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .event-details {{ background-color: #ffffff; border: 1px solid #dee2e6; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .rsvp-buttons {{ text-align: center; margin: 20px 0; }}
                .btn {{ display: inline-block; padding: 12px 24px; margin: 5px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .btn-confirm {{ background-color: #28a745; color: white; }}
                .btn-reschedule {{ background-color: #ffc107; color: black; }}
                .btn-cancel {{ background-color: #dc3545; color: white; }}
                .footer {{ font-size: 12px; color: #6c757d; text-align: center; margin-top: 30px; }}
                .conference-link {{ margin: 10px 0; }}
                .conference-link a {{ color: #007bff; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📅 Meeting Reminder</h1>
                    <p>This is a reminder about your upcoming appointment.</p>
                </div>
                
                <div class="event-details">
                    <h2>{title}</h2>
                    <p><strong>📅 Date & Time:</strong> {formatted_time}</p>
                    {f'<p><strong>📍 Location:</strong> {location}</p>' if location else ''}
                    {f'<div class="conference-link"><strong>🔗 Meeting Link:</strong> <a href="{conf_link}">{conf_link}</a></div>' if conf_link else ''}
                    {f'<p><strong>📝 Description:</strong><br>{description}</p>' if description else ''}
                </div>
                
                <div class="rsvp-buttons">
                    <h3>Quick Actions</h3>
                    <a href="{confirm_url}" class="btn btn-confirm">✅ Confirm</a>
                    <a href="{reschedule_url}" class="btn btn-reschedule">🔄 Reschedule</a>
                    <a href="{cancel_url}" class="btn btn-cancel">❌ Cancel</a>
                </div>
                
                <div class="footer">
                    <p>This email was sent by your Personal Assistant (MOCK MODE).</p>
                    <p>You can also add this event to your calendar using the attached .ics file.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_email(
        self,
        event: Dict[str, Any],
        notification: Dict[str, Any],
        rsvp_token: str
    ) -> str:
        """Generate plain text email content."""
        title = event.get("title", "Untitled Event")
        start_time = event.get("start_ts", "")
        location = event.get("location", "")
        conf_link = event.get("conf_link", "")
        description = event.get("description", "")
        
        # Format start time
        from datetime import datetime
        if isinstance(start_time, str):
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                formatted_time = start_dt.strftime("%A, %B %d, %Y at %I:%M %p")
            except:
                formatted_time = start_time
        else:
            formatted_time = str(start_time)
        
        # Generate RSVP links
        base_url = "http://localhost:8000"
        confirm_url = f"{base_url}/rsvp/{rsvp_token}?action=confirm"
        reschedule_url = f"{base_url}/rsvp/{rsvp_token}?action=reschedule"
        cancel_url = f"{base_url}/rsvp/{rsvp_token}?action=cancel"
        
        text = f"""
MEETING REMINDER (MOCK MODE)

{title}

Date & Time: {formatted_time}
{f'Location: {location}' if location else ''}
{f'Meeting Link: {conf_link}' if conf_link else ''}
{f'Description: {description}' if description else ''}

QUICK ACTIONS:
- Confirm: {confirm_url}
- Reschedule: {reschedule_url}
- Cancel: {cancel_url}

This email was sent by your Personal Assistant (MOCK MODE).
You can also add this event to your calendar using the attached .ics file.
        """
        
        return text.strip()
    
    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Get all sent emails."""
        return self.emails.copy()
    
    def get_email_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get email by message ID."""
        for email in self.emails:
            if email["message_id"] == message_id:
                return email
        return None
    
    def clear_emails(self):
        """Clear email history."""
        self.emails.clear()
    
    async def close(self):
        """Close the mock client."""
        logger.info("Mock SendGrid client closed")
