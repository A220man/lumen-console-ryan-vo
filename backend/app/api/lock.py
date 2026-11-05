from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

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


class LockExportRequest(BaseModel):
    scope: SkillScope = SkillScope.PROJECT
    path: Optional[str] = None


class LockImportRequest(BaseModel):
    scope: SkillScope = SkillScope.PROJECT
    path: str
    force: bool = False


class CiInstallRequest(BaseModel):
    scope: SkillScope = SkillScope.PROJECT
    path: Optional[str] = None


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


@router.post("/export")
async def export_lock_file(
    request: LockExportRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: SkillService = Depends(get_skill_service),
):
    try:
        output_path = Path(request.path).resolve() if request.path else Path.cwd() / "skills-lock.json"
        await service.export_lock_file(user_id, request.scope, output_path)
        return {"message": f"Lock file exported to {output_path}", "path": str(output_path)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lock export failed: {e}")


@router.post("/import")
async def import_lock_file(
    request: LockImportRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: SkillService = Depends(get_skill_service),
):
    try:
        input_path = Path(request.path).resolve()
        results = await service.import_lock_file(user_id, request.scope, input_path, request.force)
        return {"results": results, "message": f"Lock file imported from {input_path}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lock import failed: {e}")


@router.post("/ci")
async def ci_install(
    request: CiInstallRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: SkillService = Depends(get_skill_service),
):
    try:
        lock_file_path = Path(request.path).resolve() if request.path else None
        results = await service.ci_install(user_id, request.scope, lock_file_path)
        return {"results": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CI install failed: {e}")

