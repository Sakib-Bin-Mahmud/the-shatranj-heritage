from fastapi import APIRouter

router = APIRouter(prefix="/cms", tags=["CMS"])


@router.get("/", summary="Module scaffold placeholder")
async def scaffold() -> dict[str, str]:
    """Placeholder confirming the cms module is wired into the API.

    Replaced by real endpoints as this module's implementation phase
    begins (see docs/Implementation Plan.md).
    """
    return {"module": "cms", "status": "scaffolded"}
