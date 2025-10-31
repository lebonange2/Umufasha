"""Assistant application tools for MCP."""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from mcp.capabilities.tools.base import FunctionTool
from mcp.core.concurrency import CancellationToken
from app.models import User, Event, Notification
from app.database import AsyncSessionLocal
from app.llm.client import LLMClient
from app.scheduling.planner import NotificationPlanner
from app.deps import get_llm_client


async def get_user_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Get a user by ID."""
    if cancellation_token:
        cancellation_token.check()
    
    user_id = params.get("user_id")
    if not user_id:
        raise ValueError("user_id is required")
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return {"error": "User not found"}
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone_e164": user.phone_e164,
            "timezone": user.timezone,
            "channel_pref": user.channel_pref,
            "quiet_start": user.quiet_start,
            "quiet_end": user.quiet_end
        }


GET_USER_TOOL = FunctionTool(
    name="getUser",
    description="Get user details by ID",
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "User ID"
            }
        },
        "required": ["user_id"]
    },
    handler=get_user_tool
)


async def list_events_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """List events with optional filters."""
    if cancellation_token:
        cancellation_token.check()
    
    user_id = params.get("user_id")
    days_back = params.get("days_back", 2)
    days_forward = params.get("days_forward", 30)
    
    now = datetime.utcnow()
    start_time = now - timedelta(days=days_back)
    end_time = now + timedelta(days=days_forward)
    
    async with AsyncSessionLocal() as db:
        query = select(Event).where(
            and_(
                Event.start_ts >= start_time,
                Event.start_ts <= end_time
            )
        )
        
        if user_id:
            query = query.where(Event.user_id == user_id)
        
        query = query.order_by(Event.start_ts)
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        return {
            "events": [
                {
                    "id": event.id,
                    "user_id": event.user_id,
                    "title": event.title,
                    "start_ts": event.start_ts.isoformat(),
                    "end_ts": event.end_ts.isoformat(),
                    "location": event.location,
                    "status": event.status,
                    "provider": event.provider
                }
                for event in events
            ],
            "count": len(events)
        }


LIST_EVENTS_TOOL = FunctionTool(
    name="listEvents",
    description="List calendar events with optional filters",
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "Optional user ID filter"
            },
            "days_back": {
                "type": "integer",
                "description": "Days to look back (default: 2)",
                "default": 2,
                "minimum": 0,
                "maximum": 30
            },
            "days_forward": {
                "type": "integer",
                "description": "Days to look forward (default: 30)",
                "default": 30,
                "minimum": 1,
                "maximum": 90
            }
        }
    },
    handler=list_events_tool
)


async def plan_notifications_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Plan notifications for user events using LLM policy."""
    if cancellation_token:
        cancellation_token.check()
    
    user_id = params.get("user_id")
    event_id = params.get("event_id")
    force_replan = params.get("force_replan", False)
    
    if not user_id:
        raise ValueError("user_id is required")
    
    async with AsyncSessionLocal() as db:
        llm_client = get_llm_client()
        planner = NotificationPlanner(llm_client)
        
        result = await planner.plan_user_notifications(
            db=db,
            user_id=user_id,
            event_id=event_id,
            force_replan=force_replan
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        return {
            "notifications_planned": result.get("notifications_planned", 0),
            "events_processed": result.get("events_processed", 0),
            "plan_time": datetime.utcnow().isoformat()
        }


PLAN_NOTIFICATIONS_TOOL = FunctionTool(
    name="planNotifications",
    description="Plan notifications for user events using LLM policy agent",
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "User ID to plan notifications for"
            },
            "event_id": {
                "type": "string",
                "description": "Optional specific event ID (if omitted, plans for all events)"
            },
            "force_replan": {
                "type": "boolean",
                "description": "Force replanning even if notifications exist (default: false)",
                "default": False
            }
        },
        "required": ["user_id"]
    },
    handler=plan_notifications_tool
)


async def get_event_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Get an event by ID."""
    if cancellation_token:
        cancellation_token.check()
    
    event_id = params.get("event_id")
    if not event_id:
        raise ValueError("event_id is required")
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        
        if not event:
            return {"error": "Event not found"}
        
        return {
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
            "provider_event_id": event.provider_event_id
        }


GET_EVENT_TOOL = FunctionTool(
    name="getEvent",
    description="Get event details by ID",
    input_schema={
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "Event ID"
            }
        },
        "required": ["event_id"]
    },
    handler=get_event_tool
)


async def list_notifications_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """List notifications with optional filters."""
    if cancellation_token:
        cancellation_token.check()
    
    user_id = params.get("user_id")
    status_filter = params.get("status")
    days_forward = params.get("days_forward", 7)
    
    now = datetime.utcnow()
    end_time = now + timedelta(days=days_forward)
    
    async with AsyncSessionLocal() as db:
        query = select(Notification).where(
            and_(
                Notification.plan_time >= now,
                Notification.plan_time <= end_time
            )
        )
        
        if user_id:
            query = query.where(Notification.user_id == user_id)
        
        if status_filter:
            query = query.where(Notification.status == status_filter)
        
        query = query.order_by(Notification.plan_time)
        
        result = await db.execute(query)
        notifications = result.scalars().all()
        
        return {
            "notifications": [
                {
                    "id": notif.id,
                    "user_id": notif.user_id,
                    "event_id": notif.event_id,
                    "channel": notif.channel,
                    "plan_time": notif.plan_time.isoformat(),
                    "status": notif.status,
                    "sent_time": notif.sent_time.isoformat() if notif.sent_time else None
                }
                for notif in notifications
            ],
            "count": len(notifications)
        }


LIST_NOTIFICATIONS_TOOL = FunctionTool(
    name="listNotifications",
    description="List notifications with optional filters",
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "Optional user ID filter"
            },
            "status": {
                "type": "string",
                "description": "Optional status filter (planned, sent, delivered, failed, cancelled)"
            },
            "days_forward": {
                "type": "integer",
                "description": "Days to look forward (default: 7)",
                "default": 7,
                "minimum": 1,
                "maximum": 30
            }
        }
    },
    handler=list_notifications_tool
)

