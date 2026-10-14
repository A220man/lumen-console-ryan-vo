import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, DateTime, Enum, Index, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, declared_attr
import uuid

from app.core.database import Base


class SkillScope(str, enum.Enum):
    PROJECT = "project"
    GLOBAL = "global"


class SkillStatus(str, enum.Enum):
    PENDING = "pending"
    INSTALLED = "installed"
    UPDATING = "updating"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sub = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    preferred_username = Column(String(255), nullable=True)
    roles = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    skills = relationship("Skill", back_populates="owner", cascade="all, delete-orphan")
    lock_files = relationship("LockFile", back_populates="owner", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    source_url = Column(Text, nullable=False)
    source_type = Column(String(50), nullable=False, default="github")
    skill_path = Column(String(500), nullable=False)
    skill_folder_hash = Column(String(64), nullable=False)
    scope = Column(Enum(SkillScope), nullable=False, default=SkillScope.PROJECT)
    status = Column(Enum(SkillStatus), nullable=False, default=SkillStatus.PENDING)
    target_path = Column(Text, nullable=True)
    skill_metadata = Column(Text, nullable=False, default="{}")
    installed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="skills")

    __table_args__ = (
        UniqueConstraint("owner_id", "name", "scope", name="uq_user_skill_scope"),
        Index("ix_skills_source_url", "source_url"),
    )


class LockFile(Base):
    __tablename__ = "lock_files"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    scope = Column(Enum(SkillScope), nullable=False, default=SkillScope.PROJECT)
    content = Column(Text, nullable=False)
    version = Column(String(20), nullable=False, default="3")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="lock_files")

    __table_args__ = (
        UniqueConstraint("owner_id", "scope", name="uq_user_lock_scope"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(255), nullable=True)
    details = Column(Text, nullable=False, default="{}")
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)