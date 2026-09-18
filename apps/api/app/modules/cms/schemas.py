import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreatePageRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=150)
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    page_type: str = Field(default="policy", pattern="^(page|faq|policy)$")
    is_published: bool = False


class UpdatePageRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1)
    page_type: str | None = Field(default=None, pattern="^(page|faq|policy)$")
    is_published: bool | None = None


class PageResponse(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    body: str
    page_type: str
    is_published: bool
    published_at: datetime | None

    model_config = {"from_attributes": True}


class PageSummary(BaseModel):
    """List shape (admin listing, and the public index) — omits `body`
    since a listing doesn't need the full page content."""

    id: uuid.UUID
    slug: str
    title: str
    page_type: str
    is_published: bool
    published_at: datetime | None

    model_config = {"from_attributes": True}
