# RAE AGENTIC CONTRACT (HARD ENFORCEMENT)
Version: 1.0 (2026-01-18)

## 🚨 MANDATORY RULES
1. **BOOTSTRAP FIRST**: Never read a file or call a tool before running `scripts/bootstrap_session.py`.
2. **USE SESSION ID**: The bootstrap script provides a `SESSION_ID`. Use it in ALL agent interactions.
3. **IMPLICIT CAPTURE**: Do NOT manually call `save_memory` for your own thoughts or final answers. The `RAERuntime` captures them automatically.
4. **QUERY BEFORE GUESSING**: If you don't know the state of a feature (e.g. "Phase 3"), query RAE (Node 1) before looking at local files.
5. **NO INTERACTIVE TOOLS**: Absolute ban on `nano`, `vim`, etc. Use `replace` or `write_file`.
6. **CLUSTER FIRST**: Heavy tasks (benchmarks > 1k) must go to Node 1 (Lumina).

## 🔌 INFRASTRUCTURE CONTRACT (FIXED)
- **Node 1 (Lumina)**: `100.68.166.117`
- **RAE Dev (Hotreload)**: Port `8001` (Both Local and Node 1)
- **RAE Lite**: Port `8008`
- **Priority**: Local (8001) -> Node 1 (8001) -> Local (8008).
- **Repair Path**: If Port 8001 returns 502, execute `docker compose down && docker network prune -f && docker compose up -d` immediately.

## 🧠 MENTAL STATE SYNC
At the end of every significant milestone, update RAE Working Layer with current goals using the `session-summary` tag.
