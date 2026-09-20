from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.rate_limit import rate_limit
from app.core.responses import success_envelope
from app.modules.newsletter import service as newsletter_service
from app.modules.newsletter.schemas import SubscribeRequest, SubscribeResponse

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


@router.post(
    "/subscribe",
    status_code=201,
    dependencies=[Depends(rate_limit("newsletter_subscribe", limit=10, window_seconds=60))],
)
async def subscribe(
    payload: SubscribeRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """Homepage "Join the Circle" section (Phase F1). Public, unauthenticated
    — anyone can subscribe an email address, same trust level as a
    mailing-list signup on any storefront."""
    subscriber = await newsletter_service.subscribe(session, payload.email)
    await session.commit()
    return success_envelope(
        data=SubscribeResponse(email=subscriber.email, is_active=subscriber.is_active).model_dump(),
        message="Subscribed.",
    )
