"""ICS (iCalendar) file generation and parsing."""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid


class ICSGenerator:
    """Generate ICS files for calendar events."""
    
    @staticmethod
    def generate_ics(event: Dict[str, Any], method: str = "REQUEST") -> str:
        """Generate ICS content for an event.
        
        Args:
            event: Event data
            method: ICS method (REQUEST, CANCEL, etc.)
            
        Returns:
            ICS content string
        """
        # Generate unique UID if not provided
        uid = event.get("uid", f"{uuid.uuid4()}@assistant.local")
        
        # Format timestamps
        start_ts = event["start_ts"]
        end_ts = event["end_ts"]
        
        if isinstance(start_ts, str):
            start_dt = datetime.fromisoformat(start_ts.replace('Z', '+00:00'))
        else:
            start_dt = start_ts
        
        if isinstance(end_ts, str):
            end_dt = datetime.fromisoformat(end_ts.replace('Z', '+00:00'))
        else:
            end_dt = end_ts
        
        # Convert to UTC and format for ICS
        start_utc = start_dt.astimezone(timezone.utc)
        end_utc = end_dt.astimezone(timezone.utc)
        
        start_str = start_utc.strftime("%Y%m%dT%H%M%SZ")
        end_str = end_utc.strftime("%Y%m%dT%H%M%SZ")
        now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        
        # Escape text fields
        title = ICSGenerator._escape_text(event.get("title", "Untitled Event"))
        description = ICSGenerator._escape_text(event.get("description", ""))
        location = ICSGenerator._escape_text(event.get("location", ""))
        organizer = event.get("organizer", "")
        
        # Build ICS content
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Assistant//Personal Assistant//EN",
            f"METHOD:{method}",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART:{start_str}",
            f"DTEND:{end_str}",
            f"DTSTAMP:{now_str}",
            f"SUMMARY:{title}",
        ]
        
        if description:
            ics_lines.append(f"DESCRIPTION:{description}")
        
        if location:
            ics_lines.append(f"LOCATION:{location}")
        
        if organizer:
            ics_lines.append(f"ORGANIZER:MAILTO:{organizer}")
        
        # Add attendees
        attendees = event.get("attendees", [])
        for attendee in attendees:
            email = attendee.get("email", "")
            name = attendee.get("name", "")
            status = attendee.get("responseStatus", "NEEDS-ACTION")
            
            if email:
                attendee_line = f"ATTENDEE:MAILTO:{email}"
                if name:
                    attendee_line += f";CN={ICSGenerator._escape_text(name)}"
                attendee_line += f";RSVP=TRUE;PARTSTAT={status.upper()}"
                ics_lines.append(attendee_line)
        
        # Add conference link
        conf_link = event.get("conf_link")
        if conf_link:
            ics_lines.append(f"URL:{conf_link}")
        
        # Add status
        status = event.get("status", "confirmed")
        if status == "cancelled":
            ics_lines.append("STATUS:CANCELLED")
        elif status == "tentative":
            ics_lines.append("STATUS:TENTATIVE")
        else:
            ics_lines.append("STATUS:CONFIRMED")
        
        ics_lines.extend([
            "END:VEVENT",
            "END:VCALENDAR"
        ])
        
        return "\r\n".join(ics_lines)
    
    @staticmethod
    def _escape_text(text: str) -> str:
        """Escape text for ICS format."""
        if not text:
            return ""
        
        # Replace line breaks with \\n
        text = text.replace("\n", "\\n").replace("\r", "")
        
        # Escape special characters
        text = text.replace("\\", "\\\\")
        text = text.replace(",", "\\,")
        text = text.replace(";", "\\;")
        text = text.replace("\"", "\\\"")
        
        # Limit line length (ICS recommends 75 characters)
        lines = []
        current_line = ""
        
        for char in text:
            if len(current_line) >= 75:
                lines.append(current_line)
                current_line = " " + char  # Continuation line starts with space
            else:
                current_line += char
        
        if current_line:
            lines.append(current_line)
        
        return "\r\n".join(lines)
    
    @staticmethod
    def generate_rsvp_ics(event: Dict[str, Any], action: str, new_time: Optional[datetime] = None) -> str:
        """Generate ICS for RSVP response.
        
        Args:
            event: Original event data
            action: RSVP action (confirm, cancel, reschedule)
            new_time: New time for reschedule
            
        Returns:
            ICS content string
        """
        # Create a copy of the event
        rsvp_event = event.copy()
        
        # Update based on action
        if action == "cancel":
            rsvp_event["status"] = "cancelled"
            method = "CANCEL"
        elif action == "reschedule" and new_time:
            # Calculate duration
            start_ts = event["start_ts"]
            end_ts = event["end_ts"]
            
            if isinstance(start_ts, str):
                start_dt = datetime.fromisoformat(start_ts.replace('Z', '+00:00'))
            else:
                start_dt = start_ts
            
            if isinstance(end_ts, str):
                end_dt = datetime.fromisoformat(end_ts.replace('Z', '+00:00'))
            else:
                end_dt = end_ts
            
            duration = end_dt - start_dt
            new_end = new_time + duration
            
            rsvp_event["start_ts"] = new_time
            rsvp_event["end_ts"] = new_end
            method = "REQUEST"
        else:
            method = "REPLY"
        
        return ICSGenerator.generate_ics(rsvp_event, method)
