"""Audit log and escalation rule models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    Enum,
    DateTime,
    Text,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(100), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EscalationRule(Base):
    __tablename__ = "escalation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    trigger_event = Column(
        Enum(
            "goal_not_submitted",
            "goal_not_approved",
            "checkin_not_done",
            name="trigger_event_enum",
        ),
        nullable=False,
    )
    days_threshold = Column(Integer, nullable=False)
    notify_employee = Column(Boolean, default=True)
    notify_manager = Column(Boolean, default=True)
    notify_hr = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
