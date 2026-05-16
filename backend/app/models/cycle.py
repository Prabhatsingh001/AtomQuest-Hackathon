"""Cycle model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Cycle(Base):
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
