from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class NewsletterSubscriber(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The homepage's 'Join the Circle' signup (Phase F1). Deliberately
    minimal — no double opt-in / campaign tooling, just enough that the
    homepage form isn't wired to nothing."""

    __tablename__ = "newsletter_subscribers"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
