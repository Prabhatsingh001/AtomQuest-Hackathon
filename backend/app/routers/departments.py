"""Departments router — public department listing."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.department import Department
from app.schemas.department import DepartmentResponse

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=list[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)):
    """Retrieve all active organizational departments available for employee assignment.

    Args:
        db: Active database session.

    Returns:
        list[DepartmentResponse]: Serialized list of active departments.
    """
    departments = (
        db.query(Department)
        .filter(Department.is_active)
        .order_by(Department.name.asc())
        .all()
    )
    return [DepartmentResponse.model_validate(d) for d in departments]
