from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


def success_envelope(data: Any = None, message: str = "Request completed successfully.") -> dict:
    """Standard success shape, per docs/API Specification.md §8."""
    return {"success": True, "message": message, "data": data}


def error_envelope(code: str, message: str) -> dict:
    """Standard error shape, per docs/API Specification.md §8."""
    return {"success": False, "error": {"code": code, "message": message}}


class AppError(HTTPException):
    """Raise this instead of plain HTTPException when the API Specification
    names a specific error code (e.g. `EMAIL_ALREADY_EXISTS`,
    `INVALID_CREDENTIALS`) rather than the generic `HTTP_<status>` fallback.
    """

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail=message)
        self.code = code


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = getattr(exc, "code", None) or f"HTTP_{exc.status_code}"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(code=code, message=str(exc.detail)),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_envelope(
            code="VALIDATION_ERROR",
            message=jsonable_encoder(exc.errors()),
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", path=str(request.url))
    return JSONResponse(
        status_code=500,
        content=error_envelope(
            code="INTERNAL_SERVER_ERROR", message="An unexpected error occurred."
        ),
    )
