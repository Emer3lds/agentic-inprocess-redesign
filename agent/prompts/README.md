# Prompt versions

Prompts are versioned like code. Never edit a version after it has been used in a run; copy it to the next version number and change that instead. Every run log records which version it used.

| Version | Files | What changed | Written by |
|---|---|---|---|
| v1 | `v1.md`, `v1_retry.md` | First version. No stiffness formula; the agent sees only the checker's feedback, not the score (decisions A and B, 2026-10-29). | Amber's draft, revised together 2026-10-29 |
| v2_tools | `v2_tools.md` | v1 word for word, with OUTPUT replaced by a TOOLS section (evaluate_design, submit_fix) for agent v1. No retry file: rejections come back as the tool's reply. | Claude, from v1, 2026-11-02 |

Slots in `{braces}` are filled from each case record by `agent/agent_v0.py`.

## Which prompt produced which results

Average distance from a healthy part's stiffness, lower is better. Use only full runs here; one-case tests are in `out/runs/`.

| Prompt | Agent | Experiment and log | Model | Long reasoning | Runs | All 12 cases | 6 under- and over-extrusion cases |
|---|---|---|---|---|---|---|---|
| v1 | No calculator | E5, `e5_v1_full.jsonl` | gemini-3.6-flash (requested 3.5) | On | 36 | 1.67% | 2.54% |
| v1 | No calculator | E6, `e6_v0_nemotron.jsonl` | nemotron-3-ultra free | Off | 36 | 2.76% | 5.27% |
| v2_tools | Calculator, 10 uses | E6, `e6_v1_nemotron.jsonl` | nemotron-3-ultra free | Off | 36 | 1.17% | 2.15% |

## What each run log records

Every run records the prompt version, requested and reported model, and scores. Agent v0 logs also save the exact text sent. From 2026-11-05, agent v1 logs also save the exact prompt and tool descriptions, and all logs save the code version. For earlier agent v1 runs, the exact text can be rebuilt from `v2_tools.md`, the case facts, and `agent/agent_v1.py` in git.
