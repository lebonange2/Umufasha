"""SendGrid email integration."""
from typing import Dict, Any, Optional, List
import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class SendGridClient:
    """SendGrid email client."""
    
    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = "assistant@assistant.local"
        self.from_name = "Personal Assistant"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        ics_content: Optional[str] = None,
        tracking: bool = True
    ) -> Dict[str, Any]:
        """Send an email via SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            ics_content: Optional ICS calendar attachment
            tracking: Enable click/open tracking
            
        Returns:
            SendGrid response data
        """
        # Build email payload
        email_data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {
                "email": self.from_email,
                "name": self.from_name
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": text_content
                },
                {
                    "type": "text/html",
                    "value": html_content
                }
            ]
        }
        
        # Add ICS attachment if provided
        if ics_content:
            email_data["attachments"] = [
                {
                    "content": ics_content.encode('utf-8').decode('base64'),
                    "type": "text/calendar",
                    "filename": "event.ics",
                    "disposition": "attachment"
                }
            ]
        
        # Add tracking settings
        if tracking:
            email_data["tracking_settings"] = {
                "click_tracking": {"enable": True},
                "open_tracking": {"enable": True}
            }
        
        response = await self.client.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=email_data
        )
        response.raise_for_status()
        
        return {
            "status": "sent",
            "message_id": response.headers.get("X-Message-Id"),
            "provider": "sendgrid"
        }
    
    async def send_notification_email(
        self,
        to_email: str,
        event: Dict[str, Any],
        notification: Dict[str, Any],
        rsvp_token: str
    ) -> Dict[str, Any]:
        """Send a notification email for an event.
        
        Args:
            to_email: Recipient email address
            event: Event data
            notification: Notification data
            rsvp_token: RSVP token for actions
            
        Returns:
            SendGrid response data
        """
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
        base_url = settings.BASE_URL
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
                    <p>This email was sent by your Personal Assistant.</p>
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
        base_url = settings.BASE_URL
        confirm_url = f"{base_url}/rsvp/{rsvp_token}?action=confirm"
        reschedule_url = f"{base_url}/rsvp/{rsvp_token}?action=reschedule"
        cancel_url = f"{base_url}/rsvp/{rsvp_token}?action=cancel"
        
        text = f"""
MEETING REMINDER

{title}

Date & Time: {formatted_time}
{f'Location: {location}' if location else ''}
{f'Meeting Link: {conf_link}' if conf_link else ''}
{f'Description: {description}' if description else ''}

QUICK ACTIONS:
- Confirm: {confirm_url}
- Reschedule: {reschedule_url}
- Cancel: {cancel_url}

This email was sent by your Personal Assistant.
You can also add this event to your calendar using the attached .ics file.
        """
        
        return text.strip()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
