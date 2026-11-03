# Prompt versions

Prompts are versioned like code. Never edit a version after it has been used in a run; copy it to the next version number and change that instead. Every run log records which version it used.

| Version | Files | What changed | Written by |
|---|---|---|---|
| v1 | `v1.md`, `v1_retry.md` | First version. No stiffness formula; the agent sees only the checker's feedback, not the score (decisions A and B, 2026-10-29). | Amber's draft, revised together 2026-10-29 |
| v2_tools | `v2_tools.md` | v1 word for word, with OUTPUT replaced by a TOOLS section (evaluate_design, submit_fix) for agent v1. No retry file: rejections come back as the tool's reply. | Claude, from v1, 2026-11-02 |

Slots in `{braces}` are filled from each case record by `agent/agent_v0.py`.
