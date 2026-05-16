"""Department model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Department(Base):
    """SQLAlchemy model representing an organizational unit or department.

    Attributes:
        id: Primary key UUID.
        name: Unique descriptive name of the department.
        is_active: Status flag indicating if the department is active.
        created_at: UTC creation timestamp.
        updated_at: UTC modification timestamp.
        users: Relationship matching all employees assigned to this department.
    """
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    users = relationship("User", back_populates="department")
