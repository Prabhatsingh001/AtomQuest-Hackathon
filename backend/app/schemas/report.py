"""Report schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class AchievementReportRow(BaseModel):
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
    department: Optional[str]
    manager_name: Optional[str]
    total_employees: int
    goal_setting_done_pct: float
    q1_done_pct: float
    q2_done_pct: float
    q3_done_pct: float
    q4_done_pct: float


class AuditLogResponse(BaseModel):
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
    name: str
    trigger_event: str
    days_threshold: int
    notify_employee: bool = True
    notify_manager: bool = True
    notify_hr: bool = False


class EscalationRuleUpdate(BaseModel):
    name: Optional[str] = None
    trigger_event: Optional[str] = None
    days_threshold: Optional[int] = None
    notify_employee: Optional[bool] = None
    notify_manager: Optional[bool] = None
    notify_hr: Optional[bool] = None
    is_active: Optional[bool] = None


class EscalationRuleResponse(BaseModel):
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
