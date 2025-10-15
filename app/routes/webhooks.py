"""Webhook routes for external services."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AuditLog

router = APIRouter()


@router.post("/google")
async def google_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Google Calendar push notifications."""
    try:
        # Get headers and body
        headers = dict(request.headers)
        body = await request.json()
        
        # Log the webhook
        audit_log = AuditLog(
            action="google_webhook",
            meta_json={
                "headers": headers,
                "body": body
            }
        )
        db.add(audit_log)
        await db.commit()
        
        # TODO: Process the webhook
        # This would typically:
        # 1. Verify the webhook signature
        # 2. Extract the resource ID and change type
        # 3. Trigger a calendar sync for the affected user
        # 4. Update notification plans if needed
        
        return {"status": "received"}
        
    except Exception as e:
        # Log error
        audit_log = AuditLog(
            action="google_webhook_error",
            meta_json={"error": str(e)}
        )
        db.add(audit_log)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.post("/sendgrid")
async def sendgrid_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle SendGrid webhook events (opens, clicks, etc.)."""
    try:
        # Get webhook data
        webhook_data = await request.json()
        
        # Log the webhook
        audit_log = AuditLog(
            action="sendgrid_webhook",
            meta_json={"data": webhook_data}
        )
        db.add(audit_log)
        await db.commit()
        
        # TODO: Process webhook events
        # This would typically:
        # 1. Verify the webhook signature
        # 2. Update notification status based on events
        # 3. Track email engagement metrics
        
        return {"status": "received"}
        
    except Exception as e:
        # Log error
        audit_log = AuditLog(
            action="sendgrid_webhook_error",
            meta_json={"error": str(e)}
        )
        db.add(audit_log)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}"
        )
