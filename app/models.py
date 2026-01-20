"""SQLAlchemy models for the appointment assistant."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, 
    ForeignKey, JSON, Index, UniqueConstraint, LargeBinary
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


class Mindmap(Base):
    """Mind map model."""
    __tablename__ = "mindmaps"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, default="Untitled Mind Map")
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Optional for now
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    nodes = relationship("MindmapNode", back_populates="mindmap", cascade="all, delete-orphan", order_by="MindmapNode.created_at")
    
    # Indexes
    __table_args__ = (
        Index("idx_mindmaps_owner", "owner_id"),
        Index("idx_mindmaps_updated", "updated_at"),
    )


class MindmapNode(Base):
    """Mind map node model."""
    __tablename__ = "mindmap_nodes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mindmap_id = Column(String(36), ForeignKey("mindmaps.id"), nullable=False)
    parent_id = Column(String(36), ForeignKey("mindmap_nodes.id"), nullable=True)
    x = Column(Integer, nullable=False, default=0)
    y = Column(Integer, nullable=False, default=0)
    text = Column(Text, nullable=False, default="")
    color = Column(String(7), nullable=False, default="#ffffff")  # Hex color
    text_color = Column(String(7), nullable=False, default="#000000")  # Hex color
    shape = Column(String(20), nullable=False, default="rect")  # rect, pill
    width = Column(Integer, nullable=True)  # Auto-calculated if None
    height = Column(Integer, nullable=True)  # Auto-calculated if None
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mindmap = relationship("Mindmap", back_populates="nodes")
    parent = relationship("MindmapNode", remote_side=[id], backref="children")
    
    # Indexes
    __table_args__ = (
        Index("idx_nodes_mindmap", "mindmap_id"),
        Index("idx_nodes_parent", "parent_id"),
    )


class BookProject(Base):
    """Book project model."""
    __tablename__ = "book_projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, default="Untitled Book")
    initial_prompt = Column(Text, nullable=True)
    num_chapters = Column(Integer, default=25)
    status = Column(String(20), default="draft")  # draft, outline_generating, outline_complete, generating, complete, error
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    outline = relationship("BookOutline", back_populates="project", uselist=False, cascade="all, delete-orphan")
    chapters = relationship("BookChapter", back_populates="project", cascade="all, delete-orphan", order_by="BookChapter.chapter_number")
    
    # Indexes
    __table_args__ = (
        Index("idx_books_status", "status"),
        Index("idx_books_updated", "updated_at"),
    )


class BookOutline(Base):
    """Book outline model."""
    __tablename__ = "book_outlines"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("book_projects.id"), nullable=False, unique=True)
    outline_data = Column(JSON, nullable=False)  # List of chapter outlines
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("BookProject", back_populates="outline")
    
    # Indexes
    __table_args__ = (
        Index("idx_outline_project", "project_id"),
    )


class BookChapter(Base):
    """Book chapter model."""
    __tablename__ = "book_chapters"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("book_projects.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    prompt = Column(Text, nullable=True)  # Original chapter prompt from outline
    status = Column(String(20), default="pending")  # pending, generating, complete, error
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("BookProject", back_populates="chapters")
    
    # Indexes
    __table_args__ = (
        Index("idx_chapters_project", "project_id"),
        Index("idx_chapters_number", "project_id", "chapter_number"),
        UniqueConstraint("project_id", "chapter_number", name="uq_project_chapter"),
    )


class BookPublishingHouseProject(Base):
    """Book Publishing House project model for persistence."""
    __tablename__ = "book_publishing_house_projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    premise = Column(Text, nullable=False)
    target_word_count = Column(Integer, nullable=True)
    audience = Column(String(255), nullable=True)
    output_directory = Column(String(255), default="book_outputs")
    model = Column(String(50), default="qwen3:30b")  # Worker agent model
    ceo_model = Column(String(50), nullable=True)  # CEO/manager model
    
    # Project state
    current_phase = Column(String(50), default="strategy_concept")
    status = Column(String(50), default="in_progress")  # in_progress, complete, stopped, error
    
    # Project data (stored as JSON for flexibility)
    project_data = Column(JSON, nullable=True)  # Full BookProject state
    artifacts = Column(JSON, nullable=True)  # Phase artifacts
    owner_decisions = Column(JSON, nullable=True)  # Owner decisions per phase
    chat_log = Column(JSON, nullable=True)  # Agent communication log
    
    # Progress tracking
    progress_log = Column(JSON, nullable=True)  # List of progress entries with timestamps
    error_log = Column(JSON, nullable=True)  # List of errors with timestamps
    
    # Reference documents
    reference_documents = Column(JSON, nullable=True)  # List of document IDs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_bph_status", "status"),
        Index("idx_bph_updated", "updated_at"),
        Index("idx_bph_phase", "current_phase"),
    )


class CoreDevicesProject(Base):
    """Core Devices Company project model for persistence."""
    __tablename__ = "core_devices_projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_idea = Column(Text, nullable=True)  # Now optional - Research Team can discover
    primary_need = Column(String(50), nullable=True)
    research_mode = Column(Boolean, default=False)  # If True, project starts with Research Phase
    research_scope = Column(Text, nullable=True)  # Research scope/focus areas
    constraints = Column(JSON, nullable=True)
    output_directory = Column(String(255), default="product_outputs")
    model = Column(String(50), default="qwen3:30b")  # Worker agent model
    ceo_model = Column(String(50), nullable=True)  # CEO/manager model
    
    # Research Team outputs
    pdf_report = Column(LargeBinary, nullable=True)  # PDF research report (binary)
    
    # Project state
    current_phase = Column(String(50), default="strategy_idea_intake")
    status = Column(String(50), default="in_progress")  # in_progress, complete, stopped, error
    
    # Project data (stored as JSON for flexibility)
    project_data = Column(JSON, nullable=True)  # Full ProductProject state
    artifacts = Column(JSON, nullable=True)  # Phase artifacts
    owner_decisions = Column(JSON, nullable=True)  # Owner decisions per phase
    chat_log = Column(JSON, nullable=True)  # Agent communication log
    
    # Progress tracking
    progress_log = Column(JSON, nullable=True)  # List of progress entries with timestamps
    error_log = Column(JSON, nullable=True)  # List of errors with timestamps
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_cdc_status", "status"),
        Index("idx_cdc_updated", "updated_at"),
        Index("idx_cdc_phase", "current_phase"),
    )


class ExamGeneratorProject(Base):
    """Exam Generator project model for persistence."""
    __tablename__ = "exam_generator_projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    input_file_path = Column(String(255), nullable=True)
    input_content = Column(Text, nullable=False)
    output_directory = Column(String(255), default="exam_outputs")
    model = Column(String(50), default="qwen3:30b")
    
    # Project state
    current_phase = Column(String(50), default="content_analysis")
    status = Column(String(50), default="in_progress")  # in_progress, generating, complete, error
    num_problems = Column(Integer, default=10)
    validation_iterations = Column(Integer, default=3)
    
    # Project data (stored as JSON for flexibility)
    project_data = Column(JSON, nullable=True)
    problems = Column(JSON, nullable=True)  # List of ExamProblem dicts
    validation_results = Column(JSON, nullable=True)  # List of validation results
    final_review = Column(JSON, nullable=True)  # Final review results
    output_files = Column(JSON, nullable=True)  # Dict of output file paths
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_eg_status", "status"),
        Index("idx_eg_updated", "updated_at"),
        Index("idx_eg_phase", "current_phase"),
    )
