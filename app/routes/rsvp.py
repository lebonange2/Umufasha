"""RSVP routes for email actions."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Event, Notification, AuditLog
from app.security.tokens import validate_rsvp_token
from app.calendar.google import GoogleCalendarClient
from app.calendar.ics import ICSGenerator

router = APIRouter()


@router.get("/{token}")
async def rsvp_page(
    token: str,
    action: str = Query(..., description="Action: confirm, cancel, or reschedule"),
    db: AsyncSession = Depends(get_db)
):
    """Handle RSVP actions from email links."""
    # Validate token
    token_data = validate_rsvp_token(token)
    if not token_data:
        return HTMLResponse(
            content="<h1>Invalid or Expired Link</h1><p>This RSVP link is invalid or has expired.</p>",
            status_code=400
        )
    
    user_id = token_data["user_id"]
    event_id = token_data["event_id"]
    notification_id = token_data["notification_id"]
    
    # Get user and event
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    event_result = await db.execute(select(Event).where(Event.id == event_id))
    event = event_result.scalar_one_or_none()
    
    if not user or not event:
        return HTMLResponse(
            content="<h1>Error</h1><p>User or event not found.</p>",
            status_code=404
        )
    
    try:
        # Process the action
        if action == "confirm":
            result = await _handle_confirm(db, user, event, notification_id)
        elif action == "cancel":
            result = await _handle_cancel(db, user, event, notification_id)
        elif action == "reschedule":
            result = await _handle_reschedule(db, user, event, notification_id)
        else:
            return HTMLResponse(
                content="<h1>Invalid Action</h1><p>Invalid action specified.</p>",
                status_code=400
            )
        
        # Log the action
        audit_log = AuditLog(
            user_id=user_id,
            event_id=event_id,
            action=f"rsvp_{action}",
            meta_json={"notification_id": notification_id, "result": result}
        )
        db.add(audit_log)
        await db.commit()
        
        # Return success page
        return HTMLResponse(content=_generate_success_html(action, result))
        
    except Exception as e:
        # Log error
        audit_log = AuditLog(
            user_id=user_id,
            event_id=event_id,
            action=f"rsvp_{action}_error",
            meta_json={"error": str(e)}
        )
        db.add(audit_log)
        await db.commit()
        
        return HTMLResponse(
            content=f"<h1>Error</h1><p>Failed to process {action}: {str(e)}</p>",
            status_code=500
        )


async def _handle_confirm(db: AsyncSession, user: User, event: Event, notification_id: str) -> dict:
    """Handle confirm action."""
    # Update event status if needed
    if event.status != "confirmed":
        event.status = "confirmed"
        await db.commit()
    
    return {"status": "confirmed", "message": "Event confirmed successfully"}


async def _handle_cancel(db: AsyncSession, user: User, event: Event, notification_id: str) -> dict:
    """Handle cancel action."""
    # Update event status
    event.status = "cancelled"
    await db.commit()
    
    # TODO: Update calendar provider if connected
    # This would involve:
    # 1. Getting OAuth tokens for the user
    # 2. Calling the calendar provider API to cancel the event
    # 3. Handling any errors
    
    return {"status": "cancelled", "message": "Event cancelled successfully"}


async def _handle_reschedule(db: AsyncSession, user: User, event: Event, notification_id: str) -> dict:
    """Handle reschedule action."""
    # For now, just return a message about rescheduling
    # In a full implementation, this would:
    # 1. Show available time slots
    # 2. Allow user to select new time
    # 3. Update the event
    # 4. Update the calendar provider
    
    return {
        "status": "reschedule_requested",
        "message": "Reschedule requested. Please contact the organizer to find a new time."
    }


def _generate_success_html(action: str, result: dict) -> str:
    """Generate success HTML page."""
    title = {
        "confirm": "Event Confirmed",
        "cancel": "Event Cancelled",
        "reschedule": "Reschedule Requested"
    }.get(action, "Action Completed")
    
    message = result.get("message", f"{action} completed successfully")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
            .success {{ background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 20px; border-radius: 5px; }}
            .icon {{ font-size: 48px; text-align: center; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="success">
            <div class="icon">✅</div>
            <h1>{title}</h1>
            <p>{message}</p>
            <p>You can close this window now.</p>
        </div>
    </body>
    </html>
    """
