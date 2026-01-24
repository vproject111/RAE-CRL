from typing import List, Optional, Protocol
from uuid import UUID

from apps.crl.core.models import ArtifactType, BaseArtifact


class ArtifactRepository(Protocol):
    """
    Abstract interface for Artifact Storage.
    Allows swapping backends (Postgres, SQLite, In-Memory) without changing logic.
    """

    async def save(self, artifact: BaseArtifact) -> BaseArtifact:
        """Persist an artifact."""
        ...

    async def get(self, artifact_id: UUID) -> Optional[BaseArtifact]:
        """Retrieve by ID."""
        ...

    async def list_by_project(
        self, project_id: str, type: Optional[ArtifactType] = None
    ) -> List[BaseArtifact]:
        """List artifacts in a project context."""
        ...

    async def link_artifacts(
        self, source_id: UUID, target_id: UUID, relation: str
    ) -> bool:
        """Create a semantic link between artifacts."""
        ...

    async def get_graph(self, artifact_id: UUID, depth: int = 1) -> List[BaseArtifact]:
        """Retrieve connected artifacts (Upstream/Downstream)."""
        ...
