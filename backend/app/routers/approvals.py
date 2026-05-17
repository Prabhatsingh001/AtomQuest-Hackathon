"""Approvals router — manager approval workflow."""

from uuid import UUID
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.goal import GoalSheet
from app.models.outbox import OutboxEvent
from app.schemas.goal import GoalSheetResponse, GoalResponse
# from app.middleware.auth import get_current_active_user
from app.middleware.rbac import require_roles
from app.services.approval_service import (
    get_approval_queue, approve_sheet, return_sheet,
    unlock_sheet, inline_edit_goal
)

router = APIRouter(prefix="/approvals", tags=["Approvals"])


class ReturnRequest(BaseModel):
    comment: str


class InlineEditRequest(BaseModel):
    target_value: Optional[Decimal] = None
    weightage: Optional[Decimal] = None


class UnlockRequest(BaseModel):
    reason: Optional[str] = None


@router.get("/queue")
def get_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("manager", "admin")),
):
    """Retrieve all submitted goal sheets awaiting review from direct reports.

    Args:
        db: Active database session.
        current_user: Authenticated supervising manager or administrator.

    Returns:
        list[GoalSheetResponse]: List of serialized submitted goal sheets.
    """
    sheets = get_approval_queue(db, current_user)
    results = []
    emp_ids = {s.employee_id for s in sheets if s.employee_id}
    emp_map = {u.id: u for u in db.query(User).filter(User.id.in_(emp_ids)).all()} if emp_ids else {}

    for sheet in sheets:
        emp = emp_map.get(sheet.employee_id)
        resp = GoalSheetResponse.model_validate(sheet)
        resp.employee_name = emp.full_name if emp else None # type: ignore
        resp.employee_email = emp.email if emp else None # type: ignore
        results.append(resp)
    return results


@router.get("/sheet/{sheet_id}", response_model=GoalSheetResponse)
def get_approval_sheet(
    sheet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("manager", "admin")),
):
    """Retrieve comprehensive details of a specific goal sheet for approval review.

    Args:
        sheet_id: Target goal sheet UUID.
        db: Active database session.
        current_user: Authenticated supervising manager or administrator.

    Returns:
        GoalSheetResponse: Serialized goal sheet with employee metadata.

    Raises:
        HTTPException: If the sheet is not found or unauthorized.
    """
    sheet = db.query(GoalSheet).filter(GoalSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")
    emp = db.query(User).filter(User.id == sheet.employee_id).first()
    if current_user.role != "admin" and (
        not emp or emp.manager_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not your direct report")
    resp = GoalSheetResponse.model_validate(sheet)
    resp.employee_name = emp.full_name if emp else None # type: ignore
    resp.employee_email = emp.email if emp else None # type: ignore
    return resp


@router.put("/sheet/{sheet_id}/goal/{goal_id}", response_model=GoalResponse)
def inline_edit(
    sheet_id: UUID,
    goal_id: UUID,
    data: InlineEditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("manager", "admin")),
):
    """Perform inline modifications to a goal's target value or weightage during manager review.

    Args:
        sheet_id: Target goal sheet UUID.
        goal_id: Target goal UUID.
        data: Inline edit payload parameters.
        db: Active database session.
        current_user: Authenticated supervising manager or administrator.

    Returns:
        GoalResponse: Serialized updated goal.
    """
    edit_data = data.model_dump(exclude_unset=True)
    goal = inline_edit_goal(db, sheet_id, goal_id, edit_data, current_user)
    return GoalResponse.model_validate(goal)


@router.post("/approve/{sheet_id}", response_model=GoalSheetResponse)
def approve(
    sheet_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("manager", "admin")),
):
    """Officially approve an employee's submitted goal sheet and trigger notification.

    Args:
        sheet_id: Target goal sheet UUID.
        background_tasks: FastAPI background tasks queue.
        db: Active database session.
        current_user: Authenticated supervising manager or administrator.

    Returns:
        GoalSheetResponse: Serialized approved and locked goal sheet.
    """
    sheet = approve_sheet(db, sheet_id, current_user)
    
    emp = db.query(User).filter(User.id == sheet.employee_id).first()
    if emp:
        outbox = OutboxEvent(
            event_type="notify_goal_approved",
            payload={
                "sheet_id": str(sheet.id),
                "employee_email": emp.email,  # type: ignore
                "manager_name": current_user.full_name,  # type: ignore
            },
        )
        db.add(outbox)
        db.commit()

        from app.services.notification_service import notify_goal_approved
        background_tasks.add_task(
            notify_goal_approved, str(sheet.id), emp.email, current_user.full_name # type: ignore
        )
        
    return GoalSheetResponse.model_validate(sheet)


@router.post("/return/{sheet_id}", response_model=GoalSheetResponse)
def return_for_rework(
    sheet_id: UUID,
    data: ReturnRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("manager", "admin")),
):
    """Return a submitted goal sheet to an employee for revisions alongside a feedback comment.

    Args:
        sheet_id: Target goal sheet UUID.
        data: Return request schema containing feedback comment.
        background_tasks: FastAPI background tasks queue.
        db: Active database session.
        current_user: Authenticated supervising manager or administrator.

    Returns:
        GoalSheetResponse: Serialized returned goal sheet.
    """
    sheet = return_sheet(db, sheet_id, current_user, data.comment)
    
    emp = db.query(User).filter(User.id == sheet.employee_id).first()
    if emp:
        outbox = OutboxEvent(
            event_type="notify_goal_returned",
            payload={
                "sheet_id": str(sheet.id),
                "employee_email": emp.email,  # type: ignore
                "manager_name": current_user.full_name,  # type: ignore
                "comment": data.comment,
            },
        )
        db.add(outbox)
        db.commit()

        from app.services.notification_service import notify_goal_returned
        background_tasks.add_task(
            notify_goal_returned, str(sheet.id), emp.email, current_user.full_name, data.comment # type: ignore
        )

    return GoalSheetResponse.model_validate(sheet)


@router.post("/unlock/{sheet_id}", response_model=GoalSheetResponse)
def unlock(
    sheet_id: UUID,
    data: UnlockRequest = UnlockRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Override protection lock to unlock an approved goal sheet for administrative corrections.

    Args:
        sheet_id: Target goal sheet UUID.
        data: Optional justification schema.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        GoalSheetResponse: Serialized unlocked goal sheet.
    """
    sheet = unlock_sheet(db, sheet_id, current_user, data.reason) # type: ignore
    return GoalSheetResponse.model_validate(sheet)
