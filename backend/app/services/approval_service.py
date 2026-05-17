"""Approval service — business logic for goal sheet approval workflow."""

from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.goal import GoalSheet, Goal
from app.models.user import User
from app.services.audit_service import log_audit


def get_approval_queue(db: Session, manager: User) -> List[GoalSheet]:
    """Retrieve all submitted goal sheets waiting for manager review.

    Args:
        db: Active database session.
        manager: The supervising manager or administrator entity.

    Returns:
        List[GoalSheet]: A list of goal sheets currently in 'submitted' status.
    """
    query = (
        db.query(GoalSheet)
        .join(User, GoalSheet.employee_id == User.id)
        .filter(GoalSheet.status == "submitted")
    )
    if manager.role != "admin": # type: ignore
        query = query.filter(User.manager_id == manager.id)
    return query.all()


def get_team_sheets(
    db: Session, manager: User, statuses: list = None # type: ignore
) -> List[GoalSheet]:
    """Retrieve goal sheets for all direct reports, optionally filtered by status.

    Args:
        db: Active database session.
        manager: The supervising manager or administrator entity.
        statuses: Optional list of status strings to filter matching sheets.

    Returns:
        List[GoalSheet]: A list of matching team goal sheets.
    """
    query = db.query(GoalSheet).join(User, GoalSheet.employee_id == User.id)
    if manager.role != "admin": # type: ignore
        query = query.filter(User.manager_id == manager.id)
    if statuses:
        query = query.filter(GoalSheet.status.in_(statuses))
    return query.all()


def approve_sheet(db: Session, sheet_id: UUID, manager: User) -> GoalSheet:
    """Approve an employee's submitted goal sheet and lock it.

    Args:
        db: Active database session.
        sheet_id: Target goal sheet UUID.
        manager: The manager or administrator executing the approval.

    Returns:
        GoalSheet: The successfully approved and locked goal sheet.

    Raises:
        HTTPException: If the sheet is not found, unauthorized, or not submitted.
    """
    sheet = db.query(GoalSheet).filter(GoalSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")

    employee = db.query(User).filter(User.id == sheet.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if manager.role != "admin" and employee.manager_id != manager.id: # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only approve sheets of your direct reports",
        )

    if sheet.status != "submitted": # type: ignore
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only submitted sheets can be approved",
        )

    sheet.status = "approved" # type: ignore
    sheet.is_locked = True # type: ignore
    sheet.approved_by = manager.id
    sheet.approved_at = datetime.utcnow()

    log_audit(
        db,
        "goal_sheet",
        sheet.id,
        "goal_sheet.approved",
        manager.id,
        {"status": "submitted"},
        {"status": "approved", "is_locked": True},
    )

    db.commit()
    db.refresh(sheet)
    return sheet


def return_sheet(db: Session, sheet_id: UUID, manager: User, comment: str) -> GoalSheet:
    """Return a submitted goal sheet to an employee for revisions.

    Args:
        db: Active database session.
        sheet_id: Target goal sheet UUID.
        manager: The manager or administrator returning the sheet.
        comment: Rationale or feedback describing required revisions.

    Returns:
        GoalSheet: The goal sheet updated to 'returned' status.

    Raises:
        HTTPException: If the sheet is not found, unauthorized, or not submitted.
    """
    sheet = db.query(GoalSheet).filter(GoalSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")

    employee = db.query(User).filter(User.id == sheet.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if manager.role != "admin" and employee.manager_id != manager.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only return sheets of your direct reports",
        )

    if sheet.status != "submitted":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only submitted sheets can be returned",
        )

    sheet.status = "returned"

    log_audit(
        db,
        "goal_sheet",
        sheet.id,
        "goal_sheet.returned",
        manager.id,
        {"status": "submitted"},
        {"status": "returned", "comment": comment},
    )

    from app.models.checkin import CheckinComment

    return_comment = CheckinComment(
        goal_sheet_id=sheet.id,
        quarter="q1",
        manager_id=manager.id,
        comment=f"[RETURNED] {comment}",
    )
    db.add(return_comment)

    db.commit()
    db.refresh(sheet)
    return sheet


def unlock_sheet(
    db: Session, sheet_id: UUID, admin: User, reason: str = None
) -> GoalSheet:
    """Administrator override to unlock an approved or locked goal sheet.

    Args:
        db: Active database session.
        sheet_id: Target goal sheet UUID.
        admin: The administrator executing the unlock operation.
        reason: Optional text justification for the override.

    Returns:
        GoalSheet: The unlocked goal sheet reverted to 'returned' status.

    Raises:
        HTTPException: If the sheet is not found.
    """
    sheet = db.query(GoalSheet).filter(GoalSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")

    old_locked = sheet.is_locked
    sheet.is_locked = False
    sheet.status = "returned"

    log_audit(
        db,
        "goal_sheet",
        sheet.id,
        "goal_sheet.unlocked",
        admin.id,
        {"is_locked": old_locked, "status": "approved"},
        {"is_locked": False, "status": "returned"},
        reason=reason,
    )

    db.commit()
    db.refresh(sheet)
    return sheet


def inline_edit_goal(
    db: Session, sheet_id: UUID, goal_id: UUID, data: dict, manager: User
) -> Goal:
    """Execute manager inline edits of goal targets or weightages during review.

    Args:
        db: Active database session.
        sheet_id: Target goal sheet UUID.
        goal_id: Target goal UUID to modify.
        data: Dictionary containing fields to update.
        manager: The manager or administrator executing the edit.

    Returns:
        Goal: The updated goal entity.

    Raises:
        HTTPException: If the sheet or goal is not found, or validation fails.
    """
    sheet = db.query(GoalSheet).filter(GoalSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")

    if sheet.status != "submitted":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only submitted sheets can be edited during review",
        )

    employee = db.query(User).filter(User.id == sheet.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if manager.role != "admin" and employee.manager_id != manager.id:
        raise HTTPException(status_code=403, detail="Not your direct report")

    goal = (
        db.query(Goal)
        .filter(Goal.id == goal_id, Goal.goal_sheet_id == sheet_id)
        .first()
    )
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found in this sheet")

    old_values = {
        "target_value": str(goal.target_value)
        if goal.target_value is not None
        else None,
        "weightage": str(goal.weightage),
    }

    all_goals = db.query(Goal).filter(Goal.goal_sheet_id == sheet_id).all()

    if "weightage" in data:
        new_weightage = Decimal(str(data["weightage"]))
        if new_weightage < 10 or new_weightage > 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Weightage must be between 10 and 100",
            )

        other_total = sum(g.weightage for g in all_goals if g.id != goal.id)
        if other_total + new_weightage > 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Total weightage cannot exceed 100%",
            )

    for field, value in data.items():
        if hasattr(goal, field) and field in (
            "target_value",
            "weightage",
            "target_date",
        ):
            setattr(goal, field, value)

    new_values = {
        "target_value": str(goal.target_value)
        if goal.target_value is not None
        else None,
        "weightage": str(goal.weightage),
    }

    log_audit(
        db,
        "goal",
        goal.id,
        "goal.inline_edited_by_manager",
        manager.id,
        old_values,
        new_values,
    )

    # Recalculate total weightage
    sheet.total_weightage = sum(g.weightage for g in all_goals)

    db.commit()
    db.refresh(goal)
    return goal

