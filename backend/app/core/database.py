from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from app.core.logging import logger

# Create Async SQLAlchemy Engine
try:
    engine = create_async_engine(
        settings.async_database_url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True
    )
except ModuleNotFoundError as e:
    if "asyncpg" in str(e):
        logger.warning("asyncpg driver not found in Python environment. Falling back to sqlite+aiosqlite.")
        engine = create_async_engine(
            "sqlite+aiosqlite:///./dev_fallback.db",
            echo=settings.DEBUG,
            future=True
        )
    else:
        raise

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

from app.models.base import Base

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing asynchronous database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session rollback due to error: {str(e)}")
            raise
        finally:
            await session.close()
