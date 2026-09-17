from fastapi import APIRouter

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/", summary="Module scaffold placeholder")
async def scaffold() -> dict[str, str]:
    """Placeholder confirming the payments module is wired into the API.

    Replaced by real endpoints as this module's implementation phase
    begins (see docs/Implementation Plan.md).
    """
    return {"module": "payments", "status": "scaffolded"}
