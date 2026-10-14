from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID


class SkillScope(str, Enum):
    PROJECT = "project"
    GLOBAL = "global"


class SkillStatus(str, Enum):
    PENDING = "pending"
    INSTALLED = "installed"
    UPDATING = "updating"
    FAILED = "failed"


class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_url: HttpUrl
    source_type: str = "github"
    skill_path: str = Field(..., min_length=1, max_length=500)
    scope: SkillScope = SkillScope.PROJECT


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    source_url: Optional[HttpUrl] = None
    skill_path: Optional[str] = Field(None, min_length=1, max_length=500)
    scope: Optional[SkillScope] = None


class SkillRead(SkillBase):
    id: UUID
    owner_id: UUID
    skill_folder_hash: str
    status: SkillStatus
    target_path: Optional[str] = None
    metadata: str
    installed_at: Optional[datetime] = None
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    items: list[SkillRead]
    total: int
    page: int
    page_size: int


class SkillSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    owner: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class SkillSearchResult(BaseModel):
    id: UUID
    name: str
    owner: str
    description: Optional[str] = None
    source_url: str
    tags: list[str] = []


class InstallRequest(BaseModel):
    source_url: HttpUrl
    skill_name: str = Field(..., min_length=1)
    skill_path: Optional[str] = None
    scope: SkillScope = SkillScope.PROJECT
    force: bool = False


class InstallResponse(BaseModel):
    skill: SkillRead
    lock_file_updated: bool


class UpdateRequest(BaseModel):
    force: bool = False


class LockFileRead(BaseModel):
    version: str
    skills: dict
    dismissed: dict
    updated_at: datetime


class LockInstallRequest(BaseModel):
    scope: SkillScope = SkillScope.PROJECT
    force: bool = False


class HealthResponse(BaseModel):
    status: str
    version: str
    demo_mode: bool


class AuthURLResponse(BaseModel):
    auth_url: str
    state: str
    nonce: str
    code_verifier: str


class CallbackRequest(BaseModel):
    code: str
    state: str
    code_verifier: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class UserRead(BaseModel):
    id: UUID
    sub: str
    email: Optional[str] = None
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    roles: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None