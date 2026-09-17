from fastapi import APIRouter

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("/", summary="Module scaffold placeholder")
async def scaffold() -> dict[str, str]:
    """Placeholder confirming the cart module is wired into the API.

    Replaced by real endpoints as this module's implementation phase
    begins (see docs/Implementation Plan.md).
    """
    return {"module": "cart", "status": "scaffolded"}
