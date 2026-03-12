import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base, get_db
from app.main import app
from app.settings import settings

# Derive test DB URL from the configured DATABASE_URL so the host/port/credentials
# stay consistent whether running locally or inside Docker.
_base_url = settings.database_url.rsplit("/", 1)[0]
PROD_DB_URL = settings.database_url
TEST_DB_URL = f"{_base_url}/trendit_test"


@pytest_asyncio.fixture
async def test_engine():
    # Ensure trendit_test database exists and is clean.
    # Connect via the prod DB so we can run admin commands.
    prod_engine = create_async_engine(PROD_DB_URL, isolation_level="AUTOCOMMIT")
    async with prod_engine.connect() as conn:
        exists = (await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'trendit_test'")
        )).fetchone()
        if not exists:
            await conn.execute(text("CREATE DATABASE trendit_test"))
        else:
            # Terminate any stale connections left by crashed test runs so that
            # DROP TABLE won't hang waiting for their locks to be released.
            await conn.execute(text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = 'trendit_test' AND pid <> pg_backend_pid()"
            ))
    await prod_engine.dispose()

    # Fresh schema for each test
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_engine):
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def register_and_login(
    client: AsyncClient,
    email: str = "user@test.com",
    password: str = "password123",
) -> dict[str, str]:
    await client.post("/auth/register", json={"email": email, "password": password})
    response = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
