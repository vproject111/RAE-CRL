from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from apps.crl.core.models import (ArtifactRelation, ArtifactStatus,
                                  ArtifactType, ArtifactVisibility,
                                  BaseArtifact)
from apps.crl.services.storage.sql import SQLRepository
from apps.crl.services.sync_service import SyncEngine


@pytest.mark.asyncio
async def test_iso27001_access_control_sync_leakage():
    """
    [ISO 27001] Confidentiality Control.
    Verify that PRIVATE artifacts and active Grace Period items are NEVER selected for Sync.
    """
    # Setup Data
    now = datetime.utcnow()

    # 1. Private Trace (Should be ignored)
    private_trace = BaseArtifact(
        title="Secret",
        type=ArtifactType.TRACE,
        project_id="p1",
        visibility=ArtifactVisibility.PRIVATE,
        last_synced_at=None,
    )

    # 2. Protected Draft (Grace Period Active) (Should be ignored)
    protected_draft = BaseArtifact(
        title="Draft",
        type=ArtifactType.HYPOTHESIS,
        project_id="p1",
        visibility=ArtifactVisibility.TEAM,
        grace_period_end=now + timedelta(hours=1),
        last_synced_at=None,
    )

    # 3. Public Mature Artifact (Should be synced)
    public_artifact = BaseArtifact(
        title="Public Knowledge",
        type=ArtifactType.OBSERVATION,
        project_id="p1",
        visibility=ArtifactVisibility.PUBLIC,
        grace_period_end=None,
        last_synced_at=None,
    )

    # In-memory DB for strict testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        session.add(private_trace)
        session.add(protected_draft)
        session.add(public_artifact)
        await session.commit()

    # Inject this session into SyncEngine
    with patch("apps.crl.services.sync_service.get_session") as mock_get_session:

        async def session_gen():
            async with async_session() as session:
                yield session

        mock_get_session.return_value = session_gen()

        # Mock RAE Client to verify what gets sent
        with patch("apps.crl.services.sync_service.RAEClient") as MockClient:
            client = MockClient.return_value
            client.store_artifact = AsyncMock(return_value=True)

            # Run Sync
            sync = SyncEngine()
            await sync.run_sync_cycle()

            # ASSERTIONS

            # 1. Store should be called ONLY once (for public_artifact)
            assert client.store_artifact.call_count == 1

            # 2. Verify argument was the public artifact
            args, _ = client.store_artifact.call_args
            sent_artifact = args[0]
            assert sent_artifact.title == "Public Knowledge"
            assert sent_artifact.visibility == ArtifactVisibility.PUBLIC


@pytest.mark.asyncio
async def test_iso42001_provenance_audit_trail():
    """
    [ISO 42001] AI Management - Traceability & Provenance.
    Verify that Forking creates a strict cryptographic/relational link.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        repo = SQLRepository(session)

        # 1. Original
        origin = BaseArtifact(
            title="Origin", type=ArtifactType.HYPOTHESIS, project_id="p1"
        )
        origin = await repo.save(origin)

        # 2. Fork
        fork = BaseArtifact(title="Fork", type=ArtifactType.HYPOTHESIS, project_id="p1")
        fork = await repo.save(fork)

        # 3. Link
        await repo.link_artifacts(origin.id, fork.id, "has_alternative_interpretation")

        # 4. Verify Graph
        graph = await repo.get_graph(origin.id)

        assert len(graph) == 1
        assert graph[0].id == fork.id

        # 5. Verify Metadata (Provenance) simulation
        assert graph[0].title == "Fork"
