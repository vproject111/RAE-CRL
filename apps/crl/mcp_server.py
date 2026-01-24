import asyncio
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP  # type: ignore
from typing import Dict, Any, List, Optional
from uuid import UUID


from apps.crl.core.database import get_session
from apps.crl.core.models import (ArtifactStatus, ArtifactType,
                                  ArtifactVisibility, BaseArtifact)
from apps.crl.services.storage.sql import SQLRepository
from apps.crl.services.sync_service import SyncEngine

# Initialize MCP Server
mcp = FastMCP("RAE-CRL-Research-Loop")

# Start Sync Engine in Background (moved to main to avoid test import side-effects)
# @mcp.on_startup - removed due to API mismatch


# Helper to run database operations
async def with_repo(func):
    """Executes a function with a Repository instance."""
    async for session in get_session():
        repo = SQLRepository(session)
        return await func(repo)


@mcp.tool()
async def quick_note(content: str, project_id: str, author: str = "researcher") -> str:
    """
    [HUMAN-CENTRIC] Creates a quick Epistemic Trace.
    Use this for rough ideas, doubts, or rapid logging.
    - Private by default.
    - Protected for 24h (Grace Period).
    """

    async def _action(repo: SQLRepository):
        trace = BaseArtifact(
            type=ArtifactType.TRACE,
            title=content[:50] + "..." if len(content) > 50 else content,
            description=content,
            project_id=project_id,
            author=author,
            status=ArtifactStatus.DRAFT,
            visibility=ArtifactVisibility.PRIVATE,
            grace_period_end=datetime.utcnow() + timedelta(hours=24),
        )
        saved = await repo.save(trace)
        return f"✅ Saved Trace ({saved.id}). Private until {saved.grace_period_end}."

    return await with_repo(_action)


@mcp.tool()
async def refine_artifact(
    artifact_id: UUID,
    new_type: ArtifactType,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """
    [HUMAN-CENTRIC] Converts a Trace into a formal Artifact (Hypothesis/Experiment/etc).
    """

    async def _action(repo: SQLRepository):
        artifact = await repo.get(artifact_id)
        if not artifact:
            return "❌ Artifact not found."

        artifact.type = new_type
        if title:
            artifact.title = title
        if description:
            artifact.description = description

        # Remove grace period on refinement
        artifact.grace_period_end = None
        artifact.status = ArtifactStatus.ACTIVE

        saved = await repo.save(artifact)
        return f"✅ Refined to {new_type.value} ({saved.id}). Grace period ended."

    return await with_repo(_action)


@mcp.tool()
async def record_failure(experiment_id: UUID, reason: str) -> str:
    """
    [HUMAN-CENTRIC] Logs a failure as a valuable learning asset.
    """

    async def _action(repo: SQLRepository):
        exp = await repo.get(experiment_id)
        if not exp:
            return "❌ Experiment not found."

        exp.status = ArtifactStatus.FAILED_BUT_INFORMATIVE
        exp.metadata_blob["failure_reason"] = reason
        await repo.save(exp)
        return (
            f"✅ Recorded meaningful failure for {experiment_id}. Knowledge retained."
        )

    return await with_repo(_action)


@mcp.tool()
async def fork_artifact(original_id: UUID, new_author: str, reason: str) -> str:
    """
    [EPISTEMIC FORK] Creates an alternative interpretation (Fork) of an artifact.
    Use when you disagree with a hypothesis or conclusion.
    """

    async def _action(repo: SQLRepository):
        original = await repo.get(original_id)
        if not original:
            return "❌ Original artifact not found."

        # Clone logic
        from apps.crl.core.models import ArtifactType, BaseArtifact

        fork = BaseArtifact(
            type=original.type,
            title=f"Fork of: {original.title}",
            description=f"Fork Reason: {reason}\n\nOriginal Content: {original.description}",
            project_id=original.project_id,
            author=new_author,
            status=ArtifactStatus.DRAFT,
            visibility=ArtifactVisibility.TEAM,  # Forks are usually for discussion
            metadata_blob={"forked_from": str(original.id), "reason": reason},
        )

        saved_fork = await repo.save(fork)
        await repo.link_artifacts(
            original.id, saved_fork.id, "has_alternative_interpretation"
        )

        return f"✅ Fork created ({saved_fork.id}). Let the debate begin!"

    return await with_repo(_action)


@mcp.tool()
async def request_approval(artifact_id: UUID, approver_name: str) -> str:
    """[RESPONSIBILITY] Submits an artifact for formal approval (e.g., by PI)."""

    async def _action(repo: SQLRepository):
        art = await repo.get(artifact_id)
        if not art:
            return "❌ Artifact not found."

        art.proposed_by = art.author
        art.metadata_blob["approver_target"] = approver_name
        # Status could change to PENDING if we had it, for now keep ACTIVE but marked
        await repo.save(art)
        return f"✅ Submitted {artifact_id} for approval by {approver_name}."

    return await with_repo(_action)


@mcp.tool()
async def approve_artifact(artifact_id: UUID, approver_name: str) -> str:
    """[RESPONSIBILITY] Formally approves an artifact."""

    async def _action(repo: SQLRepository):
        art = await repo.get(artifact_id)
        if not art:
            return "❌ Artifact not found."

        art.approved_by = approver_name
        art.status = ArtifactStatus.ACTIVE  # Ensure it's active
        art.grace_period_end = None  # Approval implies readiness for Sync

        await repo.save(art)
        return f"✅ Artifact {artifact_id} APPROVED by {approver_name}."

    return await with_repo(_action)


@mcp.tool()
async def list_my_traces(project_id: str) -> str:
    """Shows active traces / drafts to remind you what needs refinement."""

    async def _action(repo: SQLRepository):
        artifacts = await repo.list_by_project(project_id, type=ArtifactType.TRACE)
        if not artifacts:
            return "No pending traces."

        output = "📝 **Your Epistemic Traces:**\n"
        for a in artifacts:
            output += (
                f"- [{str(a.id)[:8]}] {a.title} (Grace ends: {a.grace_period_end})\n"
            )
        return output

    return await with_repo(_action)


if __name__ == "__main__":
    # Start Sync Engine when running standalone
    sync = SyncEngine()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(sync.start(interval_seconds=300))

    mcp.run()
