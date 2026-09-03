"""Database engine, session management, and base declarative class."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


def get_database_url() -> str:
    """Construct async PostgreSQL connection string from environment variables."""
    url = os.getenv("DATABASE_URL")
    if url:
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    user = os.getenv("POSTGRES_USER", "enum_admin")
    password = os.getenv("POSTGRES_PASSWORD", "enum_secure_password_dev")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "enum_tip")

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


engine: AsyncEngine = create_async_engine(
    get_database_url(),
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for FastAPI route handlers."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
