"""Goal service — business logic for goal management."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.goal import GoalSheet, Goal, GoalAchievement
from app.models.user import User
from app.models.cycle import Cycle
from app.schemas.goal import GoalCreate, GoalUpdate
from app.services.audit_service import log_audit


def get_or_create_sheet(db: Session, employee_id: UUID, cycle_id: UUID) -> GoalSheet:
    """Get existing goal sheet or create a new one for the employee+cycle."""
    sheet = db.query(GoalSheet).filter(
        GoalSheet.employee_id == employee_id,
        GoalSheet.cycle_id == cycle_id,
    ).first()

    if not sheet:
        sheet = GoalSheet(
            employee_id=employee_id,
            cycle_id=cycle_id,
            status="draft",
            total_weightage=Decimal("0.00"),
        )
        db.add(sheet)
        db.commit()
        db.refresh(sheet)

    return sheet


def validate_goal_creation(db: Session, sheet: GoalSheet, weightage: Decimal, exclude_goal_id: UUID = None, bypass_lock: bool = False):
    """Validate goal creation/update rules."""
    # Check sheet status
    if not bypass_lock and sheet.status not in ("draft", "returned"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Goal sheet is locked. Contact admin to unlock.",
        )

    # Check max goals (excluding shared goals)
    goals_query = db.query(Goal).filter(
        Goal.goal_sheet_id == sheet.id,
        Goal.is_shared == False
    )
    if exclude_goal_id:
        goals_query = goals_query.filter(Goal.id != exclude_goal_id)
    goal_count = goals_query.count()

    if not exclude_goal_id and goal_count >= 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Maximum 8 goals allowed per cycle",
        )

    # Check weightage
    if weightage < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Minimum weightage per goal is 10%",
        )
    if weightage > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Weightage cannot exceed 100%",
        )

    # Check total weightage
    existing_weightage = Decimal("0.00")
    goals = goals_query.all()
    for g in goals:
        existing_weightage += g.weightage

    if existing_weightage + weightage > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Total weightage would exceed 100%. Current: {existing_weightage}%, Adding: {weightage}%",
        )


def validate_uom(uom_type: str, target_value: Optional[Decimal], target_date=None):
    """Validate UoM-specific requirements."""
    if uom_type in ("min", "max"):
        if target_value is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"UoM type '{uom_type}' requires a target value",
            )
    elif uom_type == "timeline":
        if target_date is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="UoM type 'timeline' requires a target date",
            )
    # zero: no validation needed


def create_goal(db: Session, data: GoalCreate, user: User) -> Goal:
    """Create a new goal on a goal sheet."""
    sheet = db.query(GoalSheet).filter(GoalSheet.id == data.goal_sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")

    if sheet.employee_id != user.id:
        raise HTTPException(status_code=403, detail="Not your goal sheet")

    validate_goal_creation(db, sheet, data.weightage)
    validate_uom(data.uom_type, data.target_value, data.target_date)

    goal = Goal(
        goal_sheet_id=sheet.id,
        thrust_area=data.thrust_area,
        title=data.title,
        description=data.description,
        uom_type=data.uom_type,
        target_value=data.target_value,
        target_date=data.target_date,
        weightage=data.weightage,
    )
    db.add(goal)

    # Recalculate total weightage
    _recalculate_weightage(db, sheet)

    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, goal_id: UUID, data: GoalUpdate, user: User) -> Goal:
    """Update an existing goal."""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    sheet = db.query(GoalSheet).filter(GoalSheet.id == goal.goal_sheet_id).first()

    # Check if shared goal — restrict edits
    if goal.is_shared:
        if data.title is not None or data.target_value is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Title and target of shared goals cannot be changed",
            )

    if sheet.employee_id != user.id and user.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    # For employees, check sheet status
    if user.role == "employee":
        if sheet.status not in ("draft", "returned"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Goal sheet is locked. Contact admin to unlock.",
            )

    new_weightage = data.weightage if data.weightage is not None else goal.weightage
    if data.weightage is not None:
        validate_goal_creation(
            db,
            sheet,
            new_weightage,
            exclude_goal_id=goal_id,
            bypass_lock=user.role in ("manager", "admin"),
        )

    if data.uom_type is not None:
        tv = data.target_value if data.target_value is not None else goal.target_value
        td = data.target_date if data.target_date is not None else goal.target_date
        validate_uom(data.uom_type, tv, td)

    # Track old values for audit if locked
    old_values = {}
    if sheet.is_locked:
        old_values = {
            "target_value": str(goal.target_value)
            if goal.target_value is not None
            else None,
            "weightage": str(goal.weightage),
            "title": goal.title,
        }

    # Apply updates
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)

    _recalculate_weightage(db, sheet)

    # Log audit for locked sheet changes
    if sheet.is_locked and old_values:
        new_values = {
            "target_value": str(goal.target_value)
            if goal.target_value is not None
            else None,
            "weightage": str(goal.weightage),
            "title": goal.title,
        }
        log_audit(
            db, "goal", goal.id, "goal.updated_while_locked",
            user.id, old_values, new_values
        )

    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, goal_id: UUID, user: User):
    """Delete a goal."""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    sheet = db.query(GoalSheet).filter(GoalSheet.id == goal.goal_sheet_id).first()
    if sheet.employee_id != user.id and user.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete goal")

    if user.role == "employee" and sheet.status not in ("draft", "returned"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Goal sheet is locked. Contact admin to unlock.",
        )

    old_values = {}
    if sheet.is_locked:
        old_values = {
            "target_value": str(goal.target_value)
            if goal.target_value is not None
            else None,
            "weightage": str(goal.weightage),
            "title": goal.title,
        }

    db.delete(goal)
    _recalculate_weightage(db, sheet)

    if sheet.is_locked and old_values:
        log_audit(
            db, "goal", goal.id, "goal.deleted_while_locked",
            user.id, old_values, None
        )

    db.commit()


def submit_sheet(db: Session, sheet_id: UUID, user: User) -> GoalSheet:
    """Submit a goal sheet for manager approval."""
    sheet = db.query(GoalSheet).filter(GoalSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")

    if sheet.employee_id != user.id:
        raise HTTPException(status_code=403, detail="Not your goal sheet")

    if sheet.status not in ("draft", "returned"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Goal sheet cannot be submitted in current state",
        )

    # Check total weightage
    total = _calculate_total_weightage(db, sheet.id)
    if total != Decimal("100.00"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Total weightage must equal 100% before submitting. Currently at {total}%",
        )

    sheet.status = "submitted"
    sheet.submitted_at = datetime.utcnow()
    sheet.total_weightage = total
    db.commit()
    db.refresh(sheet)
    return sheet


def _recalculate_weightage(db: Session, sheet: GoalSheet):
    """Recalculate the total weightage on a goal sheet."""
    total = _calculate_total_weightage(db, sheet.id)
    sheet.total_weightage = total


def _calculate_total_weightage(db: Session, sheet_id: UUID) -> Decimal:
    """Calculate total weightage for a sheet."""
    goals = db.query(Goal).filter(
        Goal.goal_sheet_id == sheet_id,
        Goal.is_shared == False
    ).all()
    return sum(g.weightage for g in goals) if goals else Decimal("0.00")
