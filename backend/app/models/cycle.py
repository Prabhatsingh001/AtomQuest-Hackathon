"""Cycle model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Cycle(Base):
    """SQLAlchemy model representing an organizational goal-setting and appraisal cycle.

    Attributes:
        id: Primary key UUID.
        name: Name of the performance cycle (e.g., 'FY2026').
        goal_setting_open: Start date when goal creation becomes permitted.
        q1_open: Opening date for Q1 milestone check-ins.
        q2_open: Opening date for Q2 milestone check-ins.
        q3_open: Opening date for Q3 milestone check-ins.
        q4_open: Opening date for Q4 milestone check-ins.
        is_active: Flag indicating if this is the currently enforced cycle.
        created_by: UUID of the administrator who configured the cycle.
        created_at: UTC creation timestamp.
    """
    __tablename__ = "cycles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    goal_setting_open = Column(Date, nullable=False)
    q1_open = Column(Date, nullable=False)
    q2_open = Column(Date, nullable=False)
    q3_open = Column(Date, nullable=False)
    q4_open = Column(Date, nullable=False)
    is_active = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
