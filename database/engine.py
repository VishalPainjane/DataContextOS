"""
Database engine setup — supports both PostgreSQL (prod) and SQLite (free/dev).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async database engine."""
    global _engine
    if _engine is None:
        url = settings.effective_database_url
        kwargs: dict = {
            "echo": settings.debug,
        }
        # SQLite needs special handling for async
        if "sqlite" in url:
            kwargs["connect_args"] = {"check_same_thread": False}
        else:
            kwargs["pool_size"] = 20
            kwargs["max_overflow"] = 10

        _engine = create_async_engine(url, **kwargs)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_session() -> AsyncSession:
    """Create a new async database session (for dependency injection)."""
    factory = get_session_factory()
    async with factory() as session:
        yield session  # type: ignore[misc]


async def init_db() -> None:
    """Initialize the database — create all tables."""
    from database.tables import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close the database engine."""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
