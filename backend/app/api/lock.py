from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import json

from app.core.database import get_db
from app.core.security import decrypt_token
from app.core.auth import get_userinfo
from app.models import LockFile, SkillScope, User
from app.schemas import LockFileRead, LockInstallRequest
from app.services.skill_service import SkillService, GitHubService

router = APIRouter()


async def get_current_user_id(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    access_token_cookie = request.cookies.get("access_token")
    if not access_token_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        access_token = decrypt_token(access_token_cookie)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    userinfo = await get_userinfo(access_token)
    result = await db.execute(select(User).where(User.sub == userinfo.sub))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id


def get_skill_service(db: AsyncSession = Depends(get_db)) -> SkillService:
    github = GitHubService()
    return SkillService(db, github)


@router.get("", response_model=LockFileRead)
async def get_lock_file(
    scope: SkillScope = SkillScope.PROJECT,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LockFile).where(LockFile.owner_id == user_id, LockFile.scope == scope)
    )
    lock_file = result.scalar_one_or_none()
    if not lock_file:
        raise HTTPException(status_code=404, detail="Lock file not found")
    data = json.loads(lock_file.content)
    return LockFileRead(
        version=lock_file.version,
        skills=data.get("skills", {}),
        dismissed=data.get("dismissed", {}),
        updated_at=lock_file.updated_at,
    )


@router.post("/install")
async def install_from_lock(
    request: LockInstallRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: SkillService = Depends(get_skill_service),
):
    try:
        results = await service.install_from_lock(
            user_id=user_id,
            scope=request.scope,
            force=request.force,
        )
        return {"results": results}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lock install failed: {e}")