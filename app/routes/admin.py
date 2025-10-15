"""Admin UI routes."""
from typing import List
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import User, Event, Notification, AuditLog
from app.deps import get_optional_admin_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_optional_admin_user)
):
    """Admin dashboard."""
    # Get statistics
    users_count = await db.scalar(select(func.count(User.id)))
    events_count = await db.scalar(select(func.count(Event.id)))
    notifications_count = await db.scalar(select(func.count(Notification.id)))
    
    # Get recent notifications
    recent_notifications_result = await db.execute(
        select(Notification)
        .order_by(Notification.created_at.desc())
        .limit(10)
    )
    recent_notifications = recent_notifications_result.scalars().all()
    
    # Get recent audit logs
    recent_audit_result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    recent_audit = recent_audit_result.scalars().all()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "admin_user": admin_user,
        "stats": {
            "users": users_count,
            "events": events_count,
            "notifications": notifications_count
        },
        "recent_notifications": recent_notifications,
        "recent_audit": recent_audit
    })


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_optional_admin_user)
):
    """Users management page."""
    users_result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = users_result.scalars().all()
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "admin_user": admin_user,
        "users": users
    })


@router.get("/events", response_class=HTMLResponse)
async def admin_events(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_optional_admin_user)
):
    """Events management page."""
    events_result = await db.execute(
        select(Event)
        .order_by(Event.start_ts.desc())
        .limit(100)
    )
    events = events_result.scalars().all()
    
    return templates.TemplateResponse("admin/events.html", {
        "request": request,
        "admin_user": admin_user,
        "events": events
    })


@router.get("/notifications", response_class=HTMLResponse)
async def admin_notifications(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_optional_admin_user)
):
    """Notifications management page."""
    notifications_result = await db.execute(
        select(Notification)
        .order_by(Notification.plan_time.desc())
        .limit(100)
    )
    notifications = notifications_result.scalars().all()
    
    return templates.TemplateResponse("admin/notifications.html", {
        "request": request,
        "admin_user": admin_user,
        "notifications": notifications
    })


@router.get("/logs", response_class=HTMLResponse)
async def admin_logs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_optional_admin_user)
):
    """Audit logs page."""
    logs_result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    )
    logs = logs_result.scalars().all()
    
    return templates.TemplateResponse("admin/logs.html", {
        "request": request,
        "admin_user": admin_user,
        "logs": logs
    })
