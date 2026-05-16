"""Checkins router — quarterly check-in management."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.goal import GoalSheet
from app.models.checkin import CheckinComment
from app.schemas.goal import GoalAchievementResponse, GoalAchievementUpdate
from app.schemas.checkin import CheckinCommentCreate, CheckinCommentResponse
from app.middleware.auth import get_current_active_user
from app.middleware.rbac import require_roles
from app.services.checkin_service import (
    update_achievement,
    get_employee_achievements,
    get_team_achievements,
    add_checkin_comment,
    normalize_quarter,
)

router = APIRouter(prefix="/checkins", tags=["Check-ins"])


@router.get("/my/{cycle_id}/{quarter}")
def get_my_checkins(
    cycle_id: UUID,
    quarter: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get the current user's achievements for a quarter."""
    quarter = normalize_quarter(quarter)
    results = get_employee_achievements(db, cycle_id, quarter, current_user.id) # type: ignore
    output = []
    for item in results:
        goal = item["goal"]
        ach = item["achievement"]
        output.append(
            {
                "goal_id": str(goal.id),
                "goal_title": goal.title,
                "thrust_area": goal.thrust_area,
                "uom_type": goal.uom_type,
                "target_value": str(goal.target_value)
                if goal.target_value is not None
                else None,
                "target_date": str(goal.target_date) if goal.target_date else None,
                "weightage": str(goal.weightage),
                "actual_value": str(ach.actual_value)
                if ach and ach.actual_value is not None
                else None,
                "completion_date": str(ach.completion_date)
                if ach and ach.completion_date
                else None,
                "status": ach.status if ach else "not_started",
                "computed_score": float(ach.computed_score)
                if ach and ach.computed_score is not None
                else None,
                "sheet_id": str(item["sheet"].id),
            }
        )
    return output


@router.put("/achievement/{goal_id}/{quarter}", response_model=GoalAchievementResponse)
def update_goal_achievement(
    goal_id: UUID,
    quarter: str,
    data: GoalAchievementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update actual value / status for a goal in a quarter."""
    ach = update_achievement(
        db,
        goal_id,
        quarter,
        current_user,
        actual_value=data.actual_value,
        completion_date=data.completion_date,
        achievement_status=data.status,
    )
    return GoalAchievementResponse.model_validate(ach)


@router.get("/team/{cycle_id}/{quarter}")
def get_team_checkins(
    cycle_id: UUID,
    quarter: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("manager", "admin")),
):
    """Get all team members' achievements for a quarter."""
    quarter = normalize_quarter(quarter)
    results = get_team_achievements(db, cycle_id, quarter, current_user)
    output = []
    for item in results:
        emp = item["employee"]
        goals_data = []
        for g in item["goals"]:
            goal = g["goal"]
            ach = g["achievement"]
            goals_data.append(
                {
                    "goal_id": str(goal.id),
                    "goal_title": goal.title,
                    "uom_type": goal.uom_type,
                    "target_value": str(goal.target_value)
                    if goal.target_value is not None
                    else None,
                    "weightage": str(goal.weightage),
                    "actual_value": str(ach.actual_value)
                    if ach and ach.actual_value is not None
                    else None,
                    "status": ach.status if ach else "not_started",
                    "computed_score": float(ach.computed_score)
                    if ach and ach.computed_score is not None
                    else None,
                    "sheet_id": str(g["sheet_id"]),
                }
            )
        output.append(
            {
                "employee_id": str(emp.id),
                "employee_name": emp.full_name,
                "department": emp.department_name,
                "goals": goals_data,
            }
        )
    return output


@router.post("/comment", response_model=CheckinCommentResponse)
def post_checkin_comment(
    data: CheckinCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("manager", "admin")),
):
    """Add a check-in comment for an employee's sheet."""
    comment = add_checkin_comment(
        db, data.goal_sheet_id, data.quarter, current_user, data.comment
    )
    resp = CheckinCommentResponse.model_validate(comment)
    resp.manager_name = current_user.full_name  # type: ignore
    return resp


@router.get("/comments/{sheet_id}/{quarter}")
def get_comments(
    sheet_id: UUID,
    quarter: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Fetch check-in comments for a sheet and quarter."""
    quarter = normalize_quarter(quarter)
    sheet = db.query(GoalSheet).filter(GoalSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")

    if current_user.role != "admin":  # type: ignore
        if sheet.employee_id != current_user.id: # type: ignore
            emp = db.query(User).filter(User.id == sheet.employee_id).first()
            if not emp or emp.manager_id != current_user.id: # type: ignore
                raise HTTPException(
                    status_code=403, detail="Not authorized to view comments"
                )

    comments = (
        db.query(CheckinComment)
        .filter(
            CheckinComment.goal_sheet_id == sheet_id,
            CheckinComment.quarter == quarter,
        )
        .order_by(CheckinComment.created_at.desc())
        .all()
    )

    results = []
    for c in comments:
        mgr = db.query(User).filter(User.id == c.manager_id).first()
        resp = CheckinCommentResponse.model_validate(c)
        resp.manager_name = mgr.full_name if mgr else None  # type: ignore
        results.append(resp)
    return results
