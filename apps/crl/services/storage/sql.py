from typing import Any, List, Optional, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from apps.crl.core.models import ArtifactRelation, ArtifactType, BaseArtifact
from apps.crl.interfaces.storage import ArtifactRepository


class SQLRepository(ArtifactRepository):
    """
    Universal SQL Repository working with both PostgreSQL (Docker) and SQLite (Desktop).
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, artifact: BaseArtifact) -> BaseArtifact:
        self.session.add(artifact)
        await self.session.commit()
        await self.session.refresh(artifact)
        return artifact

    async def get(self, artifact_id: UUID) -> Optional[BaseArtifact]:
        result = await self.session.execute(
            select(BaseArtifact).where(BaseArtifact.id == artifact_id)
        )
        return result.scalars().first()

    async def list_by_project(
        self, project_id: str, type: Optional[ArtifactType] = None
    ) -> List[BaseArtifact]:
        query = select(BaseArtifact).where(BaseArtifact.project_id == project_id)
        if type:
            query = query.where(BaseArtifact.type == type)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def link_artifacts(
        self, source_id: UUID, target_id: UUID, relation: str
    ) -> bool:
        link = ArtifactRelation(
            source_id=source_id, target_id=target_id, relation_type=relation
        )
        self.session.add(link)
        try:
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False

    async def get_graph(self, artifact_id: UUID, depth: int = 1) -> List[BaseArtifact]:
        stmt = (
            select(BaseArtifact)
            .join(
                ArtifactRelation,
                cast(Any, ArtifactRelation.target_id == BaseArtifact.id),
            )
            .where(ArtifactRelation.source_id == artifact_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
