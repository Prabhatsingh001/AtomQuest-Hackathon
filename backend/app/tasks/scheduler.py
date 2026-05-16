"""Celery task scheduler — periodic tasks for reminders and escalations."""

import asyncio
import logging
import redis
from datetime import date, timedelta
from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

celery = Celery(
    "atomquest",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
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
}

celery.conf.timezone = "UTC"


def _current_quarter(cycle, today: date):
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
    if not achievement:
        return False
    if achievement.status == "completed":
        return True
    if goal.uom_type == "timeline":
        return achievement.completion_date is not None
    return achievement.actual_value is not None


@celery.task
def enforce_cycle_windows():
    """Check if any quarter window should open; log when opened."""
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
    """Check employees who haven't submitted goals after goal_setting_open."""
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
        email_tasks = []
        for emp in employees:
            sheet = (
                db.query(GoalSheet)
                .filter(
                    GoalSheet.employee_id == emp.id,
                    GoalSheet.cycle_id == cycle.id,
                )
                .first()
            )
            if not sheet or sheet.status == "draft":
                key = f"remind:submit:{emp.id}:{cycle.id}"
                if not redis_client.get(key):
                    redis_client.setex(key, 3 * 86400, "1")
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
    """Check managers who haven't approved submitted goals."""
    try:
        from app.database import SessionLocal
        from app.models.goal import GoalSheet
        from app.models.user import User
        from app.services.notification_service import send_email

        db = SessionLocal()
        sheets = db.query(GoalSheet).filter(GoalSheet.status == "submitted").all()
        email_tasks = []
        for sheet in sheets:
            if sheet.submitted_at:
                days_pending = (date.today() - sheet.submitted_at.date()).days
                if days_pending >= 5:
                    key = f"remind:approve:{sheet.id}"
                    if not redis_client.get(key):
                        redis_client.setex(key, 3 * 86400, "1")
                        emp = db.query(User).filter(User.id == sheet.employee_id).first()
                        if emp and emp.manager_id:
                            mgr = db.query(User).filter(User.id == emp.manager_id).first()
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
    """Check employees who haven't done check-ins after quarter opens."""
    try:
        from app.database import SessionLocal
        from app.models.cycle import Cycle
        from app.models.user import User
        from app.models.goal import GoalSheet, Goal, GoalAchievement
        from app.services.notification_service import notify_checkin_reminder

        db = SessionLocal()
        cycle = db.query(Cycle).filter(Cycle.is_active == True).first()
        if cycle:
            quarter = _current_quarter(cycle, date.today())
            if not quarter:
                db.close()
                return
            logger.info(f"Check-in reminder check for cycle {cycle.name}")
            employees = (
                db.query(User)
                .filter(User.role == "employee", User.is_active == True)
                .all()
            )
            email_tasks = []
            for emp in employees:
                sheets = (
                    db.query(GoalSheet)
                    .filter(
                        GoalSheet.employee_id == emp.id,
                        GoalSheet.cycle_id == cycle.id,
                        GoalSheet.status == "approved",
                    )
                    .all()
                )
                pending = False
                for sheet in sheets:
                    goals = db.query(Goal).filter(Goal.goal_sheet_id == sheet.id).all()
                    for goal in goals:
                        ach = (
                            db.query(GoalAchievement)
                            .filter(
                                GoalAchievement.goal_id == goal.id,
                                GoalAchievement.quarter == quarter,
                            )
                            .first()
                        )
                        if not _achievement_done(goal, ach):
                            pending = True
                            break
                    if pending:
                        break

                if pending:
                    key = f"remind:checkin:{emp.id}:{cycle.id}:{quarter}"
                    if not redis_client.get(key):
                        redis_client.setex(key, 3 * 86400, "1")
                        email_tasks.append(notify_checkin_reminder(emp.email, emp.full_name))

            if email_tasks:
                asyncio.run(asyncio.gather(*email_tasks))

        db.close()
    except Exception as e:
        logger.error(f"send_checkin_reminder error: {e}")


@celery.task
def run_escalations():
    """Load active escalation_rules, evaluate conditions, fire notifications."""
    try:
        from datetime import date
        from app.database import SessionLocal
        from app.models.audit import EscalationRule
        from app.models.goal import GoalSheet
        from app.models.goal import Goal, GoalAchievement
        from app.models.user import User
        from app.models.cycle import Cycle
        from app.services.notification_service import send_email

        db = SessionLocal()
        cycle = db.query(Cycle).filter(Cycle.is_active == True).first()
        if not cycle:
            db.close()
            return

        rules = db.query(EscalationRule).filter(EscalationRule.is_active == True).all()
        email_tasks = []
        for rule in rules:
            logger.info(f"Evaluating escalation rule: {rule.name}")
            if rule.trigger_event == "goal_not_submitted":
                days_open = (date.today() - cycle.goal_setting_open).days
                if days_open > rule.days_threshold:
                    emps = (
                        db.query(User)
                        .filter(User.role == "employee", User.is_active == True)
                        .all()
                    )
                    for emp in emps:
                        sheet = (
                            db.query(GoalSheet)
                            .filter(
                                GoalSheet.employee_id == emp.id,
                                GoalSheet.cycle_id == cycle.id,
                            )
                            .first()
                        )
                        if not sheet or sheet.status == "draft":
                            if rule.notify_employee:
                                key = f"escalate:submit:emp:{emp.id}:{cycle.id}"
                                if not redis_client.get(key):
                                    redis_client.setex(key, 3 * 86400, "1")
                                    email_tasks.append(
                                        send_email(
                                            emp.email,
                                            f"[Escalation] Overdue Goal Submission",
                                            f"Hello {emp.full_name}, your goal submission is overdue by {days_open} days.",
                                        )
                                    )
                            if rule.notify_manager and emp.manager_id:
                                mgr = (
                                    db.query(User)
                                    .filter(User.id == emp.manager_id)
                                    .first()
                                )
                                if mgr:
                                    key = f"escalate:submit:mgr:{emp.id}:{cycle.id}"
                                    if not redis_client.get(key):
                                        redis_client.setex(key, 3 * 86400, "1")
                                        email_tasks.append(
                                            send_email(
                                                mgr.email,
                                                f"[Escalation] Direct Report Overdue Goals",
                                                f"Hello {mgr.full_name}, {emp.full_name}'s goal submission is overdue.",
                                            )
                                        )
            elif rule.trigger_event == "goal_not_approved":
                sheets = (
                    db.query(GoalSheet)
                    .filter(
                        GoalSheet.cycle_id == cycle.id, GoalSheet.status == "submitted"
                    )
                    .all()
                )
                for sheet in sheets:
                    if sheet.submitted_at:
                        days_pending = (date.today() - sheet.submitted_at.date()).days
                        if days_pending > rule.days_threshold:
                            emp = (
                                db.query(User)
                                .filter(User.id == sheet.employee_id)
                                .first()
                            )
                            if emp and emp.manager_id:
                                mgr = (
                                    db.query(User)
                                    .filter(User.id == emp.manager_id)
                                    .first()
                                )
                                if mgr and rule.notify_manager:
                                    key = f"escalate:approve:mgr:{sheet.id}"
                                    if not redis_client.get(key):
                                        redis_client.setex(key, 3 * 86400, "1")
                                        email_tasks.append(
                                            send_email(
                                                mgr.email,
                                                f"[Escalation] Overdue Goal Approval",
                                                f"Hello {mgr.full_name}, you have a pending sheet from {emp.full_name} overdue by {days_pending} days.",
                                            )
                                        )
            elif rule.trigger_event == "checkin_not_done":
                quarter = _current_quarter(cycle, date.today())
                if not quarter:
                    continue
                open_date = getattr(cycle, f"{quarter}_open")
                days_open = (date.today() - open_date).days
                if days_open <= rule.days_threshold:
                    continue

                emps = (
                    db.query(User)
                    .filter(User.role == "employee", User.is_active == True)
                    .all()
                )
                for emp in emps:
                    sheets = (
                        db.query(GoalSheet)
                        .filter(
                            GoalSheet.employee_id == emp.id,
                            GoalSheet.cycle_id == cycle.id,
                            GoalSheet.status == "approved",
                        )
                        .all()
                    )
                    pending = False
                    for sheet in sheets:
                        goals = (
                            db.query(Goal).filter(Goal.goal_sheet_id == sheet.id).all()
                        )
                        for goal in goals:
                            ach = (
                                db.query(GoalAchievement)
                                .filter(
                                    GoalAchievement.goal_id == goal.id,
                                    GoalAchievement.quarter == quarter,
                                )
                                .first()
                            )
                            if not _achievement_done(goal, ach):
                                pending = True
                                break
                        if pending:
                            break

                    if not pending:
                        continue

                    if rule.notify_employee:
                        key = f"escalate:checkin:emp:{emp.id}:{cycle.id}:{quarter}"
                        if not redis_client.get(key):
                            redis_client.setex(key, 3 * 86400, "1")
                            email_tasks.append(
                                send_email(
                                    emp.email,
                                    "[Escalation] Overdue Check-in",
                                    f"Hello {emp.full_name}, your {quarter.upper()} check-in is overdue by {days_open} days.",
                                )
                            )
                    if rule.notify_manager and emp.manager_id:
                        mgr = db.query(User).filter(User.id == emp.manager_id).first()
                        if mgr:
                            key = f"escalate:checkin:mgr:{emp.id}:{cycle.id}:{quarter}"
                            if not redis_client.get(key):
                                redis_client.setex(key, 3 * 86400, "1")
                                email_tasks.append(
                                    send_email(
                                        mgr.email,
                                        "[Escalation] Direct Report Overdue Check-in",
                                        f"Hello {mgr.full_name}, {emp.full_name}'s {quarter.upper()} check-in is overdue.",
                                    )
                                )
                    if rule.notify_hr and settings.HR_EMAIL:
                        key = f"escalate:checkin:hr:{emp.id}:{cycle.id}:{quarter}"
                        if not redis_client.get(key):
                            redis_client.setex(key, 3 * 86400, "1")
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
