import asyncio
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.logging import configure_logging, get_logger
from app.core.responses import (
    http_exception_handler,
    success_envelope,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.modules.inventory.service import refresh_low_stock_gauge

settings = get_settings()
configure_logging()
logger = get_logger(__name__)

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment)

# NFR-MON-002 (alerting for low stock): the gauge itself lives in
# app/core/metrics.py; this loop is what keeps it fresh. A fixed
# interval rather than per-write updates, since it's a monitoring
# signal, not something any request path needs read-your-writes
# consistency on.
LOW_STOCK_GAUGE_REFRESH_SECONDS = 60


async def _low_stock_gauge_loop() -> None:
    while True:
        try:
            async with AsyncSessionLocal() as session:
                await refresh_low_stock_gauge(session)
        except Exception:
            logger.exception("low_stock_gauge_refresh_failed")
        await asyncio.sleep(LOW_STOCK_GAUGE_REFRESH_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_startup", environment=settings.environment)
    gauge_task = asyncio.create_task(_low_stock_gauge_loop())
    yield
    gauge_task.cancel()
    logger.info("app_shutdown")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# NFR-MON-001: request-level metrics (latency, count by path/method/
# status) exposed at /metrics for Prometheus to scrape. Business-level
# counters/gauges (orders, payment outcomes, low stock) are defined in
# app/core/metrics.py and incremented from the modules that own them.
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
async def health() -> dict:
    """Liveness/readiness probe. Deliberately has no DB/cache dependency
    so it stays truthful even if a downstream dependency is degraded
    (see NFR-AVL-003 — graceful degradation)."""
    return success_envelope(data={"status": "ok"}, message="Service is healthy.")
