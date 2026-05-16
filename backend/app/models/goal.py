"""Goal-related models: GoalSheet, Goal, GoalAchievement."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    Enum,
    DateTime,
    Date,
    Integer,
    Text,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class GoalSheet(Base):
    __tablename__ = "goal_sheets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cycle_id = Column(UUID(as_uuid=True), ForeignKey("cycles.id"), nullable=False)
    status = Column(
        Enum("draft", "submitted", "approved", "returned", name="sheet_status"),
        default="draft",
    )
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_locked = Column(Boolean, default=False)
    total_weightage = Column(Numeric(5, 2), default=Decimal("0.00"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("employee_id", "cycle_id", name="uq_employee_cycle"),
    )

    # Relationships
    employee = relationship(
        "User", back_populates="goal_sheets", foreign_keys=[employee_id]
    )
    approver = relationship("User", foreign_keys=[approved_by])
    cycle = relationship("Cycle")
    goals = relationship(
        "Goal", back_populates="goal_sheet", cascade="all, delete-orphan"
    )
    comments = relationship("CheckinComment", back_populates="goal_sheet")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_sheet_id = Column(
        UUID(as_uuid=True), ForeignKey("goal_sheets.id"), nullable=False
    )
    thrust_area = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    uom_type = Column(
        Enum("min", "max", "timeline", "zero", name="uom_type"),
        nullable=False,
    )
    target_value = Column(Numeric(15, 4), nullable=True)
    target_date = Column(Date, nullable=True)
    weightage = Column(Numeric(5, 2), nullable=False)
    is_shared = Column(Boolean, default=False)
    parent_goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    goal_sheet = relationship("GoalSheet", back_populates="goals")
    parent_goal = relationship("Goal", remote_side="Goal.id", backref="linked_goals")
    achievements = relationship(
        "GoalAchievement", back_populates="goal", cascade="all, delete-orphan"
    )


class GoalAchievement(Base):
    __tablename__ = "goal_achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False)
    cycle_id = Column(UUID(as_uuid=True), ForeignKey("cycles.id"), nullable=False)
    quarter = Column(
        Enum("q1", "q2", "q3", "q4", "annual", name="quarter_enum"),
        nullable=False,
    )
    actual_value = Column(Numeric(15, 4), nullable=True)
    completion_date = Column(Date, nullable=True)
    status = Column(
        Enum("not_started", "on_track", "completed", name="achievement_status"),
        default="not_started",
    )
    computed_score = Column(Numeric(5, 4), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (UniqueConstraint("goal_id", "quarter", name="uq_goal_quarter"),)

    # Relationships
    goal = relationship("Goal", back_populates="achievements")
    cycle = relationship("Cycle")
