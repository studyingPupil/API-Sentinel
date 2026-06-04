"""System settings CRUD. Placeholder — full implementation in Phase 3."""
from fastapi import APIRouter
from app.config import DEFAULT_SYNC_INTERVAL_MINUTES

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings():
    return {
        "sync_interval_minutes": DEFAULT_SYNC_INTERVAL_MINUTES,
    }
