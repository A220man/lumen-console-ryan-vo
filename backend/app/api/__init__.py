from fastapi import APIRouter

from app.api import auth, skills, lock, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(lock.router, prefix="/lock", tags=["lock"])