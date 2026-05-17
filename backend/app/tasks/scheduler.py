"""Celery task scheduler — periodic tasks for reminders and escalations."""

import asyncio
import logging
import redis
from datetime import date, timedelta, datetime
from typing import Optional, List, Dict, Any, Set
from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

redis_url = settings.REDIS_URL
if redis_url.startswith("rediss://") and "ssl_cert_reqs=" not in redis_url:
    delimiter = "&" if "?" in redis_url else "?"
    redis_url += f"{delimiter}ssl_cert_reqs=CERT_REQUIRED"

redis_kwargs = {"decode_responses": True}
if redis_url.startswith("rediss://"):
    redis_kwargs["ssl_cert_reqs"] = "required" # type: ignore

redis_client = redis.from_url(settings.REDIS_URL, **redis_kwargs)

celery = Celery(
    "atomquest",
    broker=redis_url,
    backend=redis_url,
)

celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    task_default_retry_delay=60,
    task_max_retries=5,
)

celery.conf.beat_schedule = {
    "enforce-cycle-windows": {
        "task": "app.tasks.scheduler.enforce_cycle_windows",
        "schedule": crontab(minute=1, hour=0),
    },
    "goal-submission-reminder": {
        "task": "app.tasks.scheduler.send_goal_submission_reminder",
        "schedule": crontab(minute=0, hour=9),
    },
    "approval-reminder": {
        "task": "app.tasks.scheduler.send_approval_reminder",
        "schedule": crontab(minute=0, hour=9),
    },
    "checkin-reminder": {
        "task": "app.tasks.scheduler.send_checkin_reminder",
        "schedule": crontab(minute=0, hour=9),
    },
    "run-escalations": {
        "task": "app.tasks.scheduler.run_escalations",
        "schedule": crontab(minute=30, hour=9),
    },
    "process-outbox-events": {
        "task": "app.tasks.scheduler.process_outbox_events",
        "schedule": crontab(minute="*/5"),
    },
}

celery.conf.timezone = "UTC"

_local_cache: Dict[str, datetime] = {}


def _acquire_lock(key: str, ttl_seconds: int = 259200) -> bool:
    """Acquire idempotency lock with automatic fallback to local memory if Redis is down."""
    try:
        if redis_client.get(key):
            return False
        redis_client.setex(key, ttl_seconds, "1")
        return True
    except Exception as e:
        logger.warning(
            f"Redis unavailable for idempotency lock {key}, falling back to local memory: {e}"
        )
        now = datetime.utcnow()
        if key in _local_cache:
            expires_at = _local_cache[key]
            if now < expires_at:
                return False
        _local_cache[key] = now + timedelta(seconds=ttl_seconds)
        stale_keys = [k for k, v in _local_cache.items() if v < now]
        for k in stale_keys:
            del _local_cache[k]
        return True


def _current_quarter(cycle, today: date) -> Optional[str]:
    """Determine the currently operating performance review quarter based on milestone dates.

    Args:
        cycle: Active performance appraisal cycle entity.
        today: Current date instance for evaluation.

    Returns:
        Optional[str]: Active quarter identifier ('q1', 'q2', 'q3', 'q4') or None if unstarted.
    """
    if today >= cycle.q4_open:
        return "q4"
    if today >= cycle.q3_open:
        return "q3"
    if today >= cycle.q2_open:
        return "q2"
    if today >= cycle.q1_open:
        return "q1"
    return None


def _achievement_done(goal, achievement) -> bool:
    """Evaluate whether an employee has completed their required actuals check-in for a milestone.

    Args:
        goal: Target Goal entity.
        achievement: Matching GoalAchievement record.

    Returns:
        bool: True if the actuals check-in is complete, False otherwise.
    """
    if not achievement:
        return False
    if achievement.status == "completed":
        return True
    if goal.uom_type == "timeline":
        return achievement.completion_date is not None
    return achievement.actual_value is not None


@celery.task
def enforce_cycle_windows():
    """Daily periodic Celery task to verify and log transitions across quarterly appraisal windows."""
    try:
        from app.database import SessionLocal
        from app.models.cycle import Cycle

        db = SessionLocal()
        cycle = db.query(Cycle).filter(Cycle.is_active == True).first()
        if cycle:
            today = date.today()
            logger.info(f"Cycle check: {cycle.name}, today={today}")
        db.close()
    except Exception as e:
        logger.error(f"enforce_cycle_windows error: {e}")


@celery.task
def send_goal_submission_reminder():
    """Daily periodic Celery task to dispatch email reminders to employees with unsubmitted goals."""
    try:
        from app.database import SessionLocal
        from app.models.cycle import Cycle
        from app.models.goal import GoalSheet
        from app.models.user import User
        from app.services.notification_service import send_email

        db = SessionLocal()
        cycle = db.query(Cycle).filter(Cycle.is_active == True).first()
        if not cycle:
            db.close()
            return

        today = date.today()
        threshold = cycle.goal_setting_open + timedelta(days=7)
        if today < threshold:
            db.close()
            return

        employees = (
            db.query(User).filter(User.role == "employee", User.is_active == True).all()
        )
        if not employees:
            db.close()
            return

        emp_ids = [emp.id for emp in employees]
        sheets = (
            db.query(GoalSheet)
            .filter(
                GoalSheet.employee_id.in_(emp_ids),
                GoalSheet.cycle_id == cycle.id,
            )
            .all()
        )
        sheet_map = {s.employee_id: s for s in sheets}

        email_tasks = []
        for emp in employees:
            sheet = sheet_map.get(emp.id)
            if not sheet or sheet.status == "draft":
                key = f"remind:submit:{emp.id}:{cycle.id}"
                if _acquire_lock(key):
                    logger.info(f"Reminder: {emp.email} has not submitted goals")
                    subject = "Action Required: Submit Your Goal Sheet"
                    body = f"Hello {emp.full_name},<br><br>The goal setting window is open for {cycle.name}. Please log in and submit your goals."
                    email_tasks.append(send_email(emp.email, subject, body))

        if email_tasks:
            asyncio.run(asyncio.gather(*email_tasks))

        db.close()
    except Exception as e:
        logger.error(f"send_goal_submission_reminder error: {e}")


@celery.task
def send_approval_reminder():
    """Daily periodic Celery task to alert supervising managers of pending unapproved goal sheets."""
    try:
        from app.database import SessionLocal
        from app.models.goal import GoalSheet
        from app.models.user import User
        from app.services.notification_service import send_email

        db = SessionLocal()
        sheets = db.query(GoalSheet).filter(GoalSheet.status == "submitted").all()
        if not sheets:
            db.close()
            return

        today = date.today()
        pending_sheets = []
        for sheet in sheets:
            if sheet.submitted_at:
                days_pending = (today - sheet.submitted_at.date()).days
                if days_pending >= 5:
                    key = f"remind:approve:{sheet.id}"
                    if _acquire_lock(key):
                        pending_sheets.append((sheet, days_pending, key))

        if not pending_sheets:
            db.close()
            return

        emp_ids = {s.employee_id for s, _, _ in pending_sheets if s.employee_id}
        emps = db.query(User).filter(User.id.in_(emp_ids)).all() if emp_ids else []
        emp_map = {emp.id: emp for emp in emps}

        mgr_ids = {emp.manager_id for emp in emps if emp.manager_id}
        mgrs = db.query(User).filter(User.id.in_(mgr_ids)).all() if mgr_ids else []
        mgr_map = {mgr.id: mgr for mgr in mgrs}

        email_tasks = []
        for sheet, days_pending, key in pending_sheets:
            emp = emp_map.get(sheet.employee_id)
            if emp and emp.manager_id:
                mgr = mgr_map.get(emp.manager_id)
                if mgr:
                    logger.info(
                        f"Approval reminder: {mgr.email} has pending sheet from {emp.email}"
                    )
                    subject = f"Action Required: Pending Goal Approval for {emp.full_name}"
                    body = f"Hello {mgr.full_name},<br><br>You have an unapproved goal sheet from {emp.full_name} waiting for {days_pending} days. Please review it."
                    email_tasks.append(send_email(mgr.email, subject, body))

        if email_tasks:
            asyncio.run(asyncio.gather(*email_tasks))

        db.close()
    except Exception as e:
        logger.error(f"send_approval_reminder error: {e}")


@celery.task
def send_checkin_reminder():
    """Daily periodic Celery task to notify employees of pending or overdue quarterly check-ins."""
    try:
        from app.database import SessionLocal
        from app.models.cycle import Cycle
        from app.models.user import User
        from app.models.goal import GoalSheet, Goal, GoalAchievement
        from app.services.notification_service import notify_checkin_reminder
        from sqlalchemy.orm import joinedload

        db = SessionLocal()
        cycle = db.query(Cycle).filter(Cycle.is_active == True).first()
        if not cycle:
            db.close()
            return
        quarter = _current_quarter(cycle, date.today())
        if not quarter:
            db.close()
            return
        logger.info(f"Check-in reminder check for cycle {cycle.name}")

        sheets = (
            db.query(GoalSheet)
            .options(joinedload(GoalSheet.goals))
            .filter(
                GoalSheet.cycle_id == cycle.id,
                GoalSheet.status == "approved",
            )
            .all()
        )
        if not sheets:
            db.close()
            return

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

        sheets_by_emp = {}
        for sheet in sheets:
            sheets_by_emp.setdefault(sheet.employee_id, []).append(sheet)

        emp_ids = list(sheets_by_emp.keys())
        employees = (
            db.query(User)
            .filter(User.id.in_(emp_ids), User.role == "employee", User.is_active == True)
            .all()
        )

        email_tasks = []
        for emp in employees:
            emp_sheets = sheets_by_emp.get(emp.id, [])
            pending = False
            for sheet in emp_sheets:
                for goal in sheet.goals:
                    ach = ach_map.get(goal.id)
                    if not _achievement_done(goal, ach):
                        pending = True
                        break
                if pending:
                    break

            if pending:
                key = f"remind:checkin:{emp.id}:{cycle.id}:{quarter}"
                if _acquire_lock(key):
                    email_tasks.append(notify_checkin_reminder(emp.email, emp.full_name))

        if email_tasks:
            asyncio.run(asyncio.gather(*email_tasks))

        db.close()
    except Exception as e:
        logger.error(f"send_checkin_reminder error: {e}")


@celery.task
def run_escalations():
    """Daily periodic Celery task to evaluate active escalation rules and trigger overdue alerts across organizational hierarchy."""
    try:
        from datetime import date
        from app.database import SessionLocal
        from app.models.audit import EscalationRule
        from app.models.goal import GoalSheet, Goal, GoalAchievement
        from app.models.user import User
        from app.models.cycle import Cycle
        from app.services.notification_service import send_email
        from sqlalchemy.orm import joinedload

        db = SessionLocal()
        cycle = db.query(Cycle).filter(Cycle.is_active == True).first()
        if not cycle:
            db.close()
            return

        rules = db.query(EscalationRule).filter(EscalationRule.is_active == True).all()
        if not rules:
            db.close()
            return

        email_tasks = []
        today = date.today()

        emps = db.query(User).filter(User.role == "employee", User.is_active == True).all()
        emp_map = {emp.id: emp for emp in emps}
        mgr_ids = {emp.manager_id for emp in emps if emp.manager_id}
        mgr_map = {m.id: m for m in db.query(User).filter(User.id.in_(mgr_ids)).all()} if mgr_ids else {}

        cycle_sheets = db.query(GoalSheet).options(joinedload(GoalSheet.goals)).filter(GoalSheet.cycle_id == cycle.id).all()
        sheets_by_emp = {s.employee_id: s for s in cycle_sheets}
        submitted_sheets = [s for s in cycle_sheets if s.status == "submitted"]
        approved_sheets = [s for s in cycle_sheets if s.status == "approved"]

        checkin_rules_exist = any(r.trigger_event == "checkin_not_done" for r in rules)
        ach_map = {}
        quarter = _current_quarter(cycle, today)
        if checkin_rules_exist and quarter:
            goal_ids = [goal.id for sheet in approved_sheets for goal in sheet.goals]
            if goal_ids:
                achievements = db.query(GoalAchievement).filter(
                    GoalAchievement.goal_id.in_(goal_ids),
                    GoalAchievement.quarter == quarter
                ).all()
                ach_map = {ach.goal_id: ach for ach in achievements}

        for rule in rules:
            logger.info(f"Evaluating escalation rule: {rule.name}")
            if rule.trigger_event == "goal_not_submitted":
                days_open = (today - cycle.goal_setting_open).days
                if days_open > rule.days_threshold:
                    for emp in emps:
                        sheet = sheets_by_emp.get(emp.id)
                        if not sheet or sheet.status == "draft":
                            if rule.notify_employee:
                                key = f"escalate:submit:emp:{emp.id}:{cycle.id}"
                                if _acquire_lock(key):
                                    email_tasks.append(
                                        send_email(
                                            emp.email,
                                            f"[Escalation] Overdue Goal Submission",
                                            f"Hello {emp.full_name}, your goal submission is overdue by {days_open} days.",
                                        )
                                    )
                            if rule.notify_manager and emp.manager_id:
                                mgr = mgr_map.get(emp.manager_id)
                                if mgr:
                                    key = f"escalate:submit:mgr:{emp.id}:{cycle.id}"
                                    if _acquire_lock(key):
                                        email_tasks.append(
                                            send_email(
                                                mgr.email,
                                                f"[Escalation] Direct Report Overdue Goals",
                                                f"Hello {mgr.full_name}, {emp.full_name}'s goal submission is overdue.",
                                            )
                                        )
            elif rule.trigger_event == "goal_not_approved":
                for sheet in submitted_sheets:
                    if sheet.submitted_at:
                        days_pending = (today - sheet.submitted_at.date()).days
                        if days_pending > rule.days_threshold:
                            emp = emp_map.get(sheet.employee_id)
                            if emp and emp.manager_id:
                                mgr = mgr_map.get(emp.manager_id)
                                if mgr and rule.notify_manager:
                                    key = f"escalate:approve:mgr:{sheet.id}"
                                    if _acquire_lock(key):
                                        email_tasks.append(
                                            send_email(
                                                mgr.email,
                                                f"[Escalation] Overdue Goal Approval",
                                                f"Hello {mgr.full_name}, you have a pending sheet from {emp.full_name} overdue by {days_pending} days.",
                                            )
                                        )
            elif rule.trigger_event == "checkin_not_done":
                if not quarter:
                    continue
                open_date = getattr(cycle, f"{quarter}_open")
                days_open = (today - open_date).days
                if days_open <= rule.days_threshold:
                    continue

                approved_sheets_by_emp = {}
                for sheet in approved_sheets:
                    approved_sheets_by_emp.setdefault(sheet.employee_id, []).append(sheet)

                for emp in emps:
                    emp_sheets = approved_sheets_by_emp.get(emp.id, [])
                    pending = False
                    for sheet in emp_sheets:
                        for goal in sheet.goals:
                            ach = ach_map.get(goal.id)
                            if not _achievement_done(goal, ach):
                                pending = True
                                break
                        if pending:
                            break

                    if not pending:
                        continue

                    if rule.notify_employee:
                        key = f"escalate:checkin:emp:{emp.id}:{cycle.id}:{quarter}"
                        if _acquire_lock(key):
                            email_tasks.append(
                                send_email(
                                    emp.email,
                                    "[Escalation] Overdue Check-in",
                                    f"Hello {emp.full_name}, your {quarter.upper()} check-in is overdue by {days_open} days.",
                                )
                            )
                    if rule.notify_manager and emp.manager_id:
                        mgr = mgr_map.get(emp.manager_id)
                        if mgr:
                            key = f"escalate:checkin:mgr:{emp.id}:{cycle.id}:{quarter}"
                            if _acquire_lock(key):
                                email_tasks.append(
                                    send_email(
                                        mgr.email,
                                        "[Escalation] Direct Report Overdue Check-in",
                                        f"Hello {mgr.full_name}, {emp.full_name}'s {quarter.upper()} check-in is overdue.",
                                    )
                                )
                    if rule.notify_hr and settings.HR_EMAIL:
                        key = f"escalate:checkin:hr:{emp.id}:{cycle.id}:{quarter}"
                        if _acquire_lock(key):
                            email_tasks.append(
                                send_email(
                                    settings.HR_EMAIL,
                                    "[Escalation] Overdue Check-in",
                                    f"{emp.full_name}'s {quarter.upper()} check-in is overdue.",
                                )
                            )

        if email_tasks:
            asyncio.run(asyncio.gather(*email_tasks))

        db.close()
    except Exception as e:
        logger.error(f"run_escalations error: {e}")


@celery.task
def process_outbox_events():
    """Periodic outbox relay task to process pending asynchronous notifications reliably."""
    try:
        from app.database import SessionLocal
        from app.models.outbox import OutboxEvent
        from app.services.notification_service import (
            notify_goal_submitted,
            notify_goal_approved,
            notify_goal_returned,
        )

        db = SessionLocal()
        events = db.query(OutboxEvent).filter(OutboxEvent.status == "pending").limit(50).all()
        if not events:
            db.close()
            return

        for event in events:
            event.status = "processing"
        db.commit()

        tasks = []
        for event in events:
            try:
                payload = event.payload
                if event.event_type == "notify_goal_submitted":
                    tasks.append(
                        notify_goal_submitted(
                            payload["sheet_id"],
                            payload["employee_email"],
                            payload["employee_name"],
                            payload["manager_email"],
                        )
                    )
                elif event.event_type == "notify_goal_approved":
                    tasks.append(
                        notify_goal_approved(
                            payload["sheet_id"],
                            payload["employee_email"],
                            payload["manager_name"],
                        )
                    )
                elif event.event_type == "notify_goal_returned":
                    tasks.append(
                        notify_goal_returned(
                            payload["sheet_id"],
                            payload["employee_email"],
                            payload["manager_name"],
                            payload["comment"],
                        )
                    )
                event.status = "completed"
            except Exception as e:
                logger.error(f"Failed outbox event {event.id}: {e}")
                event.status = "failed"

        if tasks:
            asyncio.run(asyncio.gather(*tasks))

        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"process_outbox_events error: {e}")

