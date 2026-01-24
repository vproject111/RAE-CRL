import pytest
import respx
from httpx import Response

from apps.crl.core.models import ArtifactType, BaseArtifact
from apps.crl.services.rae_client import RAEClient


@pytest.mark.asyncio
async def test_store_artifact_success():
    async with respx.mock(base_url="http://test-rae") as respx_mock:
        # Mock successful response
        respx_mock.post("/memories").mock(
            return_value=Response(200, json={"status": "ok"})
        )

        client = RAEClient(base_url="http://test-rae")
        artifact = BaseArtifact(
            title="Test",
            type=ArtifactType.HYPOTHESIS,
            project_id="p1",
            description="Content",
        )

        success = await client.store_artifact(artifact)
        assert success is True
        assert respx_mock.calls.call_count == 1


@pytest.mark.asyncio
async def test_store_artifact_failure():
    async with respx.mock(base_url="http://test-rae") as respx_mock:
        # Mock 500 error
        respx_mock.post("/memories").mock(return_value=Response(500))

        client = RAEClient(base_url="http://test-rae")
        artifact = BaseArtifact(
            title="Test",
            type=ArtifactType.HYPOTHESIS,
            project_id="p1",
            description="desc",
        )

        success = await client.store_artifact(artifact)
        assert success is False  # Should catch exception and return False


@pytest.mark.asyncio
async def test_query_artifacts():
    async with respx.mock(base_url="http://test-rae") as respx_mock:
        mock_results = [{"content": "Result 1", "score": 0.9}]
        respx_mock.post("/memories/query").mock(
            return_value=Response(200, json={"results": mock_results})
        )

        client = RAEClient(base_url="http://test-rae")
        results = await client.query_artifacts("query", "p1")

        assert len(results) == 1
        assert results[0]["content"] == "Result 1"


@pytest.mark.asyncio
async def test_query_artifacts_failure():
    async with respx.mock(base_url="http://test-rae") as respx_mock:
        respx_mock.post("/memories/query").mock(return_value=Response(500))

        client = RAEClient(base_url="http://test-rae")
        results = await client.query_artifacts("query", "p1")

        assert results == []
