"""Notification service — email sending and notification triggers."""

import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_email(to: str, subject: str, body_html: str):
    """Send an email using SMTP. Logs on failure, does not raise."""
    try:
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.info(f"Email skipped (no SMTP config): to={to}, subject={subject}")
            return
        import aiosmtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["From"] = settings.SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body_html, "html"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=True,
        )
        logger.info(f"Email sent to {to}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")


async def notify_goal_submitted(sheet_id: str, employee_email: str, employee_name: str, manager_email: str):
    """Notify manager that a goal sheet has been submitted."""
    subject = f"Action Required: Goal Sheet Submitted by {employee_name}"
    body = f"Hello,<br><br>{employee_name} ({employee_email}) has submitted their goal sheet for your review. Please log in to the portal to approve or return it."
    logger.info(f"Goal sheet {sheet_id} submitted — emailing manager at {manager_email}")
    await send_email(manager_email, subject, body)


async def notify_goal_approved(sheet_id: str, employee_email: str, manager_name: str):
    """Notify employee that their goal sheet has been approved."""
    subject = "Your Goal Sheet has been Approved"
    body = f"Hello,<br><br>Your goal sheet has been officially approved by {manager_name}."
    logger.info(f"Goal sheet {sheet_id} approved — emailing employee at {employee_email}")
    await send_email(employee_email, subject, body)


async def notify_goal_returned(sheet_id: str, employee_email: str, manager_name: str, comment: str):
    """Notify employee that their goal sheet has been returned."""
    subject = "Action Required: Goal Sheet Returned"
    body = f"Hello,<br><br>Your goal sheet has been returned by {manager_name} for rework.<br><br>Comment: {comment}"
    logger.info(f"Goal sheet {sheet_id} returned — emailing employee at {employee_email}")
    await send_email(employee_email, subject, body)


async def notify_checkin_reminder(employee_email: str, employee_name: str):
    """Notify employee about pending check-in."""
    subject = "Action Required: Goal Check-in Overdue"
    body = f"Hello {employee_name},<br><br>You have pending check-ins for your active goals. Please log in to submit your actuals."
    logger.info(f"Check-in reminder for {employee_email} — emailing employee")
    await send_email(employee_email, subject, body)
