"""Goals router — CRUD for goals and goal sheets."""

from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.goal import GoalSheet
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse, GoalSheetResponse
from app.middleware.auth import get_current_active_user
from app.services.goal_service import (
    get_or_create_sheet,
    create_goal,
    update_goal,
    delete_goal,
    submit_sheet,
)

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get("/my-sheet/{cycle_id}", response_model=GoalSheetResponse)
def get_my_sheet(
    cycle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get or create the current user's goal sheet for a cycle."""
    sheet = get_or_create_sheet(db, current_user.id, cycle_id) # type: ignore
    resp = GoalSheetResponse.model_validate(sheet)
    resp.employee_name = current_user.full_name # type: ignore
    resp.employee_email = current_user.email # type: ignore
    return resp


@router.post("/", response_model=GoalResponse)
def create_new_goal(
    data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new goal on the user's goal sheet."""
    goal = create_goal(db, data, current_user)
    return GoalResponse.model_validate(goal)


@router.put("/{goal_id}", response_model=GoalResponse)
def update_existing_goal(
    goal_id: UUID,
    data: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing goal."""
    goal = update_goal(db, goal_id, data, current_user)
    return GoalResponse.model_validate(goal)


@router.delete("/{goal_id}")
def delete_existing_goal(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a goal (only if sheet is draft/returned)."""
    delete_goal(db, goal_id, current_user)
    return {"message": "Goal deleted"}


@router.post("/submit/{sheet_id}", response_model=GoalSheetResponse)
def submit_goal_sheet(
    sheet_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Submit a goal sheet for manager approval."""
    sheet = submit_sheet(db, sheet_id, current_user)

    if current_user.manager_id: # type: ignore
        manager = db.query(User).filter(User.id == current_user.manager_id).first()
        if manager:
            from app.services.notification_service import notify_goal_submitted

            background_tasks.add_task(
                notify_goal_submitted,
                str(sheet.id),
                current_user.email, # type: ignore
                current_user.full_name, # type: ignore
                manager.email, # type: ignore
            )

    return GoalSheetResponse.model_validate(sheet)


@router.get("/sheet/{sheet_id}", response_model=GoalSheetResponse)
def get_sheet(
    sheet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a goal sheet by ID."""
    sheet = db.query(GoalSheet).filter(GoalSheet.id == sheet_id).first()
    if not sheet:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Goal sheet not found")

    emp = db.query(User).filter(User.id == sheet.employee_id).first()
    if current_user.role != "admin": # type: ignore
        if sheet.employee_id != current_user.id: # type: ignore
            if not emp or emp.manager_id != current_user.id: # type: ignore
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=403, detail="Not authorized to view this sheet"
                )

    resp = GoalSheetResponse.model_validate(sheet)
    resp.employee_name = emp.full_name if emp else None # type: ignore
    resp.employee_email = emp.email if emp else None # type: ignore
    return resp
