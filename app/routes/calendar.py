"""Calendar integration routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, OAuthAccount
from app.calendar.google import GoogleCalendarClient
from app.security.tokens import encrypt_token
from app.deps import get_admin_user

router = APIRouter()


@router.get("/google/auth/{user_id}")
async def google_auth(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Initiate Google Calendar OAuth flow."""
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create Google Calendar client
    google_client = GoogleCalendarClient()
    
    # Generate state parameter
    import secrets
    state = secrets.token_urlsafe(32)
    
    # Store state in session or database (simplified for demo)
    # In production, use proper session management
    
    # Get authorization URL
    auth_url = google_client.get_auth_url(state)
    
    return {"auth_url": auth_url, "state": state}


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle Google Calendar OAuth callback."""
    try:
        # Create Google Calendar client
        google_client = GoogleCalendarClient()
        
        # Exchange code for tokens
        token_data = await google_client.exchange_code_for_tokens(code)
        
        # Get user info from Google (simplified - in production, get from state)
        # For demo purposes, we'll need to associate this with a user
        # In production, store the state parameter and retrieve user_id from it
        
        # For now, return success - in production, you'd:
        # 1. Validate the state parameter
        # 2. Get user_id from stored state
        # 3. Store encrypted tokens in OAuthAccount table
        # 4. Redirect to success page
        
        await google_client.close()
        
        return {"message": "OAuth successful", "tokens_received": True}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth failed: {str(e)}"
        )


@router.post("/google/sync/{user_id}")
async def sync_google_calendar(
    user_id: str,
    days_back: int = 2,
    days_forward: int = 30,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Sync Google Calendar events for a user."""
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get OAuth account
    oauth_result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == user_id,
            OAuthAccount.provider == "google"
        )
    )
    oauth_account = oauth_result.scalar_one_or_none()
    
    if not oauth_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Calendar not connected. Please complete OAuth flow first."
        )
    
    try:
        # Create Google Calendar client
        google_client = GoogleCalendarClient()
        
        # Decrypt access token
        from app.security.tokens import decrypt_token
        access_token = decrypt_token(oauth_account.access_token_enc)
        
        # Get events from Google Calendar
        from datetime import datetime, timedelta
        events = await google_client.get_events(
            access_token=access_token,
            time_min=datetime.utcnow() - timedelta(days=days_back),
            time_max=datetime.utcnow() + timedelta(days=days_forward)
        )
        
        # Process and store events
        events_created = 0
        events_updated = 0
        
        for google_event in events:
            # Normalize event
            normalized_event = google_client.normalize_event(google_event, user_id)
            
            # Check if event already exists
            from app.models import Event
            existing_result = await db.execute(
                select(Event).where(
                    Event.user_id == user_id,
                    Event.provider == "google",
                    Event.provider_event_id == normalized_event["provider_event_id"]
                )
            )
            existing_event = existing_result.scalar_one_or_none()
            
            if existing_event:
                # Update existing event
                for key, value in normalized_event.items():
                    if key != "user_id":  # Don't update user_id
                        setattr(existing_event, key, value)
                events_updated += 1
            else:
                # Create new event
                event = Event(**normalized_event)
                db.add(event)
                events_created += 1
        
        await db.commit()
        await google_client.close()
        
        return {
            "events_created": events_created,
            "events_updated": events_updated,
            "sync_time": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sync failed: {str(e)}"
        )
