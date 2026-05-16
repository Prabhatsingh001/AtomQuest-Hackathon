"""Check-in service — business logic for quarterly check-ins."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.goal import Goal, GoalAchievement, GoalSheet
from app.models.cycle import Cycle
from app.models.checkin import CheckinComment
from app.models.user import User
from app.services.score_engine import compute_score


QUARTER_MAP = {
    "q1": "q1_open",
    "q2": "q2_open",
    "q3": "q3_open",
    "q4": "q4_open",
    "annual": "q4_open",
}


def normalize_quarter(quarter: str) -> str:
    """Return a normalized quarter value or reject invalid input."""
    normalized = quarter.lower()
    if normalized not in QUARTER_MAP:
        raise HTTPException(status_code=400, detail="Invalid quarter")
    return normalized


def check_quarter_window(db: Session, cycle_id: UUID, quarter: str):
    """Verify that the check-in window for the given quarter is open and not closed."""
    quarter = normalize_quarter(quarter)
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")

    if not cycle.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cycle is inactive. Check-ins are closed.",
        )

    field = QUARTER_MAP[quarter]
    open_date = getattr(cycle, field)
    today = date.today()
    if today < open_date:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{quarter.upper()} check-in window opens on {open_date.isoformat()}",
        )

    # Check window closure when subsequent quarter opens
    if quarter == "q1" and today >= cycle.q2_open:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Q1 check-in window has closed (Q2 has started).",
        )
    elif quarter == "q2" and today >= cycle.q3_open:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Q2 check-in window has closed (Q3 has started).",
        )
    elif quarter == "q3" and today >= cycle.q4_open:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Q3 check-in window has closed (Q4 has started).",
        )


def update_achievement(
    db: Session,
    goal_id: UUID,
    quarter: str,
    user: User,
    actual_value: Optional[Decimal] = None,
    completion_date: Optional[date] = None,
    achievement_status: Optional[str] = None,
) -> GoalAchievement:
    """Update or create a goal achievement for a quarter."""
    quarter = normalize_quarter(quarter)
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    sheet = db.query(GoalSheet).filter(GoalSheet.id == goal.goal_sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")

    # Verify ownership
    if sheet.employee_id != user.id:
        raise HTTPException(status_code=403, detail="Not your goal")

    if sheet.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Check-ins are only allowed after goals are approved",
        )

    # Check quarter window
    check_quarter_window(db, sheet.cycle_id, quarter)

    # Get or create achievement
    achievement = (
        db.query(GoalAchievement)
        .filter(
            GoalAchievement.goal_id == goal_id,
            GoalAchievement.quarter == quarter,
        )
        .first()
    )

    if not achievement:
        achievement = GoalAchievement(
            goal_id=goal_id,
            cycle_id=sheet.cycle_id,
            quarter=quarter,
            updated_by=user.id,
        )
        db.add(achievement)

    if actual_value is not None:
        achievement.actual_value = actual_value
    if completion_date is not None:
        achievement.completion_date = completion_date
    if achievement_status is not None:
        achievement.status = achievement_status

    achievement.updated_by = user.id
    achievement.updated_at = datetime.utcnow()

    # Compute score
    score = compute_score(
        uom_type=goal.uom_type,
        target=goal.target_value,
        actual=achievement.actual_value,
        target_date=goal.target_date,
        completion_date=achievement.completion_date,
    )
    achievement.computed_score = Decimal(str(round(score, 4)))

    db.commit()
    db.refresh(achievement)
    return achievement


def get_employee_achievements(
    db: Session, cycle_id: UUID, quarter: str, employee_id: UUID
) -> List[dict]:
    """Get all achievements for an employee's goals in a quarter."""
    quarter = normalize_quarter(quarter)
    sheets = (
        db.query(GoalSheet)
        .filter(
            GoalSheet.employee_id == employee_id,
            GoalSheet.cycle_id == cycle_id,
            GoalSheet.status == "approved",
        )
        .all()
    )

    results = []
    for sheet in sheets:
        for goal in sheet.goals:
            achievement = (
                db.query(GoalAchievement)
                .filter(
                    GoalAchievement.goal_id == goal.id,
                    GoalAchievement.quarter == quarter,
                )
                .first()
            )

            results.append(
                {
                    "goal": goal,
                    "achievement": achievement,
                    "sheet": sheet,
                }
            )

    return results


def get_team_achievements(db: Session, cycle_id: UUID, quarter: str, viewer: User) -> List[dict]:
    """Get all achievements for a manager's team in a quarter."""
    quarter = normalize_quarter(quarter)
    employees_query = db.query(User)
    if viewer.role != "admin":
        employees_query = employees_query.filter(User.manager_id == viewer.id)
    employees = employees_query.order_by(User.full_name.asc()).all()
    results = []
    for emp in employees:
        emp_data = {
            "employee": emp,
            "goals": [],
        }
        sheets = (
            db.query(GoalSheet)
            .filter(
                GoalSheet.employee_id == emp.id,
                GoalSheet.cycle_id == cycle_id,
                GoalSheet.status == "approved",
            )
            .all()
        )

        for sheet in sheets:
            for goal in sheet.goals:
                achievement = (
                    db.query(GoalAchievement)
                    .filter(
                        GoalAchievement.goal_id == goal.id,
                        GoalAchievement.quarter == quarter,
                    )
                    .first()
                )
                emp_data["goals"].append(
                    {
                        "goal": goal,
                        "achievement": achievement,
                        "sheet_id": sheet.id,
                    }
                )

        results.append(emp_data)

    return results


def add_checkin_comment(
    db: Session, goal_sheet_id: UUID, quarter: str, manager: User, comment: str
) -> CheckinComment:
    """Add a check-in comment for an employee's sheet."""
    quarter = normalize_quarter(quarter)
    sheet = db.query(GoalSheet).filter(GoalSheet.id == goal_sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")

    # Verify manager relationship
    employee = db.query(User).filter(User.id == sheet.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if manager.role != "admin" and employee.manager_id != manager.id:
        raise HTTPException(status_code=403, detail="Not your direct report")

    checkin_comment = CheckinComment(
        goal_sheet_id=goal_sheet_id,
        quarter=quarter,
        manager_id=manager.id,
        comment=comment,
    )
    db.add(checkin_comment)
    db.commit()
    db.refresh(checkin_comment)
    return checkin_comment
