"""Check-in service — business logic for quarterly check-ins."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

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
    """Validate and normalize a milestone quarter identifier.

    Args:
        quarter: Raw quarter string input.

    Returns:
        str: Normalized lowercase quarter string.

    Raises:
        HTTPException: If the quarter identifier is not recognized.
    """
    normalized = quarter.lower()
    if normalized not in QUARTER_MAP:
        raise HTTPException(status_code=400, detail="Invalid quarter")
    return normalized


def check_quarter_window(db: Session, cycle_id: UUID, quarter: str):
    """Verify that the check-in time window for a specific milestone is open.

    Args:
        db: Active database session.
        cycle_id: Target performance cycle UUID.
        quarter: Target milestone identifier.

    Raises:
        HTTPException: If the cycle is inactive, window has not opened, or window has closed.
    """
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
    """Record or update an employee's milestone achievement actuals.

    Args:
        db: Active database session.
        goal_id: Target goal UUID.
        quarter: Target milestone period.
        user: The authenticated employee submitting the check-in.
        actual_value: Recorded numeric actual figure.
        completion_date: Completion date if applicable.
        achievement_status: Qualitative status string.

    Returns:
        GoalAchievement: The updated achievement record with recalculated score.

    Raises:
        HTTPException: If the goal or sheet is not found, unauthorized, or window is closed.
    """
    quarter = normalize_quarter(quarter)
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    sheet = db.query(GoalSheet).filter(GoalSheet.id == goal.goal_sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")

    if sheet.employee_id != user.id:
        raise HTTPException(status_code=403, detail="Not your goal")

    if sheet.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Check-ins are only allowed after goals are approved",
        )

    check_quarter_window(db, sheet.cycle_id, quarter)

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
    """Retrieve all goal achievements for a specific employee in a given quarter.

    Args:
        db: Active database session.
        cycle_id: Target performance cycle UUID.
        quarter: Milestone review period.
        employee_id: Target employee UUID.

    Returns:
        List[dict]: A list of dictionaries containing goal, achievement, and sheet records.
    """
    quarter = normalize_quarter(quarter)
    sheets = (
        db.query(GoalSheet)
        .options(joinedload(GoalSheet.goals))
        .filter(
            GoalSheet.employee_id == employee_id,
            GoalSheet.cycle_id == cycle_id,
            GoalSheet.status == "approved",
        )
        .all()
    )

    goal_ids = [goal.id for sheet in sheets for goal in sheet.goals]
    ach_map = {}
    if goal_ids:
        achievements = (
            db.query(GoalAchievement)
            .filter(
                GoalAchievement.goal_id.in_(goal_ids),
                GoalAchievement.quarter == quarter,
            )
            .all()
        )
        ach_map = {ach.goal_id: ach for ach in achievements}

    results = []
    for sheet in sheets:
        for goal in sheet.goals:
            results.append(
                {
                    "goal": goal,
                    "achievement": ach_map.get(goal.id),
                    "sheet": sheet,
                }
            )

    return results


def get_team_achievements(db: Session, cycle_id: UUID, quarter: str, viewer: User) -> List[dict]:
    """Retrieve goal check-in progress for all team members managed by the viewer.

    Args:
        db: Active database session.
        cycle_id: Target performance cycle UUID.
        quarter: Milestone review period.
        viewer: The supervising manager or administrator entity.

    Returns:
        List[dict]: A structured list of team member progress reports.
    """
    quarter = normalize_quarter(quarter)
    employees_query = db.query(User)
    if viewer.role != "admin":
        employees_query = employees_query.filter(User.manager_id == viewer.id)
    employees = employees_query.order_by(User.full_name.asc()).all()

    if not employees:
        return []

    emp_ids = [emp.id for emp in employees]
    sheets = (
        db.query(GoalSheet)
        .options(joinedload(GoalSheet.goals))
        .filter(
            GoalSheet.employee_id.in_(emp_ids),
            GoalSheet.cycle_id == cycle_id,
            GoalSheet.status == "approved",
        )
        .all()
    )

    sheets_by_emp = {}
    goal_ids = []
    for sheet in sheets:
        sheets_by_emp.setdefault(sheet.employee_id, []).append(sheet)
        for goal in sheet.goals:
            goal_ids.append(goal.id)

    ach_map = {}
    if goal_ids:
        achievements = (
            db.query(GoalAchievement)
            .filter(
                GoalAchievement.goal_id.in_(goal_ids),
                GoalAchievement.quarter == quarter,
            )
            .all()
        )
        ach_map = {ach.goal_id: ach for ach in achievements}

    results = []
    for emp in employees:
        emp_data = {
            "employee": emp,
            "goals": [],
        }
        emp_sheets = sheets_by_emp.get(emp.id, [])
        for sheet in emp_sheets:
            for goal in sheet.goals:
                emp_data["goals"].append(
                    {
                        "goal": goal,
                        "achievement": ach_map.get(goal.id),
                        "sheet_id": sheet.id,
                    }
                )
        results.append(emp_data)

    return results


def add_checkin_comment(
    db: Session, goal_sheet_id: UUID, quarter: str, manager: User, comment: str
) -> CheckinComment:
    """Record qualitative feedback comment from a manager regarding a check-in.

    Args:
        db: Active database session.
        goal_sheet_id: Associated goal sheet UUID.
        quarter: Target milestone period.
        manager: Supervising manager entity authoring the comment.
        comment: Feedback text content.

    Returns:
        CheckinComment: The recorded comment entity.

    Raises:
        HTTPException: If the sheet is not found or unauthorized.
    """
    quarter = normalize_quarter(quarter)
    sheet = db.query(GoalSheet).filter(GoalSheet.id == goal_sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Goal sheet not found")

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
