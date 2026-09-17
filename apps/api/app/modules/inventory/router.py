from fastapi import APIRouter

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/", summary="Module scaffold placeholder")
async def scaffold() -> dict[str, str]:
    """Placeholder confirming the inventory module is wired into the API.

    Replaced by real endpoints as this module's implementation phase
    begins (see docs/Implementation Plan.md).
    """
    return {"module": "inventory", "status": "scaffolded"}
