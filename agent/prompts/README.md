# Prompt versions

Prompts are versioned like code. Never edit a version after it has been used in a run; copy it to the next version number and change that instead. Every run log records which version it used.

| Version | Files | What changed | Written by |
|---|---|---|---|
| v1 | `v1.md`, `v1_retry.md` | First version. No stiffness formula; the agent sees only the checker's feedback, not the score (decisions A and B, 2026-10-29). | Amber's draft, revised together 2026-10-29 |

Slots in `{braces}` are filled from each case record by `agent/agent_v0.py`.
