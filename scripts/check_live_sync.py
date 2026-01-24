import asyncio
import os
from datetime import datetime, timedelta
from uuid import uuid4

import structlog

from apps.crl.core.database import get_session
from apps.crl.core.models import (ArtifactStatus, ArtifactType,
                                  ArtifactVisibility, BaseArtifact)
from apps.crl.services.rae_client import RAEClient
from apps.crl.services.storage.sql import SQLRepository
from apps.crl.services.sync_service import SyncEngine

# Setup Logger
structlog.configure(processors=[structlog.processors.JSONRenderer()])
logger = structlog.get_logger()


async def live_check():
    print("--- 🚀 STARTING LIVE SYNC CHECK ---")

    # 1. Create a Test Artifact (Ready for Sync)
    artifact_id = uuid4()
    project_id = f"live-check-{datetime.utcnow().timestamp()}"

    print(f"1. Creating Artifact {artifact_id} in Project {project_id}...")

    async for session in get_session():
        repo = SQLRepository(session)
        art = BaseArtifact(
            id=artifact_id,
            type=ArtifactType.OBSERVATION,
            title="Live Sync Check Artifact",
            description="This is a test to verify CRL -> RAE connection.",
            project_id=project_id,
            status=ArtifactStatus.ACTIVE,
            visibility=ArtifactVisibility.TEAM,  # Must be Public/Team to sync
            grace_period_end=None,  # Immediate sync
            author="tester",
        )
        await repo.save(art)
        print("   ✅ Saved to Local DB (Postgres).")
        break

    # 2. Run Sync Engine
    print("2. Running Sync Engine Cycle...")
    sync = SyncEngine()
    try:
        await sync.run_sync_cycle()
        print("   ✅ Sync Cycle Completed without error.")
    except Exception as e:
        print(f"   ❌ Sync Failed: {e}")
        return

    # 3. Verify Local Status (Updated last_synced_at)
    async for session in get_session():
        repo = SQLRepository(session)
        loaded = await repo.get(artifact_id)
        if loaded.last_synced_at:
            print(f"   ✅ Local DB updated: last_synced_at = {loaded.last_synced_at}")
        else:
            print("   ❌ Local DB NOT updated (Sync likely failed silently).")
            return
        break

    # 4. Verify Remote RAE (Query)
    print("3. Verifying Memory in RAE Core...")
    client = RAEClient()
    # Wait a bit for RAE to index (if async)
    await asyncio.sleep(2)

    try:
        results = await client.query_artifacts("Live Sync Check", project_id)
        found = any(
            r.get("content", "").startswith("[OBSERVATION] Live Sync Check")
            for r in results
        )

        if found:
            print("   ✅ SUCCESS! RAE Core returned the artifact.")
        else:
            print(
                "   ⚠️  WARNING: RAE Core returned results, but specific artifact not found (Index lag?)."
            )
            print(f"      Results: {results}")
    except Exception as e:
        print(f"   ❌ Query Failed: {e}")


if __name__ == "__main__":
    asyncio.run(live_check())
