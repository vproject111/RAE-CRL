from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

# Agnostic Database URL (Defaults to Docker Service, fallbacks to local SQLite)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite+aiosqlite:///crl_local.db"
)

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async def init_db():
    """Initializes the database schema."""
    async with engine.begin() as conn:
        # For SQLite (Desktop App), we create tables directly without Alembic
        if "sqlite" in DATABASE_URL:
            await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency for getting async DB session."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
