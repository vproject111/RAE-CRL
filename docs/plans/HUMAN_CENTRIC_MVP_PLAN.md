# Human-Centric RAE-CRL MVP Plan
Status: DRAFT (Pending analysis of plan_01)
Date: 2026-01-24

## Core Philosophy
"RAE-CRL must be a tool for the tired scientist, not just the perfect one."
Focus on: Imperfection, Cognitive Safety, and Epistemic Traces.

## 1. Data Model Extensions (Postgres)
- [ ] **Epistemic Trace**: Add `ArtifactType.TRACE` (The "Rough Draft").
    - Characteristics: Loose validation, private by default, ephemeral.
- [ ] **Epistemic Safety Fields**:
    - `visibility`: `PRIVATE` (Author only), `TEAM` (Lab), `PUBLIC` (Published).
    - `grace_period_end`: Timestamp until which the artifact is hidden from "Hive Mind" logic.
    - `status`: Add `FAILED_BUT_INFORMATIVE` to explicit statuses.
- [ ] **Responsibility Layer**:
    - Add metadata fields: `proposed_by`, `approved_by`, `contested_by`.

## 2. Interface (UX/MCP)
- [ ] **Tool: `quick_note`**:
    - Input: `content` (string).
    - Action: Creates a TRACE linked to current context.
    - UX: Zero friction. No "Title", "Type", "Metadata" required initially.
- [ ] **Tool: `refine_artifact`**:
    - Action: Converts TRACE -> HYPOTHESIS/OBSERVATION.
- [ ] **Tool: `fork_interpretation`**:
    - Action: Creates a parallel Hypothesis linked to the same Experiment.

## 3. Workflow Logic
- [ ] **The "Morning Coffee" View**:
    - Query: Show me all my `TRACE` items from yesterday.
    - Action: Prompt user to refine or discard.
- [ ] **The "Failure" Celebration**:
    - Explicitly tag failed experiments as high-value knowledge (high retention priority in RAE).

## 4. Agnosticism & Architecture
- Maintain `ArtifactRepository` protocol.
- Ensure `Trace` objects are stored in the same SQL/Agnostic backend but treated differently by the sync engine.
