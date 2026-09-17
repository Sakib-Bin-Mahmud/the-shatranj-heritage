from fastapi import APIRouter

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("/", summary="Module scaffold placeholder")
async def scaffold() -> dict[str, str]:
    """Placeholder confirming the catalog module is wired into the API.

    Replaced by real endpoints as this module's implementation phase
    begins (see docs/Implementation Plan.md).
    """
    return {"module": "catalog", "status": "scaffolded"}
