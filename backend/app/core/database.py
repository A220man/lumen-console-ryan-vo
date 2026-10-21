from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from contextvars import ContextVar
from typing import Optional

from app.core.config import get_settings

settings = get_settings()

_engine: Optional[create_async_engine] = None
_async_session_maker: Optional[async_sessionmaker] = None


def get_engine() -> create_async_engine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.demo_mode,
            pool_pre_ping=True,
        )
    return _engine


def get_async_session_maker() -> async_sessionmaker:
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


def override_engine(engine):
    global _engine, _async_session_maker
    _engine = engine
    _async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with get_async_session_maker() as session:
        yield session


async def init_db() -> None:
    from app.core.config import get_settings
    settings = get_settings()
    if settings.demo_mode:
        # Use in-memory SQLite for demo mode
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.pool import StaticPool
        demo_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        async with demo_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await demo_engine.dispose()
    else:
        async with get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)