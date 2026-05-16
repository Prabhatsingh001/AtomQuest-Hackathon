"""Audit service — append-only audit logging."""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def log_audit(
    db: Session,
    entity_type: str,
    entity_id: UUID,
    action: str,
    changed_by: UUID,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    reason: Optional[str] = None,
):
    """Create an append-only audit log entry recording a data mutation event.

    Args:
        db: Active database session.
        entity_type: Domain classification of the modified entity.
        entity_id: Unique UUID of the record being audited.
        action: Identifier describing the specific operation performed.
        changed_by: UUID of the user responsible for the action.
        old_value: Optional dictionary snapshot prior to modification.
        new_value: Optional dictionary snapshot after modification.
        reason: Optional text explanation provided for the change.
    """
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changed_by=changed_by,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
    )
    db.add(entry)
