import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta
from apps.crl.core.models import BaseArtifact, ArtifactType, ArtifactStatus, ArtifactVisibility
from apps.crl.services.storage.sql import SQLRepository
from apps.crl.services.sync_service import SyncEngine
from apps.crl.mcp_server import fork_artifact, request_approval, approve_artifact

@pytest.mark.asyncio
async def test_sync_engine_logic():
    # Mock Repository and Session
    mock_session = AsyncMock()
    # Mock scalars().all() result
    mock_result = MagicMock()
    
    # Create artifacts: one ripe for sync, one still in grace period
    ripe_artifact = BaseArtifact(
        title="Mature Knowledge",
        type=ArtifactType.OBSERVATION,
        project_id="p1",
        visibility=ArtifactVisibility.TEAM,
        grace_period_end=datetime.utcnow() - timedelta(hours=1), # Expired grace
        last_synced_at=None
    )
    
    # Setup mock return
    mock_result.scalars.return_value.all.return_value = [ripe_artifact]
    mock_session.execute.return_value = mock_result
    
    # Mock RAEClient to avoid real HTTP calls
    with patch("apps.crl.services.sync_service.RAEClient") as MockClient:
        client_instance = MockClient.return_value
        client_instance.store_artifact = AsyncMock(return_value=True)
        
        # Patch get_session to yield our mock session
        with patch("apps.crl.services.sync_service.get_session") as mock_get_session:
            async def session_gen():
                yield mock_session
            mock_get_session.return_value = session_gen()
            
            # Run Sync
            engine = SyncEngine()
            await engine.run_sync_cycle()
            
            # Assertions
            # Should have called store_artifact once for the ripe artifact
            client_instance.store_artifact.assert_called_once()
            # Artifact should be updated with timestamp
            assert ripe_artifact.last_synced_at is not None
            # Session commit should be called
            mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_forking_logic():
    # Ideally integration test, but mocking for speed/safety here
    # Similar setup or use docker exec for integration (preferred)
    pass 
