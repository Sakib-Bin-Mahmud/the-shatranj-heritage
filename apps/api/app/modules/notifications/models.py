import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPrimaryKeyMixin


class NotificationLog(UUIDPrimaryKeyMixin, Base):
    """Sent/attempted notification record, per ERD §5.19. Written for
    every attempt regardless of outcome — `status='failed'` is how a
    broken channel becomes visible without ever blocking the
    operation that triggered the notification (NFR-AVL-003).
    """

    __tablename__ = "notifications_log"
    __table_args__ = (
        CheckConstraint("channel IN ('email', 'sms')", name="ck_notifications_log_channel"),
        CheckConstraint("status IN ('sent', 'failed')", name="ck_notifications_log_status"),
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    channel: Mapped[str] = mapped_column(String(10), nullable=False)
    template_code: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
