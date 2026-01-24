import pytest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from apps.crl.core.models import ArtifactType, BaseArtifact
from apps.crl.services.storage.sql import SQLRepository


@pytest.fixture
async def memory_repo():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield SQLRepository(session)


@pytest.mark.asyncio
async def test_save_and_get(memory_repo):
    repo = memory_repo  # Direct access because pytest-asyncio handles async fixtures

    art = BaseArtifact(title="T1", type=ArtifactType.TRACE, project_id="p1")
    saved = await repo.save(art)

    fetched = await repo.get(saved.id)
    assert fetched.title == "T1"


@pytest.mark.asyncio
async def test_link_artifacts_rollback_on_error(memory_repo):
    repo = memory_repo
    # Force a failure by providing non-existent UUIDs if constraints exist, 
    # or mock the commit to fail.
    with patch.object(repo.session, 'commit', side_effect=Exception("DB Error")):
        success = await repo.link_artifacts(uuid4(), uuid4(), "test")
        assert success is False

@pytest.mark.asyncio
async def test_list_by_project_filtering(memory_repo):
    repo = memory_repo

    await repo.save(BaseArtifact(title="A1", type=ArtifactType.TRACE, project_id="p1"))
    await repo.save(
        BaseArtifact(title="A2", type=ArtifactType.HYPOTHESIS, project_id="p1")
    )
    await repo.save(BaseArtifact(title="B1", type=ArtifactType.TRACE, project_id="p2"))

    # Filter by project
    p1_items = await repo.list_by_project("p1")
    assert len(p1_items) == 2

    # Filter by project + type
    p1_traces = await repo.list_by_project("p1", type=ArtifactType.TRACE)
    assert len(p1_traces) == 1
    assert p1_traces[0].title == "A1"
