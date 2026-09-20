from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CmsPage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Static/policy page, per ERD §5.18. Only the `page_type='policy'`
    slice ships in Phase 7 (NFR-COM-001: Terms/Privacy/Return/Shipping/
    Warranty must be publishable before launch); `blog_posts` and the
    richer CMS around it stay V2 per docs/Implementation Plan.md.
    """

    __tablename__ = "cms_pages"
    __table_args__ = (
        CheckConstraint("page_type IN ('page', 'faq', 'policy')", name="ck_cms_pages_page_type"),
    )

    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    page_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
