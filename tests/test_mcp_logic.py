from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from apps.crl.core.models import ArtifactStatus, ArtifactType, BaseArtifact
from apps.crl.mcp_server import (approve_artifact, fork_artifact,
                                 list_my_traces, quick_note, record_failure,
                                 refine_artifact, request_approval)


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda x: x)
    repo.get = AsyncMock()
    repo.link_artifacts = AsyncMock(return_value=True)
    repo.list_by_project = AsyncMock(return_value=[])
    return repo


async def mock_session_gen(session_mock):
    yield session_mock


@pytest.mark.asyncio
async def test_mcp_quick_note(mock_repo):
    with patch(
        "apps.crl.mcp_server.get_session", return_value=mock_session_gen(MagicMock())
    ):
        with patch("apps.crl.mcp_server.SQLRepository", return_value=mock_repo):
            result = await quick_note("My Idea", "p1")
            assert "Saved Trace" in result
            mock_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_mcp_refine_artifact(mock_repo):
    with patch(
        "apps.crl.mcp_server.get_session", return_value=mock_session_gen(MagicMock())
    ):
        with patch("apps.crl.mcp_server.SQLRepository", return_value=mock_repo):
            # Use real object logic
            art = BaseArtifact(title="T", type=ArtifactType.TRACE, project_id="p1")
            mock_repo.get.return_value = art

            result = await refine_artifact(
                art.id, ArtifactType.HYPOTHESIS, title="Better Title"
            )

            assert "Refined to hypothesis" in result
            assert art.status == ArtifactStatus.ACTIVE
            assert art.grace_period_end is None


@pytest.mark.asyncio
async def test_mcp_fork_artifact(mock_repo):
    with patch(
        "apps.crl.mcp_server.get_session", return_value=mock_session_gen(MagicMock())
    ):
        with patch("apps.crl.mcp_server.SQLRepository", return_value=mock_repo):
            original = BaseArtifact(
                title="O", type=ArtifactType.HYPOTHESIS, project_id="p1"
            )
            mock_repo.get.return_value = original
            mock_repo.save.side_effect = lambda x: x  # Identity

            result = await fork_artifact(original.id, "New Guy", "Disagree")

            assert "Fork created" in result
            mock_repo.link_artifacts.assert_called_once()


@pytest.mark.asyncio
async def test_mcp_approval_flow(mock_repo):
    # side_effect allows recreating the generator for each call
    with patch(
        "apps.crl.mcp_server.get_session",
        side_effect=lambda: mock_session_gen(MagicMock()),
    ):
        with patch("apps.crl.mcp_server.SQLRepository", return_value=mock_repo):
            # Use real object logic
            art = BaseArtifact(title="A", type=ArtifactType.HYPOTHESIS, project_id="p1")
            mock_repo.get.return_value = art
            mock_repo.save.side_effect = lambda x: x

            res1 = await request_approval(art.id, "Boss")
            assert "Submitted" in res1
            assert art.proposed_by is not None

            res2 = await approve_artifact(art.id, "Boss")
            assert "APPROVED" in res2
            assert art.approved_by == "Boss"
            assert art.status == ArtifactStatus.ACTIVE


@pytest.mark.asyncio
async def test_mcp_record_failure(mock_repo):
    with patch(
        "apps.crl.mcp_server.get_session", return_value=mock_session_gen(MagicMock())
    ):
        with patch("apps.crl.mcp_server.SQLRepository", return_value=mock_repo):
            art = BaseArtifact(title="F", type=ArtifactType.EXPERIMENT, project_id="p1")
            mock_repo.get.return_value = art

            await record_failure(uuid4(), "Explosion")
            assert art.status == ArtifactStatus.FAILED_BUT_INFORMATIVE
            assert art.metadata_blob["failure_reason"] == "Explosion"


@pytest.mark.asyncio
async def test_mcp_list_traces(mock_repo):
    with patch(
        "apps.crl.mcp_server.get_session", return_value=mock_session_gen(MagicMock())
    ):
        with patch("apps.crl.mcp_server.SQLRepository", return_value=mock_repo):
            res = await list_my_traces("p1")
            assert "No pending traces" in res
