import asyncio
from datetime import datetime

import structlog
from sqlmodel import col, select

from apps.crl.core.database import get_session
from apps.crl.core.models import ArtifactVisibility, BaseArtifact
from apps.crl.services.rae_client import RAEClient
from apps.crl.services.storage.sql import SQLRepository

logger = structlog.get_logger()


class SyncEngine:
    """
    Background service that bridges local RAE-CRL artifacts to the RAE Hive Mind.
    Respects:
    1. Visibility (Private is never synced)
    2. Grace Period (Drafts are not synced until mature)
    """

    def __init__(self):
        self.client = RAEClient()
        self._running = False

    async def start(self, interval_seconds: int = 60):
        self._running = True
        logger.info("sync_engine_started", interval=interval_seconds)
        while self._running:
            try:
                await self.run_sync_cycle()
            except Exception as e:
                logger.error("sync_cycle_failed", error=str(e))
            await asyncio.sleep(interval_seconds)

    async def run_sync_cycle(self):
        try:
            async for session in get_session():
                repo = SQLRepository(session)

                # Logic: Find items needing sync
                # 1. Not Private
                # 2. Grace Period Over (or None)
                # 3. Updated since last sync

                now = datetime.utcnow()

                # Using SQLModel select
                # Note: Complex where clauses might need raw SQL in some ORMs, but SQLModel supports this.
                query = (
                    select(BaseArtifact)
                    .where(BaseArtifact.visibility != ArtifactVisibility.PRIVATE)
                    .where(
                        (BaseArtifact.grace_period_end == None)
                        | (BaseArtifact.grace_period_end < now)
                    )
                    .where(
                        (BaseArtifact.last_synced_at == None)
                        | (BaseArtifact.updated_at > BaseArtifact.last_synced_at)
                    )
                )

                result = await session.execute(query)
                artifacts = result.scalars().all()

                if not artifacts:
                    return

                logger.info("sync_candidates_found", count=len(artifacts))

                for artifact in artifacts:
                    success = await self.client.store_artifact(artifact)
                    if success:
                        artifact.last_synced_at = now
                        session.add(artifact)

                await session.commit()
                logger.info("sync_cycle_complete", synced=len(artifacts))
        except Exception as e:
            logger.error("sync_cycle_internal_error", error=str(e))


    def stop(self):
        self._running = False
