"""Department schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DepartmentBase(BaseModel):
    """Base organizational department schema.

    Attributes:
        name: Unique name of the department (e.g. 'Engineering', 'Human Resources').
    """
    name: str


class DepartmentCreate(DepartmentBase):
    """Schema for creating a new organizational department."""
    pass


class DepartmentUpdate(BaseModel):
    """Schema for updating department attributes or active status.

    Attributes:
        name: Optional updated department name.
        is_active: Optional activation toggle flag.
    """
    name: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    """Serialized department record payload.

    Attributes:
        id: Unique department UUID.
        name: Department name.
        is_active: Status flag indicating whether employees can be assigned.
        created_at: ISO-8601 creation timestamp.
        updated_at: ISO-8601 last modification timestamp.
        employee_count: Aggregated count of active assigned employees.
    """
    id: UUID
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    employee_count: Optional[int] = None

    class Config:
        from_attributes = True
