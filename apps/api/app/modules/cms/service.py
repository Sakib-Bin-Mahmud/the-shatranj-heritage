import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import AppError
from app.modules.cms.models import CmsPage
from app.modules.cms.schemas import CreatePageRequest, UpdatePageRequest


async def _check_slug_available(
    session: AsyncSession, slug: str, exclude_id: uuid.UUID | None = None
) -> None:
    query = select(CmsPage).where(CmsPage.slug == slug)
    if exclude_id:
        query = query.where(CmsPage.id != exclude_id)
    if await session.scalar(query):
        raise AppError(
            status_code=409, code="SLUG_ALREADY_EXISTS", message="Slug is already in use."
        )


async def get_published_page_or_404(session: AsyncSession, slug: str) -> CmsPage:
    page = await session.scalar(
        select(CmsPage).where(CmsPage.slug == slug, CmsPage.is_published.is_(True))
    )
    if not page:
        raise AppError(status_code=404, code="NOT_FOUND", message="Page not found.")
    return page


async def list_published_pages(session: AsyncSession) -> list[CmsPage]:
    return list(
        await session.scalars(
            select(CmsPage).where(CmsPage.is_published.is_(True)).order_by(CmsPage.title)
        )
    )


async def get_page_or_404(session: AsyncSession, page_id: uuid.UUID) -> CmsPage:
    page = await session.get(CmsPage, page_id)
    if not page:
        raise AppError(status_code=404, code="NOT_FOUND", message="Page not found.")
    return page


async def admin_list_pages(session: AsyncSession) -> list[CmsPage]:
    return list(await session.scalars(select(CmsPage).order_by(CmsPage.title)))


async def create_page(session: AsyncSession, data: CreatePageRequest) -> CmsPage:
    await _check_slug_available(session, data.slug)
    page = CmsPage(**data.model_dump())
    if page.is_published:
        page.published_at = datetime.now(UTC)
    session.add(page)
    await session.flush()
    return page


async def update_page(
    session: AsyncSession, page_id: uuid.UUID, data: UpdatePageRequest
) -> CmsPage:
    page = await get_page_or_404(session, page_id)
    updates = data.model_dump(exclude_unset=True)

    was_published = page.is_published
    for field, value in updates.items():
        setattr(page, field, value)

    if page.is_published and not was_published:
        page.published_at = datetime.now(UTC)
    elif not page.is_published:
        page.published_at = None

    await session.flush()
    return page
