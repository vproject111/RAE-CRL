from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from apps.crl.core.models import BaseArtifact, ArtifactType, ArtifactStatus, ArtifactVisibility
from apps.crl.services.storage.sql import SQLRepository
from apps.crl.core.database import get_session

# Initialize MCP Server
mcp = FastMCP("RAE-CRL-Research-Loop")

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
            grace_period_end=datetime.utcnow() + timedelta(hours=24)
        )
        saved = await repo.save(trace)
        return f"✅ Saved Trace ({saved.id}). Private until {saved.grace_period_end}."
    
    return await with_repo(_action)

@mcp.tool()
async def refine_artifact(
    artifact_id: UUID, 
    new_type: ArtifactType, 
    title: Optional[str] = None, 
    description: Optional[str] = None
) -> str:
    """
    [HUMAN-CENTRIC] Converts a Trace into a formal Artifact (Hypothesis/Experiment/etc).
    """
    async def _action(repo: SQLRepository):
        artifact = await repo.get(artifact_id)
        if not artifact:
            return "❌ Artifact not found."
        
        artifact.type = new_type
        if title: artifact.title = title
        if description: artifact.description = description
        
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
        if not exp: return "❌ Experiment not found."
        
        exp.status = ArtifactStatus.FAILED_BUT_INFORMATIVE
        exp.metadata_blob["failure_reason"] = reason
        await repo.save(exp)
        return f"✅ Recorded meaningful failure for {experiment_id}. Knowledge retained."

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
            output += f"- [{str(a.id)[:8]}] {a.title} (Grace ends: {a.grace_period_end})\n"
        return output

    return await with_repo(_action)

if __name__ == "__main__":
    mcp.run()