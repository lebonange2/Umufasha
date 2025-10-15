"""Notification management routes."""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models import Notification, User, Event
from app.schemas import Notification as NotificationSchema, NotificationPlanRequest, NotificationPlanResponse
from app.deps import get_admin_user, get_scheduler
from app.scheduling.planner import NotificationPlanner
from app.scheduling.scheduler import NotificationScheduler
from app.llm.client import LLMClient
from app.deps import get_llm_client

router = APIRouter()


@router.get("/", response_model=List[NotificationSchema])
async def list_notifications(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    days_forward: int = Query(7, ge=1, le=30, description="Days to look forward"),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """List notifications within a time window."""
    now = datetime.utcnow()
    end_time = now + timedelta(days=days_forward)
    
    query = select(Notification).where(
        and_(
            Notification.plan_time >= now,
            Notification.plan_time <= end_time
        )
    )
    
    if user_id:
        query = query.where(Notification.user_id == user_id)
    
    if status:
        query = query.where(Notification.status == status)
    
    query = query.order_by(Notification.plan_time)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return notifications


@router.get("/{notification_id}", response_model=NotificationSchema)
async def get_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Get a notification by ID."""
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return notification


@router.post("/plan", response_model=NotificationPlanResponse)
async def plan_notifications(
    request: NotificationPlanRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user),
    llm_client: LLMClient = Depends(get_llm_client)
):
    """Plan notifications for a user's events."""
    planner = NotificationPlanner(llm_client)
    
    result = await planner.plan_user_notifications(
        db=db,
        user_id=request.user_id,
        event_id=request.event_id,
        force_replan=request.force_replan
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return NotificationPlanResponse(
        notifications_planned=result["notifications_planned"],
        plan_time=datetime.utcnow()
    )


@router.post("/{notification_id}/cancel")
async def cancel_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user),
    scheduler: NotificationScheduler = Depends(get_scheduler)
):
    """Cancel a scheduled notification."""
    # Get notification
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if notification.status != "planned":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel planned notifications"
        )
    
    # Cancel in scheduler
    if scheduler:
        scheduler.cancel_notification(notification_id)
    
    # Update status in database
    notification.status = "cancelled"
    await db.commit()
    
    return {"message": "Notification cancelled successfully"}


@router.get("/user/{user_id}/upcoming", response_model=List[NotificationSchema])
async def get_upcoming_notifications(
    user_id: str,
    hours: int = Query(24, ge=1, le=168, description="Hours to look ahead"),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Get upcoming notifications for a user."""
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    now = datetime.utcnow()
    end_time = now + timedelta(hours=hours)
    
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.plan_time >= now,
                Notification.plan_time <= end_time,
                Notification.status == "planned"
            )
        ).order_by(Notification.plan_time)
    )
    notifications = result.scalars().all()
    
    return notifications
