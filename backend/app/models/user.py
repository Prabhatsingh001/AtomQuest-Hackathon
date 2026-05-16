"""User model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(
        Enum("employee", "manager", "admin", name="user_role"),
        nullable=False,
    )
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    department_id = Column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    manager = relationship("User", remote_side="User.id", backref="direct_reports")
    department = relationship("Department", back_populates="users")
    goal_sheets = relationship(
        "GoalSheet", back_populates="employee", foreign_keys="GoalSheet.employee_id"
    )

    @property
    def department_name(self):
        return self.department.name if self.department else None
