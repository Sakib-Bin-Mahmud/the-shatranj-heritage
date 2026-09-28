from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.newsletter.models import NewsletterSubscriber


async def subscribe(session: AsyncSession, email: str) -> NewsletterSubscriber:
    """Idempotent: re-subscribing an address is a normal, expected retry
    (double form submit, resubmitting after leaving the page), not an
    error — and reactivates an address that had previously unsubscribed."""
    normalized_email = email.strip().lower()
    subscriber = await session.scalar(
        select(NewsletterSubscriber).where(NewsletterSubscriber.email == normalized_email)
    )
    if subscriber:
        subscriber.is_active = True
        await session.flush()
        return subscriber

    subscriber = NewsletterSubscriber(email=normalized_email, is_active=True)
    session.add(subscriber)
    await session.flush()
    return subscriber
