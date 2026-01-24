from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel


class ArtifactType(str, Enum):
    TRACE = "epistemic_trace"  # The "Rough Draft" / "Napkin sketch"
    HYPOTHESIS = "hypothesis"
    ASSUMPTION = "assumption"
    EXPERIMENT = "experiment"
    OBSERVATION = "observation"
    DECISION = "decision"
    REFLECTION = "reflection"


class ArtifactStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED_BUT_INFORMATIVE = (
        "failed_but_informative"  # Crucial for psychological safety
    )
    DEPRECATED = "deprecated"


class ArtifactVisibility(str, Enum):
    PRIVATE = "private"  # Visible only to author (Grace Period default)
    TEAM = "team"  # Visible to lab
    PUBLIC = "public"  # Published/Frozen


class ArtifactRelation(SQLModel, table=True):
    """Represents a directed edge in the research graph."""

    source_id: UUID = Field(foreign_key="baseartifact.id", primary_key=True)
    target_id: UUID = Field(foreign_key="baseartifact.id", primary_key=True)
    relation_type: str = Field(default="related_to")


class BaseArtifact(SQLModel, table=True):
    """
    Universal schema for all research artifacts + Epistemic Traces.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    type: ArtifactType = Field(index=True)
    title: str = Field(min_length=1, max_length=200)  # Traces can have short titles
    description: str = Field(default="")  # Traces might just be a title initially

    # Context
    project_id: str = Field(index=True)
    research_phase: Optional[str] = None

    # Epistemic Safety & Status
    status: ArtifactStatus = Field(default=ArtifactStatus.DRAFT, index=True)
    visibility: ArtifactVisibility = Field(default=ArtifactVisibility.PRIVATE)
    grace_period_end: Optional[datetime] = (
        None  # If set, protected from Mesh/Sync until this date
    )

    # Responsibility (Epistemic Governance)
    author: str = Field(default="unknown")
    proposed_by: Optional[str] = None
    approved_by: Optional[str] = None

    # Metadata (Flexible Storage)
    metadata_blob: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced_at: Optional[datetime] = Field(default=None)  # Bridge to RAE Core
    provenance_hash: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
