"""Goal-related schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class GoalBase(BaseModel):
    """Core parameters defining a measurable performance goal.

    Attributes:
        thrust_area: Organizational strategic category.
        title: Title string for the goal.
        description: Optional detailed description.
        uom_type: Unit of measurement classification ('min', 'max', 'timeline', 'zero').
        target_value: Optional numeric target threshold.
        target_date: Optional deadline date.
        weightage: Personal percentage weight allocation (must be between 10% and 100%).
    """
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
        """Validate that goal weightage adheres to minimum 10% and maximum 100% boundaries.

        Args:
            v: Input weightage decimal.

        Returns:
            Decimal: Verified weightage value.

        Raises:
            ValueError: If out of allowed bounds.
        """
        if v < 10:
            raise ValueError("Minimum weightage per goal is 10%")
        if v > 100:
            raise ValueError("Weightage cannot exceed 100%")
        return v

    @field_validator("uom_type")
    @classmethod
    def validate_uom_type(cls, v):
        """Verify that the unit of measurement type matches supported evaluation functions.

        Args:
            v: Input unit of measurement string.

        Returns:
            str: Verified unit classification.

        Raises:
            ValueError: If an unsupported unit type is submitted.
        """
        if v not in ("min", "max", "timeline", "zero"):
            raise ValueError("UoM type must be one of: min, max, timeline, zero")
        return v


class GoalCreate(GoalBase):
    """Schema for initializing a new performance goal within an employee goal sheet.

    Attributes:
        goal_sheet_id: Target goal sheet UUID.
    """
    goal_sheet_id: UUID


class GoalUpdate(BaseModel):
    """Schema for updating attributes of an existing unlocked goal.

    Attributes:
        thrust_area: Optional updated strategic category.
        title: Optional updated title.
        description: Optional updated description.
        uom_type: Optional updated UoM type.
        target_value: Optional updated numeric target.
        target_date: Optional updated deadline date.
        weightage: Optional updated percentage weightage.
    """
    thrust_area: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    uom_type: Optional[str] = None
    target_value: Optional[Decimal] = None
    target_date: Optional[date] = None
    weightage: Optional[Decimal] = None


class GoalResponse(BaseModel):
    """Serialized goal entity representation.

    Attributes:
        id: Unique goal UUID.
        goal_sheet_id: Associated goal sheet UUID.
        thrust_area: Strategic category.
        title: Goal title.
        description: Description text.
        uom_type: Unit of measurement classification.
        target_value: Numeric target threshold.
        target_date: Deadline date.
        weightage: Percentage weight allocation.
        is_shared: True if distributed organization-wide as a shared goal.
        parent_goal_id: Optional parent shared goal UUID if linked.
        order_index: Display sorting sequence.
        created_at: ISO-8601 creation timestamp.
        updated_at: ISO-8601 last modification timestamp.
        achievements: List of milestone achievement records.
    """
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
    """Serialized goal sheet container representation.

    Attributes:
        id: Unique goal sheet UUID.
        employee_id: Assigned employee UUID.
        cycle_id: Associated performance cycle UUID.
        status: State classification ('draft', 'submitted', 'approved', 'returned').
        submitted_at: Submission timestamp.
        approved_at: Approval timestamp.
        approved_by: Manager UUID who approved the sheet.
        is_locked: Protection lock flag preventing edits.
        total_weightage: Sum of personal goal weightages.
        created_at: ISO-8601 creation timestamp.
        updated_at: ISO-8601 last modification timestamp.
        goals: List of associated goals.
        employee_name: Employee full display name.
        employee_email: Employee email address.
    """
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
    """Serialized milestone achievement actuals record.

    Attributes:
        id: Unique achievement UUID.
        goal_id: Target goal UUID.
        cycle_id: Associated performance cycle UUID.
        quarter: Milestone review period.
        actual_value: Recorded actual numeric value.
        completion_date: Recorded completion date for timeline goals.
        status: Qualitative progress classification.
        computed_score: Normalized performance score (0.0 to 1.0).
        updated_at: Timestamp of last check-in update.
    """
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
    """Schema for recording milestone check-in actuals.

    Attributes:
        actual_value: Recorded numeric actual figure.
        completion_date: Recorded completion date.
        status: Qualitative status ('not_started', 'on_track', 'completed').
    """
    actual_value: Optional[Decimal] = None
    completion_date: Optional[date] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Validate qualitative status against approved achievement states.

        Args:
            v: Input status string.

        Returns:
            str: Verified status identifier.

        Raises:
            ValueError: If an unsupported status is provided.
        """
        if v is not None and v not in ("not_started", "on_track", "completed"):
            raise ValueError(
                "Achievement status must be one of: not_started, on_track, completed"
            )
        return v


class SharedGoalPush(BaseModel):
    """Schema for distributing a shared company goal template to multiple employees.

    Attributes:
        goal_template: Core goal parameter definitions.
        employee_ids: Target employee UUIDs.
    """
    goal_template: GoalBase
    employee_ids: List[UUID]


# Update forward references
GoalResponse.model_rebuild()
