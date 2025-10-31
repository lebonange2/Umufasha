"""Admin UI routes."""
from typing import List
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import secrets
import structlog
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, Event, Notification, AuditLog
from app.deps import get_optional_admin_user, get_admin_user
from app.core.config import settings
from app.schemas import UserCreate, UserUpdate

logger = structlog.get_logger()
router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

# In-memory session storage (in production, use Redis or database)
admin_sessions = {}


@router.get("/", response_class=HTMLResponse)
async def admin_root(request: Request):
    """Redirect to login or dashboard."""
    # Check if user has valid session
    session_token = request.cookies.get("admin_session")
    if session_token and session_token in admin_sessions:
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    return RedirectResponse(url="/admin/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page."""
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "error": None
    })


@router.post("/login", response_class=HTMLResponse)
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Process admin login."""
    # Check credentials
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        # Create session
        session_token = secrets.token_urlsafe(32)
        admin_sessions[session_token] = {
            "username": username,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=24)
        }
        
        # Redirect to dashboard with session cookie
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(
            key="admin_session",
            value=session_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400  # 24 hours
        )
        return response
    else:
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Invalid username or password"
        })


@router.get("/logout")
async def admin_logout(request: Request):
    """Admin logout."""
    session_token = request.cookies.get("admin_session")
    if session_token and session_token in admin_sessions:
        del admin_sessions[session_token]
    
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_session")
    return response


def get_admin_user_from_session(request: Request):
    """Get admin user from session."""
    session_token = request.cookies.get("admin_session")
    if not session_token or session_token not in admin_sessions:
        return None
    
    session_data = admin_sessions[session_token]
    
    # Check if session is expired
    if datetime.now() > session_data["expires_at"]:
        del admin_sessions[session_token]
        return None
    
    return {"username": session_data["username"]}


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Admin dashboard."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return RedirectResponse(url="/admin/login", status_code=302)
    
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
    db: AsyncSession = Depends(get_db)
):
    """Users management page."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    users_result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = users_result.scalars().all()
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "admin_user": admin_user,
        "users": users
    })


@router.get("/user-account/{user_id}")
async def admin_user_account(user_id: str, request: Request):
    """Individual user account page."""
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>User Account - {user_id}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-3 col-lg-2 sidebar p-3" style="background-color: #f8f9fa; min-height: 100vh;">
                    <h4 class="mb-4">
                        <i class="bi bi-robot"></i>
                        Assistant Admin
                    </h4>
                    <nav class="nav flex-column">
                        <a class="nav-link" href="/admin">
                            <i class="bi bi-speedometer2"></i> Dashboard
                        </a>
                        <a class="nav-link active" href="/admin/users">
                            <i class="bi bi-people"></i> Users
                        </a>
                        <a class="nav-link" href="/admin/testing">
                            <i class="bi bi-bug"></i> Testing
                        </a>
                    </nav>
                    <div class="mt-4 pt-4 border-top">
                        <small class="text-muted">
                            Logged in as: admin
                        </small>
                        <div class="mt-2">
                            <a href="/admin/logout" class="btn btn-outline-danger btn-sm">
                                <i class="bi bi-box-arrow-right"></i> Logout
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-9 col-lg-10 main-content" style="padding: 20px;">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <div>
                            <nav aria-label="breadcrumb">
                                <ol class="breadcrumb">
                                    <li class="breadcrumb-item"><a href="/admin">Admin</a></li>
                                    <li class="breadcrumb-item"><a href="/admin/users">Users</a></li>
                                    <li class="breadcrumb-item active" aria-current="page">User Account</li>
                                </ol>
                            </nav>
                            <h1><i class="bi bi-person-circle"></i> User Account</h1>
                            <p class="text-muted">User ID: {user_id}</p>
                        </div>
                        <div>
                            <a href="/admin/users" class="btn btn-outline-secondary">
                                <i class="bi bi-arrow-left"></i> Back to Users
                            </a>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0"><i class="bi bi-person"></i> User Information</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>User ID:</strong> {user_id}</p>
                                    <p><strong>Status:</strong> <span class="badge bg-success">Active</span></p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Account Type:</strong> Standard User</p>
                                    <p><strong>Last Activity:</strong> Recently</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-header">
                            <h5 class="mb-0"><i class="bi bi-lightning"></i> Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2 d-md-block">
                                <button class="btn btn-primary" onclick="testUserEmail()">
                                    <i class="bi bi-envelope"></i> Test Email
                                </button>
                                <button class="btn btn-success" onclick="testUserCall()">
                                    <i class="bi bi-telephone"></i> Test Call
                                </button>
                                <button class="btn btn-info" onclick="testUserSMS()">
                                    <i class="bi bi-chat-dots"></i> Test SMS
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
        function testUserEmail() {{
            alert('Email test for user {user_id}');
        }}
        function testUserCall() {{
            alert('Call test for user {user_id}');
        }}
        function testUserSMS() {{
            alert('SMS test for user {user_id}');
        }}
        </script>
    </body>
    </html>
    """)






@router.get("/events", response_class=HTMLResponse)
async def admin_events(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Events management page."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return RedirectResponse(url="/admin/login", status_code=302)
    
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
    db: AsyncSession = Depends(get_db)
):
    """Notifications management page."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return RedirectResponse(url="/admin/login", status_code=302)
    
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
    db: AsyncSession = Depends(get_db)
):
    """Audit logs page."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return RedirectResponse(url="/admin/login", status_code=302)
    
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


# User management routes
@router.post("/users", response_class=HTMLResponse)
async def admin_create_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    try:
        # Get form data
        form_data = await request.form()
        
        # Create user data
        user_data = {
            "name": form_data.get("name"),
            "email": form_data.get("email"),
            "phone_e164": form_data.get("phone_e164") or None,
            "timezone": form_data.get("timezone", "UTC"),
            "channel_pref": form_data.get("channel_pref", "email"),
            "quiet_start": form_data.get("quiet_start", "21:00"),
            "quiet_end": form_data.get("quiet_end", "07:00"),
            "weekend_policy": form_data.get("weekend_policy", "email"),
            "locale": "en",
            "voice": "Polly.Joanna",
            "max_call_attempts": 3,
            "escalation_threshold": 60
        }
        
        # Validate and create user
        user_create = UserCreate(**user_data)
        user = User(
            **user_create.dict(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Redirect back to users page with success message
        return RedirectResponse(url="/admin/users?success=created", status_code=302)
        
    except Exception as e:
        # Redirect back with error message
        return RedirectResponse(url="/admin/users?error=create_failed", status_code=302)


@router.put("/users/{user_id}", response_class=HTMLResponse)
async def admin_update_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Update a user."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return RedirectResponse(url="/admin/users?error=user_not_found", status_code=302)
        
        # Get form data
        form_data = await request.form()
        
        # Update user data
        update_data = {}
        if form_data.get("name"):
            update_data["name"] = form_data.get("name")
        if form_data.get("email"):
            update_data["email"] = form_data.get("email")
        if form_data.get("phone_e164"):
            update_data["phone_e164"] = form_data.get("phone_e164")
        if form_data.get("timezone"):
            update_data["timezone"] = form_data.get("timezone")
        if form_data.get("channel_pref"):
            update_data["channel_pref"] = form_data.get("channel_pref")
        if form_data.get("quiet_start"):
            update_data["quiet_start"] = form_data.get("quiet_start")
        if form_data.get("quiet_end"):
            update_data["quiet_end"] = form_data.get("quiet_end")
        if form_data.get("weekend_policy"):
            update_data["weekend_policy"] = form_data.get("weekend_policy")
        
        # Apply updates
        for key, value in update_data.items():
            setattr(user, key, value)
        user.updated_at = datetime.now()
        
        await db.commit()
        
        # Redirect back to users page with success message
        return RedirectResponse(url="/admin/users?success=updated", status_code=302)
        
    except Exception as e:
        # Redirect back with error message
        return RedirectResponse(url="/admin/users?error=update_failed", status_code=302)


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Delete a user."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return JSONResponse({"success": False, "error": "Authentication required"})
    
    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return JSONResponse({"success": False, "error": "User not found"})
        
        # Delete user
        await db.delete(user)
        await db.commit()
        
        return {"success": True, "message": "User deleted successfully"}
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


@router.post("/users/{user_id}/test-call")
async def admin_test_call(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Test call for a user."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return JSONResponse({"success": False, "error": "Authentication required"})
    
    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return JSONResponse({"success": False, "error": "User not found"})
        
        # Make test call using testing endpoint
        from app.routes.testing import test_mock_call
        response = await test_mock_call(user_id, db)
        
        # Ensure response has success field
        if isinstance(response, dict) and 'message' in response:
            return {
                "success": True,
                "message": response.get('message', 'Call initiated successfully'),
                "data": response
            }
        else:
            return response
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


@router.post("/users/{user_id}/test-email")
async def admin_test_email(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Test email for a user."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return JSONResponse({"success": False, "error": "Authentication required"})
    
    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return JSONResponse({"success": False, "error": "User not found"})
        
        # Make test email using testing endpoint
        from app.routes.testing import test_mock_email
        response = await test_mock_email(user_id, db)
        
        # Ensure response has success field
        if isinstance(response, dict) and 'message' in response:
            return {
                "success": True,
                "message": response.get('message', 'Email sent successfully'),
                "data": response
            }
        else:
            return response
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


# Testing page route
@router.get("/testing", response_class=HTMLResponse)
async def admin_testing(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Testing dashboard page."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Get all users for testing
    users_result = await db.execute(select(User).order_by(User.name))
    users = users_result.scalars().all()
    
    return templates.TemplateResponse("admin/testing.html", {
        "request": request,
        "admin_user": admin_user,
        "users": users
    })


@router.post("/users/{user_id}/test-sms")
async def admin_test_sms(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Test SMS for a user."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return JSONResponse({"success": False, "error": "Authentication required"})
    
    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return JSONResponse({"success": False, "error": "User not found"})
        
        if not user.phone_e164:
            return {"success": False, "error": "User has no phone number configured"}
        
        # Create mock SMS response
        sms_data = {
            "message": "Test SMS from Personal Assistant",
            "to": user.phone_e164,
            "user": user.name,
            "message_id": f"mock-sms-{int(datetime.now().timestamp())}",
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "message": "SMS sent successfully",
            "data": sms_data
        }
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


@router.get("/testing/history")
async def admin_test_history(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get test history."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return JSONResponse({"success": False, "error": "Authentication required"})
    
    try:
        # Get recent notifications as test history
        notifications_result = await db.execute(
            select(Notification)
            .order_by(Notification.created_at.desc())
            .limit(50)
        )
        notifications = notifications_result.scalars().all()
        
        # Get recent audit logs
        audit_result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.action.like('%test%'))
            .order_by(AuditLog.created_at.desc())
            .limit(50)
        )
        audit_logs = audit_result.scalars().all()
        
        history = []
        
        # Add notifications to history
        for notification in notifications:
            history.append({
                "type": "notification",
                "channel": notification.channel,
                "status": notification.status,
                "timestamp": notification.created_at.isoformat(),
                "user_id": str(notification.user_id),
                "details": {
                    "plan_time": notification.plan_time.isoformat(),
                    "status": notification.status,
                    "attempts": notification.attempts
                }
            })
        
        # Add audit logs to history
        for log in audit_logs:
            history.append({
                "type": "audit",
                "action": log.action,
                "timestamp": log.created_at.isoformat(),
                "user_id": str(log.user_id) if log.user_id else None,
                "details": log.meta_json or {}
            })
        
        # Sort by timestamp
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "success": True,
            "history": history[:100]  # Limit to 100 items
        }
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


# User action endpoints for device emulation
@router.post("/users/{user_id}/call-action")
async def admin_call_action(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle call actions (answer/decline)."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return JSONResponse({"success": False, "error": "Authentication required"})
    
    try:
        # Get form data
        form_data = await request.form()
        action = form_data.get("action")  # "answer" or "decline"
        
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return JSONResponse({"success": False, "error": "User not found"})
        
        # Log the action
        from app.models import AuditLog
        audit_log = AuditLog(
            action=f"call_{action}",
            user_id=user.id,
            meta_json={"action": action, "timestamp": datetime.now().isoformat()},
            created_at=datetime.now()
        )
        db.add(audit_log)
        await db.commit()
        
        # Log to console for terminal visibility
        logger.info(f"User device interaction: Call {action}ed", 
                   user=user.name, 
                   phone=user.phone_e164, 
                   action=action)
        
        return JSONResponse({
            "success": True,
            "message": f"Call {action}ed successfully",
            "action": action,
            "user": user.name,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


@router.post("/users/{user_id}/email-action")
async def admin_email_action(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle email RSVP actions (confirm/reschedule/cancel)."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return JSONResponse({"success": False, "error": "Authentication required"})
    
    try:
        # Get form data
        form_data = await request.form()
        action = form_data.get("action")  # "confirm", "reschedule", "cancel"
        event_id = form_data.get("event_id", "test-event")
        
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return JSONResponse({"success": False, "error": "User not found"})
        
        # Log the action
        from app.models import AuditLog
        audit_log = AuditLog(
            action=f"email_{action}",
            user_id=user.id,
            meta_json={
                "action": action, 
                "event_id": event_id,
                "timestamp": datetime.now().isoformat()
            },
            created_at=datetime.now()
        )
        db.add(audit_log)
        await db.commit()
        
        # Log to console for terminal visibility
        logger.info(f"User device interaction: Email {action}ed", 
                   user=user.name, 
                   email=user.email, 
                   action=action, 
                   event_id=event_id)
        
        # Generate response message based on action
        messages = {
            "confirm": "Thank you for confirming your attendance!",
            "reschedule": "We'll help you reschedule your appointment.",
            "cancel": "Your appointment has been cancelled."
        }
        
        return JSONResponse({
            "success": True,
            "message": messages.get(action, "Action processed successfully"),
            "action": action,
            "user": user.name,
            "event_id": event_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


@router.post("/users/{user_id}/sms-response")
async def admin_sms_response(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle SMS responses from user."""
    # Check authentication
    admin_user = get_admin_user_from_session(request)
    if not admin_user:
        return JSONResponse({"success": False, "error": "Authentication required"})
    
    try:
        # Get form data
        form_data = await request.form()
        response_text = form_data.get("response", "")
        
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return JSONResponse({"success": False, "error": "User not found"})
        
        # Log the response
        from app.models import AuditLog
        audit_log = AuditLog(
            action="sms_response",
            user_id=user.id,
            meta_json={
                "response": response_text,
                "timestamp": datetime.now().isoformat()
            },
            created_at=datetime.now()
        )
        db.add(audit_log)
        await db.commit()
        
        # Log to console for terminal visibility
        logger.info(f"User device interaction: SMS response received", 
                   user=user.name, 
                   phone=user.phone_e164, 
                   response=response_text)
        
        return JSONResponse({
            "success": True,
            "message": "SMS response received and logged",
            "response": response_text,
            "user": user.name,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
