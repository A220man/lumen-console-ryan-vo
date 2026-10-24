import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
import asyncio

from app.core.database import Base, get_db, override_engine
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.get_event_loop().run_until_complete(init_db())
    yield engine
    asyncio.get_event_loop().run_until_complete(engine.dispose())


@pytest.fixture
def db_session(engine):
    override_engine(engine)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async def get_session():
        async with async_session() as session:
            return session
    return asyncio.get_event_loop().run_until_complete(get_session())


@pytest.fixture
def client(db_session):
    from fastapi.testclient import TestClient

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Override settings for demo mode to avoid DB connection in lifespan
    from app.core.config import get_settings
    settings = get_settings()
    original_demo_mode = settings.demo_mode
    settings.demo_mode = True
    try:
        with TestClient(app) as c:
            yield c
    finally:
        settings.demo_mode = original_demo_mode
    app.dependency_overrides.clear()

