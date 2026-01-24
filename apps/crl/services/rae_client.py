import httpx
import structlog
from typing import List, Optional
from uuid import UUID
from apps.crl.core.models import BaseArtifact

import os
logger = structlog.get_logger()

class RAEClient:
    """
    Adapter for communicating with RAE-Core.
    Agnostic to RAE deployment mode (Native/Docker).
    """
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("RAE_CORE_URL", "http://localhost:8000")).rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def store_artifact(self, artifact: BaseArtifact) -> bool:
        """Stores a research artifact as a semantic memory in RAE."""
        try:
            # Map Artifact -> RAE Memory Structure
            payload = {
                "content": f"[{artifact.type.upper()}] {artifact.title}\n\n{artifact.description}",
                "layer": "semantic",  # Research facts are semantic knowledge
                "tenant_id": "research-lab", # Default tenant for now
                "agent_id": artifact.author,
                "project": artifact.context.project_id,
                "metadata": {
                    "crl_id": str(artifact.id),
                    "crl_type": artifact.type,
                    "crl_metadata": artifact.metadata,
                    "related_artifacts": [str(uid) for uid in artifact.context.related_artifacts]
                },
                "tags": ["crl", artifact.type, artifact.context.project_id]
            }
            
            response = await self.client.post("/memories", json=payload)
            response.raise_for_status()
            logger.info("artifact_stored", id=str(artifact.id), type=artifact.type)
            return True
            
        except httpx.HTTPError as e:
            logger.error("rae_connection_failed", error=str(e))
            # TODO: Implement local caching for offline mode
            return False

    async def query_artifacts(self, query: str, project_id: str) -> List[dict]:
        """Retrieves artifacts relevant to the query."""
        try:
            payload = {
                "query": query,
                "project": project_id,
                "k": 10,
                "layers": ["semantic", "episodic"]
            }
            response = await self.client.post("/memories/query", json=payload)
            response.raise_for_status()
            return response.json().get("results", [])
        except httpx.HTTPError as e:
            logger.error("rae_query_failed", error=str(e))
            return []
