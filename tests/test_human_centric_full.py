import pytest
from uuid import uuid4
from apps.crl.core.models import ArtifactType, ArtifactStatus, ArtifactVisibility
from apps.crl.services.storage.sql import SQLRepository
from apps.crl.mcp_server import quick_note, refine_artifact, record_failure, list_my_traces, fork_artifact, request_approval, approve_artifact

@pytest.mark.asyncio
async def test_full_lifecycle_with_governance():
    project_id = "test-gov-project"
    
    # 1. Trace -> Refine
    result = await quick_note("Controversial finding", project_id)
    import re
    trace_id = re.search(r'\((.*?)\)', result).group(1)
    
    await refine_artifact(trace_id, ArtifactType.HYPOTHESIS, title="Earth is Flat")
    
    # 2. Forking (The Disagreement)
    fork_res = await fork_artifact(trace_id, "Galileo", "Observational evidence contradicts")
    assert "Fork created" in fork_res
    fork_id = re.search(r'\((.*?)\)', fork_res).group(1)
    
    # 3. Approval Workflow
    req_res = await request_approval(fork_id, "The Pope")
    assert "Submitted" in req_res
    
    approve_res = await approve_artifact(fork_id, "The Pope")
    assert "APPROVED" in approve_res
    
    print("Governance Flow Verified!")
