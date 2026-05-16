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
    """SQLAlchemy model representing an employee's performance container for a specific cycle.

    Attributes:
        id: Primary key UUID.
        employee_id: Owner employee UUID.
        cycle_id: Associated performance cycle UUID.
        status: Current workflow state ('draft', 'submitted', 'approved', 'returned').
        submitted_at: UTC timestamp when submitted for review.
        approved_at: UTC timestamp when approved by manager.
        approved_by: Manager UUID who executed approval.
        is_locked: Protection flag preventing unauthorized employee modifications.
        total_weightage: Aggregate percentage sum of assigned goals.
        created_at: UTC creation timestamp.
        updated_at: UTC modification timestamp.
        employee: Relationship back to owner User entity.
        approver: Relationship back to approver User entity.
        cycle: Relationship back to active Cycle entity.
        goals: List of associated Goal entities.
        comments: List of check-in and review comments.
    """
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
    """SQLAlchemy model representing an individual measurable performance goal.

    Attributes:
        id: Primary key UUID.
        goal_sheet_id: Associated goal sheet UUID.
        thrust_area: Domain categorization (e.g., 'Financial', 'Innovation').
        title: Short title summarizing the target objective.
        description: Detailed breakdown of the goal requirements.
        uom_type: Unit of measurement type ('min', 'max', 'timeline', 'zero').
        target_value: Target numeric threshold to achieve.
        target_date: Target completion deadline date.
        weightage: Percentage allocation towards overall sheet performance.
        is_shared: Flag indicating if this is an organizationally shared goal.
        parent_goal_id: Reference UUID if linked to an upstream shared goal.
        order_index: Display ordering index.
        created_at: UTC creation timestamp.
        updated_at: UTC modification timestamp.
        goal_sheet: Relationship back to parent GoalSheet entity.
        parent_goal: Self-referential relationship back to parent Goal entity.
        achievements: List of milestone check-in records.
    """
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

    goal_sheet = relationship("GoalSheet", back_populates="goals")
    parent_goal = relationship("Goal", remote_side="Goal.id", backref="linked_goals")
    achievements = relationship(
        "GoalAchievement", back_populates="goal", cascade="all, delete-orphan"
    )


class GoalAchievement(Base):
    """SQLAlchemy model representing milestone check-in progress records.

    Attributes:
        id: Primary key UUID.
        goal_id: Associated goal UUID.
        cycle_id: Active performance cycle UUID.
        quarter: Target milestone period ('q1', 'q2', 'q3', 'q4', 'annual').
        actual_value: Recorded numeric actual value.
        completion_date: Recorded completion date for timeline goals.
        status: Evaluated status ('not_started', 'on_track', 'completed').
        computed_score: Normalized performance score calculated between 0 and 1.
        updated_by: UUID of the user who recorded the check-in.
        updated_at: UTC timestamp of check-in submission.
        goal: Relationship back to parent Goal entity.
        cycle: Relationship back to Cycle entity.
    """
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

    goal = relationship("Goal", back_populates="achievements")
    cycle = relationship("Cycle")
