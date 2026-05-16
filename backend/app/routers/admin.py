"""Admin router — cycle, user, audit, escalation management."""

from uuid import UUID
from typing import Optional
from decimal import Decimal
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext

from app.database import get_db
from app.models.user import User
from app.models.cycle import Cycle
from app.models.goal import GoalSheet, Goal
from app.models.department import Department
from app.models.audit import AuditLog, EscalationRule
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.cycle import CycleCreate, CycleUpdate, CycleResponse
from app.schemas.goal import GoalSheetResponse, SharedGoalPush, GoalResponse, GoalUpdate
from app.schemas.report import (
    AuditLogResponse,
    EscalationRuleCreate,
    EscalationRuleUpdate,
    EscalationRuleResponse,
)
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
)
from app.middleware.rbac import require_roles
from app.services.audit_service import log_audit
from app.middleware.auth import get_current_active_user

router = APIRouter(prefix="/admin", tags=["Admin"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _to_jsonable(value):
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    return value


@router.get("/cycles")
def list_cycles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve all configured organizational performance cycles.

    Args:
        db: Active database session.
        current_user: Authenticated user making the request.

    Returns:
        list[CycleResponse]: List of serialized cycle records.
    """
    cycles = db.query(Cycle).order_by(Cycle.created_at.desc()).all()
    return [CycleResponse.model_validate(c) for c in cycles]


@router.post("/cycles", response_model=CycleResponse)
def create_cycle(
    data: CycleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Create a new organizational performance appraisal cycle.

    Args:
        data: Verified schema containing cycle dates and metadata.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        CycleResponse: Serialized newly created cycle.
    """
    cycle = Cycle(**data.model_dump(), created_by=current_user.id)
    db.add(cycle)
    db.flush()
    log_audit(
        db,
        "cycle",
        cycle.id, # type: ignore
        "cycle.created",
        current_user.id, # type: ignore
        new_value=_to_jsonable(data.model_dump()),
    )
    db.commit()
    db.refresh(cycle)
    return CycleResponse.model_validate(cycle)


@router.put("/cycles/{cycle_id}", response_model=CycleResponse)
def update_cycle(
    cycle_id: UUID,
    data: CycleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Update milestone dates or attributes of an existing performance cycle.

    Args:
        cycle_id: Target cycle UUID.
        data: Payload containing fields to update.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        CycleResponse: Updated cycle record.

    Raises:
        HTTPException: If the target cycle is not found.
    """
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    old_values = {
        "name": cycle.name,
        "goal_setting_open": cycle.goal_setting_open.isoformat()
        if cycle.goal_setting_open # type: ignore
        else None,
        "q1_open": cycle.q1_open.isoformat() if cycle.q1_open else None, # type: ignore
        "q2_open": cycle.q2_open.isoformat() if cycle.q2_open else None, # type: ignore
        "q3_open": cycle.q3_open.isoformat() if cycle.q3_open else None, # type: ignore
        "q4_open": cycle.q4_open.isoformat() if cycle.q4_open else None, # type: ignore
        "is_active": cycle.is_active,
    }
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cycle, field, value)
    log_audit(
        db,
        "cycle",
        cycle.id, # type: ignore
        "cycle.updated",
        current_user.id, # type: ignore
        old_value=_to_jsonable(old_values), #type: ignore
        new_value=_to_jsonable(data.model_dump(exclude_unset=True)), # type: ignore
    )
    db.commit()
    db.refresh(cycle)
    return CycleResponse.model_validate(cycle)


@router.post("/cycles/{cycle_id}/activate", response_model=CycleResponse)
def activate_cycle(
    cycle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Enforce a specific performance cycle as the actively operating company cycle.

    Args:
        cycle_id: Target cycle UUID to activate.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        CycleResponse: Serialized activated cycle.

    Raises:
        HTTPException: If the target cycle is not found.
    """
    previous_active = db.query(Cycle).filter(Cycle.is_active).first()
    db.query(Cycle).update({"is_active": False})
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    cycle.is_active = True # type: ignore
    log_audit(
        db,
        "cycle",
        cycle.id, # type: ignore
        "cycle.activated",
        current_user.id, # type: ignore
        old_value=_to_jsonable(
            {"previous_active_id": previous_active.id if previous_active else None}
        ), # type: ignore
        new_value=_to_jsonable({"is_active": True}), # type: ignore
    )
    db.commit()
    db.refresh(cycle)
    return CycleResponse.model_validate(cycle)


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Retrieve all system user accounts.

    Args:
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        list[UserResponse]: Serialized list of user records.
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserResponse)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Create a new user account with assigned role and department.

    Args:
        data: Verified user creation schema.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        UserResponse: Serialized newly created user profile.

    Raises:
        HTTPException: If email is already registered or department is invalid.
    """
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if data.department_id:
        department = (
            db.query(Department).filter(Department.id == data.department_id).first()
        )
        if not department or not department.is_active: # type: ignore
            raise HTTPException(
                status_code=400, detail="Invalid or inactive department"
            )

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=pwd_context.hash(data.password),
        role=data.role,
        department_id=data.department_id,
        manager_id=data.manager_id,
    )
    db.add(user)
    db.flush()
    log_audit(
        db,
        "user",
        user.id, # type: ignore
        "user.created",
        current_user.id, # type: ignore
        new_value=_to_jsonable(
            {
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "department_id": user.department_id,
                "manager_id": user.manager_id,
            }
        ),  # type: ignore
    )
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Modify role, department, or activation status of an existing user.

    Args:
        user_id: Target user UUID.
        data: Fields to update.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        UserResponse: Updated user profile.

    Raises:
        HTTPException: If user or department is not found.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if data.department_id is not None:
        department = (
            db.query(Department).filter(Department.id == data.department_id).first()
        )
        if data.department_id and (not department or not department.is_active): # type: ignore
            raise HTTPException(
                status_code=400, detail="Invalid or inactive department"
            )
    old_values = {
        "full_name": user.full_name,
        "role": user.role,
        "department_id": user.department_id,
        "manager_id": str(user.manager_id) if user.manager_id else None, #type: ignore
        "is_active": user.is_active,
    }
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    log_audit(
        db,
        "user",
        user.id, # type: ignore
        "user.updated",
        current_user.id, # type: ignore
        old_value=_to_jsonable(old_values), #type: ignore
        new_value=_to_jsonable(data.model_dump(exclude_unset=True)), #type: ignore
    ) #type: ignore
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/users/{user_id}/sheet/{cycle_id}", response_model=GoalSheetResponse)
def get_user_sheet(
    user_id: UUID,
    cycle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Retrieve the performance goal sheet for a specific user and cycle.

    Args:
        user_id: Target employee UUID.
        cycle_id: Target performance cycle UUID.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        GoalSheetResponse: Serialized goal sheet data.

    Raises:
        HTTPException: If the goal sheet is not found.
    """
    sheet = (
        db.query(GoalSheet)
        .filter(GoalSheet.employee_id == user_id, GoalSheet.cycle_id == cycle_id)
        .first()
    )
    if not sheet:
        raise HTTPException(status_code=404, detail="Sheet not found")

    emp = db.query(User).filter(User.id == user_id).first()
    resp = GoalSheetResponse.model_validate(sheet)
    resp.employee_name = emp.full_name if emp else None #type: ignore
    return resp


@router.get("/departments", response_model=list[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """List all organizational departments with aggregate employee counts.

    Args:
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        list[DepartmentResponse]: Serialized departments list.
    """
    rows = (
        db.query(Department, func.count(User.id))
        .outerjoin(User, User.department_id == Department.id)
        .group_by(Department.id)
        .order_by(Department.name.asc())
        .all()
    )

    results = []
    for dept, count in rows:
        resp = DepartmentResponse.model_validate(dept)
        results.append(resp.model_copy(update={"employee_count": count}))
    return results


@router.post("/departments", response_model=DepartmentResponse)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Create a new organizational department.

    Args:
        data: Verified department creation schema.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        DepartmentResponse: Serialized newly created department.

    Raises:
        HTTPException: If department name already exists.
    """
    existing = db.query(Department).filter(Department.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department already exists")

    department = Department(name=data.name, is_active=True)
    db.add(department)
    db.flush()
    log_audit(
        db,
        "department",
        department.id, # type: ignore
        "department.created",
        current_user.id, # type: ignore
        new_value=_to_jsonable({"name": department.name, "is_active": True}), # type: ignore
    )
    db.commit()
    db.refresh(department)
    resp = DepartmentResponse.model_validate(department)
    return resp


@router.post(
    "/departments/{department_id}/deactivate", response_model=DepartmentResponse
)
def deactivate_department(
    department_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Deactivate an organizational department if no employees are currently assigned.

    Args:
        department_id: Target department UUID.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        DepartmentResponse: Serialized deactivated department.

    Raises:
        HTTPException: If department is not found or has active assigned employees.
    """
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    employee_count = db.query(User).filter(User.department_id == department_id).count()
    if employee_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Department cannot be deactivated while employees are assigned",
        )

    department.is_active = False #type: ignore
    log_audit(
        db,
        "department",
        department.id, # type: ignore
        "department.deactivated",
        current_user.id, # type: ignore
        old_value=_to_jsonable({"is_active": True}), # type: ignore
        new_value=_to_jsonable({"is_active": False}), # type: ignore
    )
    db.commit()
    db.refresh(department)
    resp = DepartmentResponse.model_validate(department)
    return resp


@router.get("/completion-dashboard")
def completion_dashboard(
    cycle_id: UUID = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Retrieve organizational goal and check-in completion statistics grouped by department.

    Args:
        cycle_id: Optional performance cycle UUID.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        list[dict]: Department completion dashboard metrics.
    """
    if not cycle_id:
        cycle = db.query(Cycle).filter(Cycle.is_active).first()
        if not cycle:
            return []
        cycle_id = cycle.id
    from app.services.report_service import get_completion_dashboard

    return get_completion_dashboard(db, cycle_id)


@router.get("/audit-logs")
def get_audit_logs(
    entity_type: Optional[str] = None,
    user_id: Optional[UUID] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Retrieve immutable system audit log records with pagination and filtering.

    Args:
        entity_type: Optional entity domain filter.
        user_id: Optional user UUID filter.
        page: Requested page index.
        page_size: Records per page limit.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        dict: Paginated audit log response container.
    """
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if user_id:
        query = query.filter(AuditLog.changed_by == user_id)

    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()

    results = []
    for log in logs:
        user = db.query(User).filter(User.id == log.changed_by).first()
        resp = AuditLogResponse.model_validate(log)
        resp.changed_by_name = user.full_name if user else None #type: ignore
        results.append(resp)

    return {"items": results, "total": total, "page": page, "page_size": page_size}


@router.post("/shared-goals/push")
def push_shared_goals(
    data: SharedGoalPush,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Distribute a shared company goal to multiple employees across their active goal sheets.

    Args:
        data: Push payload containing goal template attributes and employee UUIDs.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        dict: Confirmation message and list of successfully assigned employee UUIDs.

    Raises:
        HTTPException: If no active cycle is found.
    """
    cycle = db.query(Cycle).filter(Cycle.is_active).first()
    if not cycle:
        raise HTTPException(status_code=400, detail="No active cycle")

    admin_sheet = (
        db.query(GoalSheet)
        .filter(
            GoalSheet.employee_id == current_user.id,
            GoalSheet.cycle_id == cycle.id,
        )
        .first()
    )
    if not admin_sheet:
        admin_sheet = GoalSheet(
            employee_id=current_user.id,
            cycle_id=cycle.id,
            status="draft",
            total_weightage=Decimal("0.00"),
        )
        db.add(admin_sheet)
        db.commit()
        db.refresh(admin_sheet)

    parent_goal = Goal(
        goal_sheet_id=admin_sheet.id,
        thrust_area=data.goal_template.thrust_area,
        title=data.goal_template.title,
        description=data.goal_template.description,
        uom_type=data.goal_template.uom_type,
        target_value=data.goal_template.target_value,
        target_date=data.goal_template.target_date,
        weightage=data.goal_template.weightage,
        is_shared=True,
    )
    db.add(parent_goal)
    db.commit()
    db.refresh(parent_goal)

    created = []
    num_employees = len(data.employee_ids)
    individual_weightage = Decimal(data.goal_template.weightage) / Decimal(num_employees) if num_employees > 0 else Decimal(0)
    for emp_id in data.employee_ids:
        emp_sheet = (
            db.query(GoalSheet)
            .filter(
                GoalSheet.employee_id == emp_id,
                GoalSheet.cycle_id == cycle.id,
            )
            .first()
        )
        if not emp_sheet:
            emp_sheet = GoalSheet(
                employee_id=emp_id,
                cycle_id=cycle.id,
                status="draft",
                total_weightage=Decimal("0.00"),
            )
            db.add(emp_sheet)
            db.commit()
            db.refresh(emp_sheet)

        linked_goal = Goal(
            goal_sheet_id=emp_sheet.id,
            thrust_area=data.goal_template.thrust_area,
            title=data.goal_template.title,
            description=data.goal_template.description,
            uom_type=data.goal_template.uom_type,
            target_value=data.goal_template.target_value,
            target_date=data.goal_template.target_date,
            weightage=individual_weightage,
            is_shared=True,
            parent_goal_id=parent_goal.id,
        )
        db.add(linked_goal)

        from app.services.goal_service import _calculate_total_weightage
        emp_sheet.total_weightage = _calculate_total_weightage(db, emp_sheet.id)

        created.append(str(emp_id))

    db.commit()
    log_audit(
        db,
        "goal",
        parent_goal.id, # type: ignore
        "shared_goal.pushed",
        current_user.id, #type: ignore
        new_value=_to_jsonable(
            {
                "employee_ids": data.employee_ids,
                "goal_template": data.goal_template.model_dump(),
                "cycle_id": cycle.id,
            }
        ),  # type: ignore
    )
    db.commit()
    return {
        "message": f"Shared goal pushed to {len(created)} employees",
        "employee_ids": created,
    }


@router.get("/shared-goals/list", response_model=list[GoalResponse])
def get_shared_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Retrieve all shared company goals authored by the administrator in the active cycle.

    Args:
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        list[GoalResponse]: Serialized list of shared goals.
    """
    cycle = db.query(Cycle).filter(Cycle.is_active).first()
    if not cycle:
        return []
    
    admin_sheet = db.query(GoalSheet).filter(
        GoalSheet.employee_id == current_user.id,
        GoalSheet.cycle_id == cycle.id
    ).first()
    
    if not admin_sheet:
        return []

    return db.query(Goal).filter(
        Goal.goal_sheet_id == admin_sheet.id,
        Goal.is_shared == True,
        Goal.parent_goal_id == None
    ).all()


@router.put("/shared-goals/{goal_id}", response_model=GoalResponse)
def update_shared_goal(
    goal_id: UUID,
    data: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Synchronously update attributes of a parent shared goal and all its distributed child copies.

    Args:
        goal_id: Target parent shared goal UUID.
        data: Fields to modify.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        GoalResponse: Updated parent shared goal entity.

    Raises:
        HTTPException: If parent shared goal is not found.
    """
    parent = db.query(Goal).filter(Goal.id == goal_id, Goal.is_shared == True).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Shared goal not found")
        
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(parent, field, value)
        
    children = db.query(Goal).filter(Goal.parent_goal_id == goal_id).all()
    num_children = len(children)
    
    for child in children:
        for field, value in data.model_dump(exclude_unset=True).items():
            if field == 'weightage':
                value = Decimal(value) / Decimal(num_children) if num_children > 0 else Decimal(0)
            setattr(child, field, value)
            
    db.commit()
    db.refresh(parent)
    return parent


@router.get("/escalation-rules")
def list_escalation_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Retrieve all configured automated escalation rules.

    Args:
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        list[EscalationRuleResponse]: List of escalation rules.
    """
    rules = db.query(EscalationRule).all()
    return [EscalationRuleResponse.model_validate(r) for r in rules]


@router.post("/escalation-rules", response_model=EscalationRuleResponse)
def create_escalation_rule(
    data: EscalationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Create a new automated escalation policy rule.

    Args:
        data: Verified escalation rule creation schema.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        EscalationRuleResponse: Serialized newly created rule.
    """
    rule = EscalationRule(**data.model_dump())
    db.add(rule)
    db.flush()
    log_audit(
        db,
        "escalation_rule",
        rule.id, #type: ignore
        "escalation_rule.created",
        current_user.id, #type: ignore
        new_value=_to_jsonable(data.model_dump()), #type: ignore
    )
    db.commit()
    db.refresh(rule)
    return EscalationRuleResponse.model_validate(rule)


@router.put("/escalation-rules/{rule_id}", response_model=EscalationRuleResponse)
def update_escalation_rule(
    rule_id: UUID,
    data: EscalationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Modify parameters or status of an existing escalation policy rule.

    Args:
        rule_id: Target escalation rule UUID.
        data: Fields to update.
        db: Active database session.
        current_user: Authenticated administrator entity.

    Returns:
        EscalationRuleResponse: Updated escalation rule record.

    Raises:
        HTTPException: If target escalation rule is not found.
    """
    rule = db.query(EscalationRule).filter(EscalationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Escalation rule not found")
    old_values = {
        "name": rule.name,
        "trigger_event": rule.trigger_event,
        "days_threshold": rule.days_threshold,
        "notify_employee": rule.notify_employee,
        "notify_manager": rule.notify_manager,
        "notify_hr": rule.notify_hr,
        "is_active": rule.is_active,
    }
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    log_audit(
        db,
        "escalation_rule",
        rule.id,  # type: ignore
        "escalation_rule.updated",
        current_user.id,  # type: ignore
        old_value=_to_jsonable(old_values), # type: ignore
        new_value=_to_jsonable(data.model_dump(exclude_unset=True)), # type: ignore
    )
    db.commit()
    db.refresh(rule)
    return EscalationRuleResponse.model_validate(rule)
