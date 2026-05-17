"""Transactional outbox model for guaranteed async message delivery."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class OutboxEvent(Base):
    """SQLAlchemy model representing asynchronous events pending reliable broker delivery.

    Attributes:
        id: Primary key UUID.
        event_type: Identifier of the background task or notification event.
        payload: JSONB dictionary containing task arguments.
        status: Delivery progress ('pending', 'processing', 'completed', 'failed').
        created_at: UTC timestamp of event creation.
    """
    __tablename__ = "outbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_outbox_status_created", "status", "created_at"),
    )
