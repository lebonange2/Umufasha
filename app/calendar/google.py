"""Google Calendar integration."""
import base64
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import httpx
import structlog

from app.core.config import settings
from app.security.tokens import decrypt_token, encrypt_token

logger = structlog.get_logger(__name__)


class GoogleCalendarClient:
    """Google Calendar API client."""
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = f"{settings.BASE_URL}/api/calendar/google/callback"
        self.scope = "https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def get_auth_url(self, state: str) -> str:
        """Get Google OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        response = await self.client.post(
            "https://oauth2.googleapis.com/token",
            data=data
        )
        response.raise_for_status()
        
        return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        response = await self.client.post(
            "https://oauth2.googleapis.com/token",
            data=data
        )
        response.raise_for_status()
        
        return response.json()
    
    async def get_events(
        self, 
        access_token: str, 
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 250
    ) -> List[Dict[str, Any]]:
        """Get events from Google Calendar."""
        if time_min is None:
            time_min = datetime.now(timezone.utc) - timedelta(days=2)
        if time_max is None:
            time_max = datetime.now(timezone.utc) + timedelta(days=30)
        
        params = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        response = await self.client.get(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            params=params,
            headers=headers
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("items", [])
    
    async def create_event(
        self,
        access_token: str,
        event_data: Dict[str, Any],
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Create a new event in Google Calendar."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = await self.client.post(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            json=event_data,
            headers=headers
        )
        response.raise_for_status()
        
        return response.json()
    
    async def update_event(
        self,
        access_token: str,
        event_id: str,
        event_data: Dict[str, Any],
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Update an existing event in Google Calendar."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = await self.client.put(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
            json=event_data,
            headers=headers
        )
        response.raise_for_status()
        
        return response.json()
    
    async def delete_event(
        self,
        access_token: str,
        event_id: str,
        calendar_id: str = "primary"
    ) -> bool:
        """Delete an event from Google Calendar."""
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = await self.client.delete(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
            headers=headers
        )
        
        return response.status_code == 204
    
    def normalize_event(self, google_event: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Normalize Google Calendar event to our Event model."""
        # Extract start/end times
        start_data = google_event.get("start", {})
        end_data = google_event.get("end", {})
        
        # Handle both date and dateTime fields
        if "dateTime" in start_data:
            start_ts = datetime.fromisoformat(start_data["dateTime"].replace('Z', '+00:00'))
        else:
            # All-day event
            start_ts = datetime.fromisoformat(start_data["date"] + "T00:00:00+00:00")
        
        if "dateTime" in end_data:
            end_ts = datetime.fromisoformat(end_data["dateTime"].replace('Z', '+00:00'))
        else:
            # All-day event
            end_ts = datetime.fromisoformat(end_data["date"] + "T23:59:59+00:00")
        
        # Extract attendees
        attendees = []
        for attendee in google_event.get("attendees", []):
            attendees.append({
                "email": attendee.get("email"),
                "name": attendee.get("displayName"),
                "responseStatus": attendee.get("responseStatus", "needsAction")
            })
        
        # Extract organizer
        organizer = google_event.get("organizer", {})
        organizer_email = organizer.get("email", "")
        organizer_name = organizer.get("displayName", "")
        
        # Extract conference link
        conf_link = None
        conference_data = google_event.get("conferenceData", {})
        if conference_data:
            entry_points = conference_data.get("entryPoints", [])
            for entry_point in entry_points:
                if entry_point.get("entryPointType") == "video":
                    conf_link = entry_point.get("uri")
                    break
        
        # Create event hash for change detection
        event_hash = self._create_event_hash(google_event)
        
        return {
            "user_id": user_id,
            "provider": "google",
            "provider_event_id": google_event["id"],
            "title": google_event.get("summary", "Untitled Event"),
            "start_ts": start_ts,
            "end_ts": end_ts,
            "location": google_event.get("location"),
            "conf_link": conf_link,
            "organizer": organizer_email,
            "attendees": attendees,
            "description": google_event.get("description"),
            "status": google_event.get("status", "confirmed"),
            "etag": google_event.get("etag"),
            "hash": event_hash
        }
    
    def _create_event_hash(self, event: Dict[str, Any]) -> str:
        """Create a hash of the event for change detection."""
        import hashlib
        
        # Create a string representation of the important fields
        hash_data = {
            "summary": event.get("summary", ""),
            "start": event.get("start", {}),
            "end": event.get("end", {}),
            "location": event.get("location", ""),
            "description": event.get("description", ""),
            "status": event.get("status", "")
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
