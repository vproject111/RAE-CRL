from typing import List, Optional
from apps.crl.core.models import BaseArtifact, ArtifactType
from apps.crl.services.rae_client import RAEClient
from apps.crl.interfaces.storage import ArtifactRepository

class WatchdogService:
    """Orchestrates logical verification of research consistency."""

    def __init__(self, rae_client: RAEClient, repository: ArtifactRepository):
        self.rae_client = rae_client
        self.repo = repository

    async def check_consistency(self, artifact: BaseArtifact) -> Optional[str]:
        """Checks if a new artifact contradicts existing assumptions in the same project."""
        if artifact.type != ArtifactType.OBSERVATION:
            # We mostly care about Observations contradicting Hypotheses/Assumptions
            return None
        
        # 1. Fetch existing Assumptions and Hypotheses
        project_arts = await self.repo.list_by_project(artifact.project)
        context = [a for a in project_arts if a.type in [ArtifactType.ASSUMPTION, ArtifactType.HYPOTHESIS]]
        
        if not context:
            return None

        # 2. Ask RAE for conflict detection
        return await self.rae_client.detect_conflicts(artifact, context)
