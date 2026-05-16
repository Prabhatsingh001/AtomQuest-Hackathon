"""Reports router — achievement reports, exports, analytics."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.cycle import Cycle
from app.middleware.rbac import require_roles
from app.services.report_service import (
    get_achievement_report,
    get_completion_dashboard,
    export_csv,
    export_excel,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/achievement-report")
def achievement_report(
    cycle_id: UUID = Query(None),
    quarter: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Get planned vs actual for all employees."""
    if not cycle_id:
        cycle = db.query(Cycle).filter(Cycle.is_active).first()
        if not cycle:
            return []
        cycle_id = cycle.id
    return get_achievement_report(db, cycle_id, quarter, department)


@router.get("/completion-dashboard")
def completion_dashboard(
    cycle_id: UUID = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Which employees/managers have done check-ins."""
    if not cycle_id:
        cycle = db.query(Cycle).filter(Cycle.is_active).first()
        if not cycle:
            return []
        cycle_id = cycle.id
    return get_completion_dashboard(db, cycle_id)


@router.get("/export/csv")
def export_csv_report(
    cycle_id: UUID = Query(None),
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Stream CSV export of achievement report."""
    if not cycle_id:
        cycle = db.query(Cycle).filter(Cycle.is_active).first()
        if not cycle:
            return StreamingResponse(iter([""]), media_type="text/csv")
        cycle_id = cycle.id

    rows = get_achievement_report(db, cycle_id, department=department)
    csv_content = export_csv(rows)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=achievement_report.csv"},
    )


@router.get("/export/excel")
def export_excel_report(
    cycle_id: UUID = Query(None),
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Return Excel file of achievement report."""
    if not cycle_id:
        cycle = db.query(Cycle).filter(Cycle.is_active).first()
        if not cycle:
            from io import BytesIO

            return StreamingResponse(BytesIO(), media_type="application/octet-stream")
        cycle_id = cycle.id

    rows = get_achievement_report(db, cycle_id, department=department)
    excel_bytes = export_excel(rows)

    return StreamingResponse(
        excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=achievement_report.xlsx"},
    )


@router.get("/analytics/qoq")
def qoq_trends(
    cycle_id: UUID = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Quarter-on-quarter score trends."""
    from app.models.goal import GoalAchievement

    if not cycle_id:
        cycle = db.query(Cycle).filter(Cycle.is_active).first()
        if not cycle:
            return []
        cycle_id = cycle.id

    results = []
    for q in ["q1", "q2", "q3", "q4"]:
        achievements = (
            db.query(GoalAchievement)
            .filter(GoalAchievement.cycle_id == cycle_id, GoalAchievement.quarter == q)
            .all()
        )
        scores = [
            float(a.computed_score)
            for a in achievements
            if a.computed_score is not None
        ] # type: ignore
        avg_score = sum(scores) / len(scores) if scores else 0
        results.append(
            {"quarter": q, "avg_score": round(avg_score, 4), "count": len(scores)}
        )

    return results


@router.get("/analytics/distribution")
def goal_distribution(
    cycle_id: UUID = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Goal count by thrust area, UoM type, status."""
    from app.models.goal import Goal, GoalSheet
    from sqlalchemy import func

    if not cycle_id:
        cycle = db.query(Cycle).filter(Cycle.is_active).first()
        if not cycle:
            return {"by_thrust_area": [], "by_uom_type": [], "by_status": []}
        cycle_id = cycle.id

    by_thrust = (
        db.query(Goal.thrust_area, func.count(Goal.id))
        .join(GoalSheet)
        .filter(GoalSheet.cycle_id == cycle_id)
        .group_by(Goal.thrust_area)
        .all()
    )

    by_uom = (
        db.query(Goal.uom_type, func.count(Goal.id))
        .join(GoalSheet)
        .filter(GoalSheet.cycle_id == cycle_id)
        .group_by(Goal.uom_type)
        .all()
    )

    by_status = (
        db.query(GoalSheet.status, func.count(GoalSheet.id))
        .filter(GoalSheet.cycle_id == cycle_id)
        .group_by(GoalSheet.status)
        .all()
    )

    return {
        "by_thrust_area": [{"name": t, "count": c} for t, c in by_thrust],
        "by_uom_type": [{"name": t, "count": c} for t, c in by_uom],
        "by_status": [{"name": s, "count": c} for s, c in by_status],
    }
