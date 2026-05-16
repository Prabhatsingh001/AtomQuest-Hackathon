"""Report schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class AchievementReportRow(BaseModel):
    """Structured data row representing an employee's milestone achievements for organizational reporting.

    Attributes:
        employee_name: Display name of employee.
        department: Assigned department.
        manager_name: Supervising manager display name.
        thrust_area: Strategic category of the goal.
        goal_title: Goal title string.
        uom_type: Unit of measurement classification.
        target: Formatted target threshold or deadline string.
        q1_actual: Q1 recorded actual value.
        q1_score: Recalculated Q1 performance score.
        q2_actual: Q2 recorded actual value.
        q2_score: Recalculated Q2 performance score.
        q3_actual: Q3 recorded actual value.
        q3_score: Recalculated Q3 performance score.
        q4_actual: Q4 recorded actual value.
        q4_score: Recalculated Q4 performance score.
        status: Overall goal sheet status.
    """
    employee_name: str
    department: Optional[str]
    manager_name: Optional[str]
    thrust_area: str
    goal_title: str
    uom_type: str
    target: Optional[str]
    q1_actual: Optional[str] = None
    q1_score: Optional[float] = None
    q2_actual: Optional[str] = None
    q2_score: Optional[float] = None
    q3_actual: Optional[str] = None
    q3_score: Optional[float] = None
    q4_actual: Optional[str] = None
    q4_score: Optional[float] = None
    status: str


class CompletionDashboardRow(BaseModel):
    """Aggregated department-level statistics measuring check-in compliance across milestone periods.

    Attributes:
        department: Evaluated department name.
        manager_name: Department leader display name.
        total_employees: Headcount of active employees.
        goal_setting_done_pct: Percentage of employees with submitted/approved goals.
        q1_done_pct: Q1 check-in completion percentage.
        q2_done_pct: Q2 check-in completion percentage.
        q3_done_pct: Q3 check-in completion percentage.
        q4_done_pct: Q4 check-in completion percentage.
    """
    department: Optional[str]
    manager_name: Optional[str]
    total_employees: int
    goal_setting_done_pct: float
    q1_done_pct: float
    q2_done_pct: float
    q3_done_pct: float
    q4_done_pct: float


class AuditLogResponse(BaseModel):
    """Serialized audit trail record capturing system state mutations.

    Attributes:
        id: Unique audit entry UUID.
        entity_type: Entity table name altered ('GoalSheet', 'User').
        entity_id: Primary key UUID of modified entity.
        action: Event action name ('submit', 'approve', 'unlock').
        changed_by: User UUID who executed the mutation.
        changed_by_name: Executing user display name.
        old_value: Snapshot dictionary of prior state.
        new_value: Snapshot dictionary of updated state.
        reason: Optional justification notes.
        timestamp: Event execution timestamp.
    """
    id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    changed_by: UUID
    changed_by_name: Optional[str] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    reason: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class EscalationRuleCreate(BaseModel):
    """Schema for creating a new automated notification escalation rule.

    Attributes:
        name: Rule descriptive identifier.
        trigger_event: Trigger condition ('goal_not_submitted', 'goal_not_approved', 'checkin_not_done').
        days_threshold: Grace period days limit before escalation triggers.
        notify_employee: True to notify the employee directly.
        notify_manager: True to alert the direct supervising manager.
        notify_hr: True to dispatch summary escalation to HR.
    """
    name: str
    trigger_event: str
    days_threshold: int
    notify_employee: bool = True
    notify_manager: bool = True
    notify_hr: bool = False


class EscalationRuleUpdate(BaseModel):
    """Schema for modifying trigger conditions or active status of an escalation rule.

    Attributes:
        name: Optional updated rule name.
        trigger_event: Optional updated trigger event identifier.
        days_threshold: Optional updated days grace period.
        notify_employee: Optional updated employee alert flag.
        notify_manager: Optional updated manager alert flag.
        notify_hr: Optional updated HR alert flag.
        is_active: Optional active status toggle.
    """
    name: Optional[str] = None
    trigger_event: Optional[str] = None
    days_threshold: Optional[int] = None
    notify_employee: Optional[bool] = None
    notify_manager: Optional[bool] = None
    notify_hr: Optional[bool] = None
    is_active: Optional[bool] = None


class EscalationRuleResponse(BaseModel):
    """Serialized automated escalation rule configuration record.

    Attributes:
        id: Unique rule UUID.
        name: Rule identifier.
        trigger_event: Condition event name.
        days_threshold: Overdue grace period limit.
        notify_employee: Employee alert status.
        notify_manager: Manager alert status.
        notify_hr: HR escalation status.
        is_active: True if currently active and evaluated by Celery scheduler.
    """
    id: UUID
    name: str
    trigger_event: str
    days_threshold: int
    notify_employee: bool
    notify_manager: bool
    notify_hr: bool
    is_active: bool

    class Config:
        from_attributes = True
