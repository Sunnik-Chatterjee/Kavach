"""Database initialization.

Creates all tables from SQLAlchemy metadata on application startup.
No migrations are used — the ORM models are the source of truth.
"""

import app.models  # noqa: F401
from app.core.logging import get_logger
from app.database.base import Base
from app.database.session import engine

logger = get_logger(__name__)


async def init_db() -> None:
    """Create all tables if they do not already exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")
