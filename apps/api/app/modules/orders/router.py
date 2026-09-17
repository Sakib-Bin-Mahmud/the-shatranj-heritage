from fastapi import APIRouter

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", summary="Module scaffold placeholder")
async def scaffold() -> dict[str, str]:
    """Placeholder confirming the orders module is wired into the API.

    Replaced by real endpoints as this module's implementation phase
    begins (see docs/Implementation Plan.md).
    """
    return {"module": "orders", "status": "scaffolded"}
