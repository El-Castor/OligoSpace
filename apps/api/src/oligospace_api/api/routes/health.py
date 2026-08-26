from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.db.session import get_session

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"code": "database_unavailable"}) from exc
    return {"status": "ready"}
