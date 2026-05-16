"""Check-in schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


VALID_QUARTERS = {"q1", "q2", "q3", "q4", "annual"}


class CheckinCommentCreate(BaseModel):
    goal_sheet_id: UUID
    quarter: str
    comment: str

    @field_validator("quarter")
    @classmethod
    def validate_quarter(cls, v: str) -> str:
        quarter = v.lower()
        if quarter not in VALID_QUARTERS:
            raise ValueError("Quarter must be one of: q1, q2, q3, q4, annual")
        return quarter

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str) -> str:
        comment = v.strip()
        if not comment:
            raise ValueError("Comment cannot be empty")
        return comment


class CheckinCommentResponse(BaseModel):
    id: UUID
    goal_sheet_id: UUID
    quarter: str
    manager_id: UUID
    comment: str
    created_at: datetime
    manager_name: Optional[str] = None

    class Config:
        from_attributes = True
