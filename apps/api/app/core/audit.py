import uuid
from datetime import datetime
from typing import Any, Literal

from sqlalchemy import CheckConstraint, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ActorType = Literal["admin", "system"]


class AuditLog(Base):
    """Admin/system action audit trail, per ERD §5.20 and NFR-AUD-001.

    Deliberately not used for customer self-service actions or failed
    login attempts (which would require `entity_id` to be nullable) —
    those go through structured application logs instead. See
    docs/Implementation Plan.md Phase 1 for the scoping rationale.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint("actor_type IN ('admin', 'system')", name="ck_audit_logs_actor_type"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    actor_type: Mapped[str] = mapped_column(String(10), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


async def record_audit_log(
    session: AsyncSession,
    *,
    actor_type: ActorType,
    actor_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
        )
    )
