from uuid import uuid4

import pytest

from apps.crl.core.models import (ArtifactStatus, ArtifactType,
                                  ArtifactVisibility)
from apps.crl.mcp_server import (approve_artifact, fork_artifact,
                                 list_my_traces, quick_note, record_failure,
                                 refine_artifact, request_approval)
from apps.crl.services.storage.sql import SQLRepository


@pytest.mark.asyncio
async def test_full_lifecycle_with_governance():
    project_id = "test-gov-project"

    # 1. Trace -> Refine
    result = await quick_note("Controversial finding", project_id)
    import re

    trace_id = re.search(r"\((.*?)\)", result).group(1)

    await refine_artifact(trace_id, ArtifactType.HYPOTHESIS, title="Earth is Flat")

    # 2. Forking (The Disagreement)
    fork_res = await fork_artifact(
        trace_id, "Galileo", "Observational evidence contradicts"
    )
    assert "Fork created" in fork_res
    fork_id = re.search(r"\((.*?)\)", fork_res).group(1)

    # 3. Approval Workflow
    req_res = await request_approval(fork_id, "The Pope")
    assert "Submitted" in req_res

    approve_res = await approve_artifact(fork_id, "The Pope")
    assert "APPROVED" in approve_res

    print("Governance Flow Verified!")
