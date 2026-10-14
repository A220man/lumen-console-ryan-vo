from fastapi import APIRouter
from app.core.config import get_settings
from app.schemas import HealthResponse

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        demo_mode=settings.demo_mode,
    )