"""Comprehensive tools that expose all web application features."""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func

from mcp.capabilities.tools.base import FunctionTool
from mcp.core.concurrency import CancellationToken
from app.models import User, Event, Notification, AuditLog
from app.database import AsyncSessionLocal
from app.schemas import UserCreate, UserUpdate


async def create_user_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Create a new user."""
    if cancellation_token:
        cancellation_token.check()
    
    required_fields = ["name", "email"]
    missing = [f for f in required_fields if f not in params]
    if missing:
        return {"error": f"Missing required fields: {', '.join(missing)}"}
    
    async with AsyncSessionLocal() as db:
        # Check if user with email already exists
        existing_result = await db.execute(
            select(User).where(User.email == params["email"])
        )
        existing_user = existing_result.scalar_one_or_none()
        
        if existing_user:
            return {"error": "User with this email already exists"}
        
        # Create user data
        user_data = UserCreate(**params)
        user = User(**user_data.dict())
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "message": "User created successfully"
        }


async def update_user_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Update a user."""
    if cancellation_token:
        cancellation_token.check()
    
    user_id = params.get("user_id")
    if not user_id:
        return {"error": "user_id is required"}
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return {"error": "User not found"}
        
        # Update fields
        update_data = {k: v for k, v in params.items() if k != "user_id"}
        user_update = UserUpdate(**update_data)
        update_dict = user_update.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "message": "User updated successfully"
        }


async def delete_user_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Delete a user."""
    if cancellation_token:
        cancellation_token.check()
    
    user_id = params.get("user_id")
    if not user_id:
        return {"error": "user_id is required"}
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return {"error": "User not found"}
        
        await db.delete(user)
        await db.commit()
        
        return {"message": "User deleted successfully"}


async def get_dashboard_stats_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Get dashboard statistics."""
    if cancellation_token:
        cancellation_token.check()
    
    async with AsyncSessionLocal() as db:
        users_count = await db.scalar(select(func.count(User.id)))
        events_count = await db.scalar(select(func.count(Event.id)))
        notifications_count = await db.scalar(select(func.count(Notification.id)))
        
        # Recent notifications
        recent_notifications_result = await db.execute(
            select(Notification)
            .order_by(Notification.created_at.desc())
            .limit(10)
        )
        recent_notifications = [
            {
                "id": n.id,
                "user_id": n.user_id,
                "event_id": n.event_id,
                "channel": n.channel,
                "status": n.status,
                "plan_time": n.plan_time.isoformat(),
                "created_at": n.created_at.isoformat()
            }
            for n in recent_notifications_result.scalars().all()
        ]
        
        # Recent audit logs
        recent_audit_result = await db.execute(
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(10)
        )
        recent_audit = [
            {
                "id": a.id,
                "action": a.action,
                "user_id": a.user_id,
                "event_id": a.event_id,
                "created_at": a.created_at.isoformat()
            }
            for a in recent_audit_result.scalars().all()
        ]
        
        return {
            "stats": {
                "users": users_count,
                "events": events_count,
                "notifications": notifications_count
            },
            "recent_notifications": recent_notifications,
            "recent_audit": recent_audit
        }


async def sync_calendar_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Sync Google Calendar for a user."""
    if cancellation_token:
        cancellation_token.check()
    
    user_id = params.get("user_id")
    if not user_id:
        return {"error": "user_id is required"}
    
    days_back = params.get("days_back", 2)
    days_forward = params.get("days_forward", 30)
    
    async with AsyncSessionLocal() as db:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            return {"error": "User not found"}
        
        # Import here to avoid circular dependencies
        from app.models import OAuthAccount
        from app.calendar.google import GoogleCalendarClient
        
        # Check OAuth account
        oauth_result = await db.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user_id,
                OAuthAccount.provider == "google"
            )
        )
        oauth_account = oauth_result.scalar_one_or_none()
        
        if not oauth_account:
            return {"error": "Google Calendar not connected. Please complete OAuth flow first."}
        
        try:
            google_client = GoogleCalendarClient()
            from app.security.tokens import decrypt_token
            
            access_token = decrypt_token(oauth_account.access_token_enc)
            
            events = await google_client.get_events(
                access_token=access_token,
                time_min=datetime.utcnow() - timedelta(days=days_back),
                time_max=datetime.utcnow() + timedelta(days=days_forward)
            )
            
            # Process and store events
            events_created = 0
            events_updated = 0
            
            for google_event in events:
                normalized_event = google_client.normalize_event(google_event, user_id)
                
                existing_result = await db.execute(
                    select(Event).where(
                        Event.user_id == user_id,
                        Event.provider == "google",
                        Event.provider_event_id == normalized_event["provider_event_id"]
                    )
                )
                existing_event = existing_result.scalar_one_or_none()
                
                if existing_event:
                    for key, value in normalized_event.items():
                        if key != "user_id":
                            setattr(existing_event, key, value)
                    events_updated += 1
                else:
                    event = Event(**normalized_event)
                    db.add(event)
                    events_created += 1
            
            await db.commit()
            await google_client.close()
            
            return {
                "events_created": events_created,
                "events_updated": events_updated,
                "sync_time": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"Sync failed: {str(e)}"}


async def cancel_notification_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Cancel a scheduled notification."""
    if cancellation_token:
        cancellation_token.check()
    
    notification_id = params.get("notification_id")
    if not notification_id:
        return {"error": "notification_id is required"}
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            return {"error": "Notification not found"}
        
        if notification.status != "planned":
            return {"error": "Can only cancel planned notifications"}
        
        # Cancel in scheduler (if available)
        from app.deps import get_scheduler
        scheduler = get_scheduler()
        if scheduler:
            scheduler.cancel_notification(notification_id)
        
        notification.status = "cancelled"
        await db.commit()
        
        return {"message": "Notification cancelled successfully"}


# Export tools
CREATE_USER_TOOL = FunctionTool(
    name="createUser",
    description="Create a new user account",
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "User's full name"},
            "email": {"type": "string", "description": "User's email address"},
            "phone_e164": {"type": "string", "description": "Phone number in E.164 format (optional)"},
            "timezone": {"type": "string", "description": "Timezone (default: UTC)", "default": "UTC"},
            "channel_pref": {"type": "string", "enum": ["email", "call", "both"], "description": "Preferred notification channel", "default": "email"}
        },
        "required": ["name", "email"]
    },
    handler=create_user_tool
)

UPDATE_USER_TOOL = FunctionTool(
    name="updateUser",
    description="Update user preferences and settings",
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "User ID"},
            "name": {"type": "string", "description": "User's full name"},
            "email": {"type": "string", "description": "User's email address"},
            "phone_e164": {"type": "string", "description": "Phone number in E.164 format"},
            "timezone": {"type": "string", "description": "Timezone"},
            "channel_pref": {"type": "string", "enum": ["email", "call", "both"], "description": "Preferred notification channel"}
        },
        "required": ["user_id"]
    },
    handler=update_user_tool
)

DELETE_USER_TOOL = FunctionTool(
    name="deleteUser",
    description="Delete a user account",
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "User ID"}
        },
        "required": ["user_id"]
    },
    handler=delete_user_tool
)

GET_DASHBOARD_STATS_TOOL = FunctionTool(
    name="getDashboardStats",
    description="Get dashboard statistics (user counts, recent notifications, audit logs)",
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    handler=get_dashboard_stats_tool
)

SYNC_CALENDAR_TOOL = FunctionTool(
    name="syncCalendar",
    description="Sync Google Calendar events for a user",
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "User ID"},
            "days_back": {"type": "integer", "description": "Days to look back (default: 2)", "default": 2},
            "days_forward": {"type": "integer", "description": "Days to look forward (default: 30)", "default": 30}
        },
        "required": ["user_id"]
    },
    handler=sync_calendar_tool
)

CANCEL_NOTIFICATION_TOOL = FunctionTool(
    name="cancelNotification",
    description="Cancel a scheduled notification",
    input_schema={
        "type": "object",
        "properties": {
            "notification_id": {"type": "string", "description": "Notification ID"}
        },
        "required": ["notification_id"]
    },
    handler=cancel_notification_tool
)

