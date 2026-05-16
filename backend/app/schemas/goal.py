"""Goal-related schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class GoalBase(BaseModel):
    thrust_area: str
    title: str
    description: Optional[str] = None
    uom_type: str  # min, max, timeline, zero
    target_value: Optional[Decimal] = None
    target_date: Optional[date] = None
    weightage: Decimal = Field(..., ge=10, le=100)

    @field_validator("weightage")
    @classmethod
    def validate_weightage(cls, v):
        if v < 10:
            raise ValueError("Minimum weightage per goal is 10%")
        if v > 100:
            raise ValueError("Weightage cannot exceed 100%")
        return v

    @field_validator("uom_type")
    @classmethod
    def validate_uom_type(cls, v):
        if v not in ("min", "max", "timeline", "zero"):
            raise ValueError("UoM type must be one of: min, max, timeline, zero")
        return v


class GoalCreate(GoalBase):
    goal_sheet_id: UUID


class GoalUpdate(BaseModel):
    thrust_area: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    uom_type: Optional[str] = None
    target_value: Optional[Decimal] = None
    target_date: Optional[date] = None
    weightage: Optional[Decimal] = None


class GoalResponse(BaseModel):
    id: UUID
    goal_sheet_id: UUID
    thrust_area: str
    title: str
    description: Optional[str]
    uom_type: str
    target_value: Optional[Decimal]
    target_date: Optional[date]
    weightage: Decimal
    is_shared: bool
    parent_goal_id: Optional[UUID]
    order_index: int
    created_at: datetime
    updated_at: datetime
    achievements: List["GoalAchievementResponse"] = []

    class Config:
        from_attributes = True


class GoalSheetResponse(BaseModel):
    id: UUID
    employee_id: UUID
    cycle_id: UUID
    status: str
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    approved_by: Optional[UUID]
    is_locked: bool
    total_weightage: Decimal
    created_at: datetime
    updated_at: datetime
    goals: List[GoalResponse] = []
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None

    class Config:
        from_attributes = True


class GoalAchievementResponse(BaseModel):
    id: UUID
    goal_id: UUID
    cycle_id: UUID
    quarter: str
    actual_value: Optional[Decimal]
    completion_date: Optional[date]
    status: str
    computed_score: Optional[Decimal]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class GoalAchievementUpdate(BaseModel):
    actual_value: Optional[Decimal] = None
    completion_date: Optional[date] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ("not_started", "on_track", "completed"):
            raise ValueError(
                "Achievement status must be one of: not_started, on_track, completed"
            )
        return v


class SharedGoalPush(BaseModel):
    goal_template: GoalBase
    employee_ids: List[UUID]


# Update forward references
GoalResponse.model_rebuild()
