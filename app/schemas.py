"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID


# User schemas
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    timezone: str = Field(default="UTC")
    phone_e164: Optional[str] = Field(None, pattern=r'^\+[1-9]\d{1,14}$')
    email: EmailStr
    quiet_start: str = Field(default="21:00", pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    quiet_end: str = Field(default="07:00", pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    channel_pref: Literal["email", "call", "both"] = Field(default="email")
    locale: str = Field(default="en")
    voice: str = Field(default="Polly.Joanna")
    max_call_attempts: int = Field(default=3, ge=1, le=10)
    weekend_policy: Literal["email", "call", "both", "none"] = Field(default="email")
    escalation_threshold: int = Field(default=60, ge=1, le=1440)  # minutes


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    timezone: Optional[str] = None
    phone_e164: Optional[str] = Field(None, pattern=r'^\+[1-9]\d{1,14}$')
    email: Optional[EmailStr] = None
    quiet_start: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    quiet_end: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    channel_pref: Optional[Literal["email", "call", "both"]] = None
    locale: Optional[str] = None
    voice: Optional[str] = None
    max_call_attempts: Optional[int] = Field(None, ge=1, le=10)
    weekend_policy: Optional[Literal["email", "call", "both", "none"]] = None
    escalation_threshold: Optional[int] = Field(None, ge=1, le=1440)


class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Event schemas
class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    start_ts: datetime
    end_ts: datetime
    location: Optional[str] = Field(None, max_length=500)
    conf_link: Optional[str] = Field(None, max_length=1000)
    organizer: Optional[str] = Field(None, max_length=255)
    attendees: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    status: Literal["confirmed", "tentative", "cancelled"] = Field(default="confirmed")


class EventCreate(EventBase):
    provider: str = Field(..., min_length=1, max_length=50)
    provider_event_id: str = Field(..., min_length=1, max_length=255)


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    start_ts: Optional[datetime] = None
    end_ts: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=500)
    conf_link: Optional[str] = Field(None, max_length=1000)
    organizer: Optional[str] = Field(None, max_length=255)
    attendees: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    status: Optional[Literal["confirmed", "tentative", "cancelled"]] = None


class Event(EventBase):
    id: UUID
    user_id: UUID
    provider: str
    provider_event_id: str
    etag: Optional[str] = None
    last_seen_at: datetime
    hash: Optional[str] = None
    
    class Config:
        from_attributes = True


# Notification schemas
class NotificationBase(BaseModel):
    channel: Literal["email", "call"]
    plan_time: datetime
    payload: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    user_id: UUID
    event_id: UUID


class NotificationUpdate(BaseModel):
    status: Optional[Literal["planned", "sent", "delivered", "failed", "cancelled"]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Notification(NotificationBase):
    id: UUID
    user_id: UUID
    event_id: UUID
    sent_time: Optional[datetime] = None
    status: str
    result: Optional[Dict[str, Any]] = None
    attempts: int
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Rule schemas
class RuleBase(BaseModel):
    rule_type: str = Field(..., min_length=1, max_length=50)
    rule_json: Dict[str, Any]
    enabled: bool = Field(default=True)
    priority: int = Field(default=0, ge=0, le=100)


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    rule_type: Optional[str] = Field(None, min_length=1, max_length=50)
    rule_json: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=100)


class Rule(RuleBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# OAuth schemas
class OAuthAccountBase(BaseModel):
    provider: str = Field(..., min_length=1, max_length=50)
    scope: Optional[str] = None


class OAuthAccountCreate(OAuthAccountBase):
    pass


class OAuthAccount(OAuthAccountBase):
    id: UUID
    user_id: UUID
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Audit log schemas
class AuditLogBase(BaseModel):
    action: str = Field(..., min_length=1, max_length=100)
    meta_json: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    user_id: Optional[UUID] = None
    event_id: Optional[UUID] = None


class AuditLog(AuditLogBase):
    id: UUID
    user_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# API response schemas
class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    success: bool = False


# Calendar sync schemas
class CalendarSyncRequest(BaseModel):
    user_id: UUID
    provider: str = Field(..., min_length=1, max_length=50)
    days_back: int = Field(default=2, ge=0, le=30)
    days_forward: int = Field(default=30, ge=1, le=90)


class CalendarSyncResponse(BaseModel):
    events_created: int
    events_updated: int
    events_deleted: int
    sync_time: datetime


# Notification planning schemas
class NotificationPlanRequest(BaseModel):
    user_id: UUID
    event_id: Optional[UUID] = None  # If None, plan for all events
    force_replan: bool = Field(default=False)


class NotificationPlanResponse(BaseModel):
    notifications_planned: int
    plan_time: datetime


# RSVP schemas
class RSVPRequest(BaseModel):
    action: Literal["confirm", "cancel", "reschedule"]
    new_time: Optional[datetime] = None  # For reschedule
    reason: Optional[str] = None


class RSVPResponse(BaseModel):
    success: bool
    message: str
    event_updated: bool = False


# LLM policy schemas
class PolicyRequest(BaseModel):
    event: Dict[str, Any]
    user_preferences: Dict[str, Any]
    history: Optional[List[Dict[str, Any]]] = None
    location: Optional[str] = None
    timezone: str = "UTC"


class PolicyResponse(BaseModel):
    plan: List[Dict[str, Any]]
    reasoning: Optional[str] = None


# Webhook schemas
class TwilioWebhook(BaseModel):
    CallSid: str
    From: str
    To: str
    CallStatus: str
    Direction: str
    Digits: Optional[str] = None
    AnsweredBy: Optional[str] = None


class GoogleWebhook(BaseModel):
    headers: Dict[str, str]
    body: Dict[str, Any]
