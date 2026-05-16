"""Cycle schemas."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CycleBase(BaseModel):
    """Base schema for organizational performance cycles.

    Attributes:
        name: Name of the performance cycle (e.g. 'FY2026-27').
        goal_setting_open: Start date for goal sheet creation.
        q1_open: Open date for Q1 review and check-ins.
        q2_open: Open date for Q2 review and check-ins.
        q3_open: Open date for Q3 review and check-ins.
        q4_open: Open date for Q4 review and check-ins.
    """
    name: str
    goal_setting_open: date
    q1_open: date
    q2_open: date
    q3_open: date
    q4_open: date


class CycleCreate(CycleBase):
    """Schema for initializing a new organizational performance appraisal cycle."""
    pass


class CycleUpdate(BaseModel):
    """Schema for modifying milestone dates or attributes of an existing cycle.

    Attributes:
        name: Optional updated cycle name.
        goal_setting_open: Optional updated goal setting open date.
        q1_open: Optional updated Q1 open date.
        q2_open: Optional updated Q2 open date.
        q3_open: Optional updated Q3 open date.
        q4_open: Optional updated Q4 open date.
    """
    name: Optional[str] = None
    goal_setting_open: Optional[date] = None
    q1_open: Optional[date] = None
    q2_open: Optional[date] = None
    q3_open: Optional[date] = None
    q4_open: Optional[date] = None


class CycleResponse(CycleBase):
    """Serialized performance cycle record.

    Attributes:
        id: Unique cycle UUID.
        is_active: True if currently active operating cycle.
        created_by: Administrator UUID who authored the cycle.
        created_at: ISO-8601 creation timestamp.
    """
    id: UUID
    is_active: bool
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True
