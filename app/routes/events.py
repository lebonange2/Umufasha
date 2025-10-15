"""Event management routes."""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models import Event, User
from app.schemas import Event as EventSchema
from app.deps import get_admin_user

router = APIRouter()


@router.get("/", response_model=List[EventSchema])
async def list_events(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    days_back: int = Query(2, ge=0, le=30, description="Days to look back"),
    days_forward: int = Query(30, ge=1, le=90, description="Days to look forward"),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """List events within a time window."""
    now = datetime.utcnow()
    start_time = now - timedelta(days=days_back)
    end_time = now + timedelta(days=days_forward)
    
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
    
    return events


@router.get("/{event_id}", response_model=EventSchema)
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Get an event by ID."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return event


@router.get("/user/{user_id}", response_model=List[EventSchema])
async def get_user_events(
    user_id: str,
    days_back: int = Query(2, ge=0, le=30),
    days_forward: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Get events for a specific user."""
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    now = datetime.utcnow()
    start_time = now - timedelta(days=days_back)
    end_time = now + timedelta(days=days_forward)
    
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
    
    return events
