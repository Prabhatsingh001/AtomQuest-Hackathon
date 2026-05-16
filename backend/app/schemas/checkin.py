"""Check-in schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


VALID_QUARTERS = {"q1", "q2", "q3", "q4", "annual"}


class CheckinCommentCreate(BaseModel):
    """Schema for submitting manager check-in qualitative feedback comments.

    Attributes:
        goal_sheet_id: Target goal sheet UUID.
        quarter: Target milestone period ('q1', 'q2', 'q3', 'q4', 'annual').
        comment: Non-empty qualitative feedback text.
    """
    goal_sheet_id: UUID
    quarter: str
    comment: str

    @field_validator("quarter")
    @classmethod
    def validate_quarter(cls, v: str) -> str:
        """Ensure provided quarter string matches approved milestone review identifiers.

        Args:
            v: Input quarter string.

        Returns:
            str: Normalized lowercased quarter string.

        Raises:
            ValueError: If an unrecognized quarter identifier is submitted.
        """
        quarter = v.lower()
        if quarter not in VALID_QUARTERS:
            raise ValueError("Quarter must be one of: q1, q2, q3, q4, annual")
        return quarter

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str) -> str:
        """Ensure the feedback comment is not empty after whitespace stripping.

        Args:
            v: Input comment string.

        Returns:
            str: Stripped comment text.

        Raises:
            ValueError: If the comment is completely empty.
        """
        comment = v.strip()
        if not comment:
            raise ValueError("Comment cannot be empty")
        return comment


class CheckinCommentResponse(BaseModel):
    """Serialized check-in comment payload with author metadata.

    Attributes:
        id: Unique comment record UUID.
        goal_sheet_id: Associated goal sheet UUID.
        quarter: Milestone review period.
        manager_id: Authoring manager UUID.
        comment: Feedback text.
        created_at: ISO-8601 creation timestamp.
        manager_name: Full display name of authoring manager.
    """
    id: UUID
    goal_sheet_id: UUID
    quarter: str
    manager_id: UUID
    comment: str
    created_at: datetime
    manager_name: Optional[str] = None

    class Config:
        from_attributes = True
