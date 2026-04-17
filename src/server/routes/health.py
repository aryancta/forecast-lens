from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_session
from ..schemas import HealthResponse
from ..services.sync import get_last_sync


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_session)) -> HealthResponse:
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    last_sync_at, _job_id = get_last_sync()
    return HealthResponse(
        status="ok",
        db=db_status,
        last_sync_at=last_sync_at,
        version=settings.version,
    )
