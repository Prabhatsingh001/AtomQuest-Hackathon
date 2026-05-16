"""Report service — data aggregation for reports and exports."""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from io import BytesIO
import csv
import io

from sqlalchemy.orm import Session
from openpyxl import Workbook
from sqlalchemy import or_

from app.models.goal import GoalSheet, Goal, GoalAchievement
from app.models.user import User
from app.models.department import Department
from app.models.cycle import Cycle


def get_achievement_report(
    db: Session,
    cycle_id: UUID,
    quarter: Optional[str] = None,
    department: Optional[str] = None,
) -> List[dict]:
    """Generate comprehensive achievement report metrics across all employee goal sheets.

    Args:
        db: Active database session.
        cycle_id: Target performance cycle UUID.
        quarter: Optional specific milestone review period to filter.
        department: Optional department name to filter results.

    Returns:
        List[dict]: A list of row dictionaries mapping employee goal actuals and scores.

    Raises:
        ValueError: If an invalid quarter identifier is provided.
    """
    if quarter and quarter not in {"q1", "q2", "q3", "q4"}:
        raise ValueError("quarter must be one of: q1, q2, q3, q4")

    query = (
        db.query(Goal, GoalSheet, User, Department)
        .join(GoalSheet, Goal.goal_sheet_id == GoalSheet.id)
        .join(User, GoalSheet.employee_id == User.id)
        .outerjoin(Department, User.department_id == Department.id)
        .filter(GoalSheet.cycle_id == cycle_id)
    )
    if department:
        query = query.filter(Department.name == department)

    rows = []
    quarters = [quarter] if quarter else ["q1", "q2", "q3", "q4"]

    results = query.all()
    manager_ids = {
        employee.manager_id for _, _, employee, _ in results if employee.manager_id
    }
    managers = {}
    if manager_ids:
        managers = {
            m.id: m for m in db.query(User).filter(User.id.in_(manager_ids)).all()
        }

    goal_ids = [goal.id for goal, _, _, _ in results]
    achievements = {}
    if goal_ids:
        for ach in (
            db.query(GoalAchievement)
            .filter(
                GoalAchievement.goal_id.in_(goal_ids),
                GoalAchievement.quarter.in_(quarters),
            )
            .all()
        ):
            achievements[(ach.goal_id, ach.quarter)] = ach

    for goal, sheet, employee, department_row in results:
        manager = managers.get(employee.manager_id)
        row = {
            "employee_name": employee.full_name,
            "department": department_row.name if department_row else None,
            "manager_name": manager.full_name if manager else None,
            "thrust_area": goal.thrust_area,
            "goal_title": goal.title,
            "uom_type": goal.uom_type,
            "target": str(goal.target_value)
            if goal.target_value is not None
            else (str(goal.target_date) if goal.target_date else "0"),
            "status": sheet.status,
            "q1_actual": None,
            "q1_score": None,
            "q2_actual": None,
            "q2_score": None,
            "q3_actual": None,
            "q3_score": None,
            "q4_actual": None,
            "q4_score": None,
        }

        for q in quarters:
            ach = achievements.get((goal.id, q))
            row[f"{q}_actual"] = (
                str(ach.actual_value) if ach and ach.actual_value is not None else None
            )
            row[f"{q}_score"] = (
                float(ach.computed_score)
                if ach and ach.computed_score is not None
                else None
            )

        rows.append(row)

    return rows


def get_completion_dashboard(db: Session, cycle_id: UUID) -> List[dict]:
    """Calculate organizational milestone check-in completion percentages by department.

    Args:
        db: Active database session.
        cycle_id: Target performance cycle UUID.

    Returns:
        List[dict]: Department aggregated metrics mapping employee completion progress.
    """
    employees = (
        db.query(User.id, Department.name)
        .outerjoin(Department, User.department_id == Department.id)
        .all()
    )
    dept_map = {}
    for emp_id, dept in employees:
        dept_map.setdefault(dept or "Unassigned", []).append(emp_id)

    sheets = (
        db.query(GoalSheet.employee_id, GoalSheet.status)
        .filter(GoalSheet.cycle_id == cycle_id)
        .all()
    )
    sheet_status = {emp_id: status for emp_id, status in sheets}
    goal_done_emps = {
        emp_id
        for emp_id, status in sheet_status.items()
        if status in {"submitted", "approved"}
    }

    quarter_emps = {"q1": set(), "q2": set(), "q3": set(), "q4": set()}
    achievements = (
        db.query(GoalAchievement.quarter, GoalSheet.employee_id)
        .join(Goal, GoalAchievement.goal_id == Goal.id)
        .join(GoalSheet, Goal.goal_sheet_id == GoalSheet.id)
        .filter(
            GoalSheet.cycle_id == cycle_id,
            or_(
                GoalAchievement.actual_value.isnot(None),
                GoalAchievement.completion_date.isnot(None),
                GoalAchievement.status == "completed",
            ),
        )
        .distinct()
        .all()
    )
    for quarter, emp_id in achievements:
        if quarter in quarter_emps:
            quarter_emps[quarter].add(emp_id)

    results = []
    for dept_name, emp_ids in dept_map.items():
        total = len(emp_ids)
        if total == 0:
            continue

        goal_done = len(goal_done_emps.intersection(emp_ids))
        quarter_done = {
            q: len(quarter_emps[q].intersection(emp_ids))
            for q in ["q1", "q2", "q3", "q4"]
        }

        results.append(
            {
                "department": dept_name,
                "manager_name": None,
                "total_employees": total,
                "goal_setting_done_pct": round(goal_done / total * 100, 1),
                "q1_done_pct": round(quarter_done["q1"] / total * 100, 1),
                "q2_done_pct": round(quarter_done["q2"] / total * 100, 1),
                "q3_done_pct": round(quarter_done["q3"] / total * 100, 1),
                "q4_done_pct": round(quarter_done["q4"] / total * 100, 1),
            }
        )

    return results


def export_csv(rows: List[dict]) -> str:
    """Format an achievement report dictionary dataset into a raw CSV text string.

    Args:
        rows: Dataset list of dictionaries.

    Returns:
        str: Comma-separated values formatted text payload.
    """
    output = io.StringIO()
    if not rows:
        return ""
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def export_excel(rows: List[dict]) -> BytesIO:
    """Compile an achievement report dictionary dataset into an OpenXML Excel workbook stream.

    Args:
        rows: Dataset list of dictionaries.

    Returns:
        BytesIO: In-memory byte stream containing the formatted spreadsheet.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Achievement Report"

    if rows:
        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row.get(h) for h in headers])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
