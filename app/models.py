"""SQLAlchemy models for the appointment assistant."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, 
    ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    timezone = Column(String(50), default="UTC")
    phone_e164 = Column(String(20), nullable=True)
    email = Column(String(255), nullable=False, unique=True)
    quiet_start = Column(String(5), default="21:00")  # HH:MM format
    quiet_end = Column(String(5), default="07:00")    # HH:MM format
    channel_pref = Column(String(20), default="email")  # email, call, both
    locale = Column(String(10), default="en")
    voice = Column(String(50), default="Polly.Joanna")
    max_call_attempts = Column(Integer, default=3)
    weekend_policy = Column(String(20), default="email")  # email, call, both, none
    escalation_threshold = Column(Integer, default=60)  # minutes before meeting
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    rules = relationship("Rule", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class OAuthAccount(Base):
    """OAuth account for calendar providers."""
    __tablename__ = "oauth_accounts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # google, microsoft
    access_token_enc = Column(Text, nullable=False)  # encrypted
    refresh_token_enc = Column(Text, nullable=True)  # encrypted
    expires_at = Column(DateTime(timezone=True), nullable=True)
    scope = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="oauth_accounts")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )


class Event(Base):
    """Calendar event model."""
    __tablename__ = "events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # google, microsoft
    provider_event_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    start_ts = Column(DateTime(timezone=True), nullable=False)
    end_ts = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(500), nullable=True)
    conf_link = Column(String(1000), nullable=True)
    organizer = Column(String(255), nullable=True)
    attendees = Column(JSON, nullable=True)  # List of attendee objects
    description = Column(Text, nullable=True)
    status = Column(String(20), default="confirmed")  # confirmed, tentative, cancelled
    etag = Column(String(255), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    hash = Column(String(64), nullable=True)  # For change detection
    
    # Relationships
    user = relationship("User", back_populates="events")
    notifications = relationship("Notification", back_populates="event", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_events_user_start", "user_id", "start_ts"),
        Index("idx_events_provider", "provider", "provider_event_id"),
        UniqueConstraint("user_id", "provider", "provider_event_id", name="uq_user_provider_event"),
    )


class Notification(Base):
    """Notification plan and execution tracking."""
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("events.id"), nullable=False)
    channel = Column(String(20), nullable=False)  # email, call
    plan_time = Column(DateTime(timezone=True), nullable=False)
    sent_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="planned")  # planned, sent, delivered, failed, cancelled
    result = Column(JSON, nullable=True)  # Response data from provider
    attempts = Column(Integer, default=0)
    payload = Column(JSON, nullable=True)  # Notification content
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    event = relationship("Event", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index("idx_notifications_plan_time", "plan_time"),
        Index("idx_notifications_status", "status"),
        Index("idx_notifications_user_event", "user_id", "event_id"),
    )


class Rule(Base):
    """User notification rules."""
    __tablename__ = "rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rule_type = Column(String(50), nullable=False)  # vip_organizer, internal_meeting, travel_buffer, etc.
    rule_json = Column(JSON, nullable=False)  # Rule configuration
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority rules override lower ones
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="rules")
    
    # Indexes
    __table_args__ = (
        Index("idx_rules_user_type", "user_id", "rule_type"),
        Index("idx_rules_priority", "priority"),
    )


class AuditLog(Base):
    """Audit trail for all actions."""
    __tablename__ = "audit_log"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    event_id = Column(String(36), ForeignKey("events.id"), nullable=True)
    action = Column(String(100), nullable=False)  # confirm, cancel, reschedule, call_placed, email_sent, etc.
    meta_json = Column(JSON, nullable=True)  # Additional metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_created_at", "created_at"),
    )
