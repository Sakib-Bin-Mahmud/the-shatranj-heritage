import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.responses import success_envelope
from app.modules.auth.dependencies import require_permission
from app.modules.cms import service as cms_service
from app.modules.cms.schemas import CreatePageRequest, PageResponse, PageSummary, UpdatePageRequest

router = APIRouter(prefix="/content", tags=["Content"])
admin_router = APIRouter(prefix="/admin/content/pages", tags=["Admin - Content"])


@router.get("/pages")
async def list_pages(session: AsyncSession = Depends(get_db_session)) -> dict:
    """NFR-COM-001: an index of the published legal/policy pages."""
    pages = await cms_service.list_published_pages(session)
    return success_envelope(data=[PageSummary.model_validate(p).model_dump() for p in pages])


@router.get("/pages/{slug}")
async def get_page(slug: str, session: AsyncSession = Depends(get_db_session)) -> dict:
    """FR-CMS-004."""
    page = await cms_service.get_published_page_or_404(session, slug)
    return success_envelope(data=PageResponse.model_validate(page).model_dump())


@admin_router.get("", dependencies=[Depends(require_permission("cms.write"))])
async def admin_list_pages(session: AsyncSession = Depends(get_db_session)) -> dict:
    pages = await cms_service.admin_list_pages(session)
    return success_envelope(data=[PageSummary.model_validate(p).model_dump() for p in pages])


@admin_router.get("/{page_id}", dependencies=[Depends(require_permission("cms.write"))])
async def admin_get_page(
    page_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """Needed alongside admin_list_pages (which omits `body`, per
    PageSummary) so the admin UI can prefill an edit form — the public
    GET /content/pages/{slug} only ever returns published pages, so it
    can't stand in for this on a draft."""
    page = await cms_service.get_page_or_404(session, page_id)
    return success_envelope(data=PageResponse.model_validate(page).model_dump())


@admin_router.post("", status_code=201, dependencies=[Depends(require_permission("cms.write"))])
async def admin_create_page(
    payload: CreatePageRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """FR-CMS-004."""
    page = await cms_service.create_page(session, payload)
    await session.commit()
    return success_envelope(data=PageResponse.model_validate(page).model_dump())


@admin_router.patch("/{page_id}", dependencies=[Depends(require_permission("cms.write"))])
async def admin_update_page(
    page_id: uuid.UUID, payload: UpdatePageRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """FR-CMS-004."""
    page = await cms_service.update_page(session, page_id, payload)
    await session.commit()
    return success_envelope(data=PageResponse.model_validate(page).model_dump())
