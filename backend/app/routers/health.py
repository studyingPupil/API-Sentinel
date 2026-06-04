"""Health check endpoint."""
from fastapi import APIRouter

from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version="0.1.0")
