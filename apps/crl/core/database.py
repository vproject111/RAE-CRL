import os

from typing import AsyncGenerator



from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from sqlalchemy.orm import sessionmaker

from sqlmodel import SQLModel



# Agnostic Database URL (Defaults to Docker Service, fallbacks to local SQLite)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///crl_local.db")



engine = create_async_engine(DATABASE_URL, echo=True, future=True)





async def init_db():

    """Initializes the database schema."""

    async with engine.begin() as conn:

        # For SQLite (Desktop App), we create tables directly without Alembic

        if "sqlite" in DATABASE_URL:

            await conn.run_sync(SQLModel.metadata.create_all)





async def get_session() -> AsyncGenerator[AsyncSession, None]:

    """Dependency for getting async DB session."""

    async_session = sessionmaker(

        engine, class_=AsyncSession, expire_on_commit=False  # type: ignore

    )

    async with async_session() as session:

        yield session


