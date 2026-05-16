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
    """Get submitted goal sheets from direct reports."""
    sheets = get_approval_queue(db, current_user)
    results = []
    for sheet in sheets:
        emp = db.query(User).filter(User.id == sheet.employee_id).first()
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
    """Get full sheet detail for approval review."""
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
    """Inline edit target/weightage during approval review."""
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
    """Approve a goal sheet."""
    sheet = approve_sheet(db, sheet_id, current_user)
    
    emp = db.query(User).filter(User.id == sheet.employee_id).first()
    if emp:
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
    """Return a sheet for rework with a comment."""
    sheet = return_sheet(db, sheet_id, current_user, data.comment)
    
    emp = db.query(User).filter(User.id == sheet.employee_id).first()
    if emp:
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
    """Admin unlock a locked goal sheet."""
    sheet = unlock_sheet(db, sheet_id, current_user, data.reason) # type: ignore
    return GoalSheetResponse.model_validate(sheet)
