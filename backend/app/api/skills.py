from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_userinfo
from app.core.security import decrypt_token
from app.models import Skill, SkillStatus, SkillScope, User
from app.schemas import (
    SkillCreate,
    SkillUpdate,
    SkillRead,
    SkillListResponse,
    SkillSearchRequest,
    SkillSearchResult,
    InstallRequest,
    InstallResponse,
    UpdateRequest,
    ErrorResponse,
)
from app.services.skill_service import SkillService, GitHubService

router = APIRouter()


async def get_current_user_id(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UUID:
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


@router.get("", response_model=SkillListResponse)
async def list_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scope: SkillScope | None = None,
    status: SkillStatus | None = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = select(Skill).where(Skill.owner_id == user_id)
    if scope:
        query = query.where(Skill.scope == scope)
    if status:
        query = query.where(Skill.status == status)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.order_by(Skill.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    skills = result.scalars().all()

    return SkillListResponse(
        items=[SkillRead.model_validate(s) for s in skills],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/search", response_model=list[SkillSearchResult])
async def search_skills(
    q: str = Query(..., min_length=1),
    owner: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = select(Skill).where(
        Skill.owner_id == user_id,
        Skill.status == SkillStatus.INSTALLED,
    )

    if owner:
        query = query.where(Skill.source_url.ilike(f"%/{owner}/%"))

    search_term = f"%{q}%"
    query = query.where(
        (Skill.name.ilike(search_term)) |
        (Skill.skill_metadata.ilike(search_term))
    )

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    skills = result.scalars().all()

    results = []
    for skill in skills:
        import json
        meta = json.loads(skill.skill_metadata) if skill.skill_metadata else {}
        results.append(SkillSearchResult(
            id=skill.id,
            name=skill.name,
            owner=skill.source_url.split("/")[-2] if "/" in skill.source_url else "",
            description=meta.get("description"),
            source_url=skill.source_url,
            tags=meta.get("tags", []),
        ))

    return results


@router.get("/{skill_id}", response_model=SkillRead)
async def get_skill(
    skill_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Skill).where(Skill.id == skill_id, Skill.owner_id == user_id)
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return SkillRead.model_validate(skill)


@router.post("/install", response_model=InstallResponse)
async def install_skill(
    request: InstallRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: SkillService = Depends(get_skill_service),
):
    try:
        skill, lock_updated = await service.install_skill(
            user_id=user_id,
            source_url=str(request.source_url),
            skill_name=request.skill_name,
            skill_path=request.skill_path,
            scope=request.scope,
            force=request.force,
        )
        return InstallResponse(skill=SkillRead.model_validate(skill), lock_file_updated=lock_updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Installation failed: {e}")


@router.post("/{skill_id}/update")
async def update_skill(
    skill_id: UUID,
    request: UpdateRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: SkillService = Depends(get_skill_service),
):
    try:
        result = await service.update_skill(user_id, skill_id, request.force)
        if result["status"] == "up_to_date":
            return {"message": "Skill is up to date", "skill": SkillRead.model_validate(result["skill"])}
        return {"message": "Skill updated", "skill": SkillRead.model_validate(result["skill"])}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {e}")


@router.get("/{skill_id}/check-update")
async def check_skill_update(
    skill_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: SkillService = Depends(get_skill_service),
):
    from app.models import Skill
    from sqlalchemy import select

    result = await db.execute(select(Skill).where(Skill.id == skill_id, Skill.owner_id == user_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    return {"skill_id": str(skill_id), "update_available": False}