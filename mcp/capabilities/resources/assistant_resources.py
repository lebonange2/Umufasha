"""Assistant application resources for MCP."""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
import json

from mcp.capabilities.resources.base import Resource
from app.models import User, Event, Notification
from app.database import AsyncSessionLocal


class UserResource(Resource):
    """User resource."""
    
    @property
    def uri(self) -> str:
        return "resources://users/{user_id}"
    
    @property
    def name(self) -> str:
        return "User Profile"
    
    @property
    def description(self) -> str:
        return "User profile data by user ID"
    
    async def read(
        self,
        uri: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Read user resource."""
        # Parse URI: resources://users/{user_id}
        if not uri.startswith("resources://users/"):
            raise ValueError(f"Invalid user resource URI: {uri}")
        
        user_id = uri.replace("resources://users/", "")
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                return {
                    "error": "User not found",
                    "content": "",
                    "mimeType": "application/json"
                }
            
            user_data = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone_e164": user.phone_e164,
                "timezone": user.timezone,
                "channel_pref": user.channel_pref,
                "quiet_start": user.quiet_start,
                "quiet_end": user.quiet_end,
                "locale": user.locale,
                "voice": user.voice,
                "max_call_attempts": user.max_call_attempts,
                "weekend_policy": user.weekend_policy,
                "escalation_threshold": user.escalation_threshold,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
            
            content = json.dumps(user_data, indent=2)
            content_bytes = content.encode("utf-8")
            
            # Apply offset/limit if provided
            if offset is not None:
                content_bytes = content_bytes[offset:]
            if limit is not None:
                content_bytes = content_bytes[:limit]
            
            # Compute hash for cache coherency
            content_hash = hashlib.sha256(content_bytes).hexdigest()
            
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": content_bytes.decode("utf-8"),
                        "hash": content_hash
                    }
                ]
            }


class EventResource(Resource):
    """Event resource."""
    
    @property
    def uri(self) -> str:
        return "resources://events/{event_id}"
    
    @property
    def name(self) -> str:
        return "Calendar Event"
    
    @property
    def description(self) -> str:
        return "Calendar event data by event ID"
    
    async def read(
        self,
        uri: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Read event resource."""
        if not uri.startswith("resources://events/"):
            raise ValueError(f"Invalid event resource URI: {uri}")
        
        event_id = uri.replace("resources://events/", "")
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Event).where(Event.id == event_id))
            event = result.scalar_one_or_none()
            
            if not event:
                return {
                    "error": "Event not found",
                    "contents": [],
                    "mimeType": "application/json"
                }
            
            event_data = {
                "id": event.id,
                "user_id": event.user_id,
                "title": event.title,
                "start_ts": event.start_ts.isoformat(),
                "end_ts": event.end_ts.isoformat(),
                "location": event.location,
                "conf_link": event.conf_link,
                "organizer": event.organizer,
                "attendees": event.attendees,
                "description": event.description,
                "status": event.status,
                "provider": event.provider,
                "provider_event_id": event.provider_event_id,
                "etag": event.etag,
                "last_seen_at": event.last_seen_at.isoformat()
            }
            
            content = json.dumps(event_data, indent=2)
            content_bytes = content.encode("utf-8")
            
            if offset is not None:
                content_bytes = content_bytes[offset:]
            if limit is not None:
                content_bytes = content_bytes[:limit]
            
            content_hash = hashlib.sha256(content_bytes).hexdigest()
            
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": content_bytes.decode("utf-8"),
                        "hash": content_hash
                    }
                ]
            }


class UserEventsResource(Resource):
    """User events list resource."""
    
    @property
    def uri(self) -> str:
        return "resources://users/{user_id}/events"
    
    @property
    def name(self) -> str:
        return "User Events"
    
    @property
    def description(self) -> str:
        return "List of events for a user"
    
    async def read(
        self,
        uri: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Read user events resource."""
        if not uri.startswith("resources://users/") or not uri.endswith("/events"):
            raise ValueError(f"Invalid user events resource URI: {uri}")
        
        user_id = uri.replace("resources://users/", "").replace("/events", "")
        
        now = datetime.utcnow()
        start_time = now - timedelta(days=2)
        end_time = now + timedelta(days=30)
        
        async with AsyncSessionLocal() as db:
            from sqlalchemy import and_
            result = await db.execute(
                select(Event).where(
                    and_(
                        Event.user_id == user_id,
                        Event.start_ts >= start_time,
                        Event.start_ts <= end_time
                    )
                ).order_by(Event.start_ts)
            )
            events = result.scalars().all()
            
            events_data = [
                {
                    "id": event.id,
                    "title": event.title,
                    "start_ts": event.start_ts.isoformat(),
                    "end_ts": event.end_ts.isoformat(),
                    "location": event.location,
                    "status": event.status
                }
                for event in events
            ]
            
            content = json.dumps({"events": events_data, "count": len(events_data)}, indent=2)
            content_bytes = content.encode("utf-8")
            
            if offset is not None:
                content_bytes = content_bytes[offset:]
            if limit is not None:
                content_bytes = content_bytes[:limit]
            
            content_hash = hashlib.sha256(content_bytes).hexdigest()
            
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": content_bytes.decode("utf-8"),
                        "hash": content_hash
                    }
                ]
            }


# Export resource instances
USER_RESOURCE = UserResource()
EVENT_RESOURCE = EventResource()
USER_EVENTS_RESOURCE = UserEventsResource()

