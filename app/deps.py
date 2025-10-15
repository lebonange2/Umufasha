"""Dependency injection for FastAPI."""
import redis.asyncio as redis
from typing import Optional, Generator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import get_db
from app.core.config import settings
from app.llm.client import LLMClient
from app.scheduling.scheduler import NotificationScheduler

# Security
security = HTTPBearer(auto_error=False)

# Redis connection
_redis: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis connection."""
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


# LLM client
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL
        )
    return _llm_client


# Scheduler
_scheduler: Optional[NotificationScheduler] = None


def get_scheduler() -> Optional[NotificationScheduler]:
    """Get notification scheduler."""
    global _scheduler
    if _scheduler is None and settings.SCHEDULER == "apscheduler":
        from app.scheduling.apscheduler import APSchedulerScheduler
        _scheduler = APSchedulerScheduler()
    return _scheduler


# Mock clients for testing
def get_twilio_client():
    """Get Twilio client (real or mock)."""
    if settings.MOCK_MODE or settings.MOCK_TWILIO:
        from app.telephony.mock import MockTwilioClient
        return MockTwilioClient()
    else:
        from app.telephony.twilio import TwilioClient
        return TwilioClient()


def get_sendgrid_client():
    """Get SendGrid client (real or mock)."""
    if settings.MOCK_MODE or settings.MOCK_SENDGRID:
        from app.email.mock import MockSendGridClient
        return MockSendGridClient()
    else:
        from app.email.sendgrid import SendGridClient
        return SendGridClient()


# Admin authentication
async def get_admin_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get admin user from credentials."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Simple admin authentication (in production, use proper auth)
    if (credentials.credentials == f"{settings.ADMIN_USERNAME}:{settings.ADMIN_PASSWORD}"):
        return {"username": settings.ADMIN_USERNAME}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )


# Optional admin authentication (for endpoints that work with or without auth)
async def get_optional_admin_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get admin user from credentials (optional)."""
    if not credentials:
        return None
    
    try:
        return await get_admin_user(credentials)
    except HTTPException:
        return None