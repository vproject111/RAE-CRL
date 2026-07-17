import os
from typing import List, Optional, cast
from uuid import UUID

import httpx
import structlog

from apps.crl.core.models import BaseArtifact

logger = structlog.get_logger()


class RAEClient:
    """
    Adapter for communicating with RAE-Core.
    Agnostic to RAE deployment mode (Native/Docker).
    """

    base_url: str

    def __init__(self, base_url: Optional[str] = None):
        url = base_url or os.getenv("RAE_CORE_URL", "http://localhost:8000")
        self.base_url = cast(str, url).rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def store_artifact(self, artifact: BaseArtifact) -> bool:
        """Stores a research artifact as a semantic memory in RAE."""
        try:
            # Map Artifact -> RAE Memory Structure
            payload = {
                "content": f"[{artifact.type.upper()}] {artifact.title}\n\n{artifact.description}",
                "layer": "semantic",  # Research facts are semantic knowledge
                "tenant_id": "research-lab",  # Default tenant for now
                "agent_id": artifact.author,
                "project": artifact.project,
                "metadata": {
                    "crl_id": str(artifact.id),
                    "crl_type": artifact.type,
                    "crl_metadata": artifact.metadata_blob,
                    # Relations are handled via graph, not direct context in new model
                },
                "tags": ["crl", artifact.type, artifact.project],
            }

            response = await self.client.post("/memories", json=payload)
            response.raise_for_status()
            logger.info("artifact_stored", id=str(artifact.id), type=artifact.type)
            return True

        except httpx.HTTPError as e:
            logger.error("rae_connection_failed", error=str(e))
            # TODO: Implement local caching for offline mode
            return False

    async def query_artifacts(self, query: str, project: str) -> List[dict]:
        """Retrieves artifacts relevant to the query."""
        try:
            payload = {
                "query": query,
                "project": project,
                "k": 10,
                "layers": ["semantic", "episodic"],
            }
            response = await self.client.post("/memories/query", json=payload)
            response.raise_for_status()
            return response.json().get("results", [])
        except httpx.HTTPError as e:
            logger.error("rae_query_failed", error=str(e))
            return []

    async def global_search(self, query: str) -> List[dict]:
        """Queries the entire Hive Mind (all projects) for related knowledge."""
        try:
            payload = {
                "query": query,
                "k": 5,
                "layers": ["semantic", "reflective"],
            }
            response = await self.client.post("/memories/query", json=payload)
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception as e:
            logger.error("global_search_failed", error=str(e))
            return []

    async def detect_conflicts(
        self, target: BaseArtifact, context: List[BaseArtifact]
    ) -> Optional[str]:
        """Uses RAE-Core's LLM capabilities to detect logical conflicts between artifacts."""
        if not context:
            return None

        # Build prompt for RAE
        context_str = "\n".join(
            [f"- [{a.type}] {a.title}: {a.description}" for a in context]
        )
        prompt = f"""Analyze the following research context and the new item. 
Is there any logical contradiction or violation of assumptions?

CONTEXT:
{context_str}

NEW ITEM:
[{target.type}] {target.title}
{target.description}

If there is a conflict, explain it concisely. If no conflict, respond with 'NONE'."""

        try:
            # Route through the v2 Agent execution endpoint
            payload = {
                "prompt": prompt,
                "project": target.project,
                "metadata": {
                    "system_prompt": "You are a scientific reasoning auditor. Be critical and precise."
                },
            }
            response = await self.client.post("/agent/execute", json=payload)
            response.raise_for_status()
            result = response.json().get("answer", "NONE")

            if "NONE" in result.upper():
                return None
            return result
        except Exception as e:
            logger.error("conflict_detection_failed", error=str(e))
            return None
