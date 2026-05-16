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
    """SQLAlchemy model representing immutable system audit log records.

    Attributes:
        id: Primary key UUID.
        entity_type: Name of the audited table or entity domain.
        entity_id: UUID of the modified database record.
        action: Specific event or action identifier string.
        changed_by: UUID of the user who executed the operation.
        old_value: JSONB snapshot of state prior to modification.
        new_value: JSONB snapshot of state resulting from modification.
        reason: Optional text justification provided for the change.
        timestamp: UTC timestamp indicating precisely when the event occurred.
    """
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
    """SQLAlchemy model representing configurable automated escalation rules.

    Attributes:
        id: Primary key UUID.
        name: Human-readable descriptive name of the rule.
        trigger_event: Categorized event type that initiates evaluation.
        days_threshold: Duration in days after which unaddressed items escalate.
        notify_employee: Flag enabling direct email notification to the target employee.
        notify_manager: Flag enabling direct email notification to the target's manager.
        notify_hr: Flag enabling direct email notification to the HR department.
        is_active: Status flag controlling whether this rule actively evaluates.
    """
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
