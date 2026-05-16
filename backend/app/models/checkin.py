"""Check-in comment model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Enum, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CheckinComment(Base):
    """SQLAlchemy model representing qualitative feedback or comments submitted during check-ins.

    Attributes:
        id: Primary key UUID.
        goal_sheet_id: Associated goal sheet UUID.
        quarter: Target review period or milestone identifier.
        manager_id: UUID of the manager or user authoring the comment.
        comment: Rich text content of the submitted feedback.
        created_at: UTC timestamp when the comment was recorded.
        goal_sheet: Relationship back to parent GoalSheet entity.
        manager: Relationship back to authoring User entity.
    """
    __tablename__ = "checkin_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_sheet_id = Column(
        UUID(as_uuid=True), ForeignKey("goal_sheets.id"), nullable=False
    )
    quarter = Column(
        Enum("q1", "q2", "q3", "q4", "annual", name="quarter_enum", create_type=False),
        nullable=False,
    )
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    goal_sheet = relationship("GoalSheet", back_populates="comments")
    manager = relationship("User")
