"""Cycle schemas."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CycleBase(BaseModel):
    name: str
    goal_setting_open: date
    q1_open: date
    q2_open: date
    q3_open: date
    q4_open: date


class CycleCreate(CycleBase):
    pass


class CycleUpdate(BaseModel):
    name: Optional[str] = None
    goal_setting_open: Optional[date] = None
    q1_open: Optional[date] = None
    q2_open: Optional[date] = None
    q3_open: Optional[date] = None
    q4_open: Optional[date] = None


class CycleResponse(CycleBase):
    id: UUID
    is_active: bool
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True
