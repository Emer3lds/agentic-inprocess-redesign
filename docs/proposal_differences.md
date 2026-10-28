# Where the project differs from the proposal

Reference: `../Agentic_IPQI_AM_Research_Proposal.docx` (version 1.0, 4 October 2026).
One row per difference. "Source" says who or what caused the difference. Updated 2026-10-28.

| Topic | Proposal says | Current project | Source | Action |
|---|---|---|---|---|
| Specimen | Re-entrant only, 60 × 60 × 12 mm, rows 4-3-4-3-4, 18 cells (sec. 6) | 3 shapes, 50 × 50 × 10 mm | Ma (week 2) | None; keep |
| Checkpoint height | One checkpoint at z = 6 mm (half the height) (sec. 6) | Defect start at 10, 50, 80%; stop 1 mm later | Ma (week 3: sweep 10 to 90%) | None; keep |
| Defect | Case I: a small connected patch of wall thinning (sec. 10.1) | Printing defects covering whole layers: under/over-extrusion, layer shift, warpage | Ma (week 2) | Patches in part of a layer are a possible later addition |
| What the agent sees | Measured state with uncertainty, kept separate from guesses (sec. 5.1, 8.4) | Exact defect, no measurement error | D4 | Add noise later |
| What the agent may change | Width redistribution in about 4 named wall groups, with a gradual transition height; topology changes only later (sec. 7.1, 7.3) | Level 1: one thickness per 1 mm band, all walls equal | D5 | Ma (2026-10-28) wants full regeneration of the design; see D5. Per-wall-group thickness needs the beam model |
| Fair comparison when editing shape | A shape-editing agent must be compared with a non-AI method using the same operations (sec. 4.3, 7.3) | Not yet relevant (thickness only) | — | Must hold if we move to full regeneration |
| Score | Measured crush curve (curve error J, peak force P, work W) or peak force only (sec. 5.2, 5.3) | Formula stiffness estimate (D8), no physical tests yet | D8 | Beam model next; crush tests later |
| Material budget | Remaining CAD volume ≤ budget at the checkpoint; missing printed material does not raise the budget (sec. 5.4) | Same ("remaining") | D7 | Aligned since 2026-10-28 |
| Comparison methods | N nominal, R fixed rule, B non-AI search/optimizer, A AI agent (sec. 8.5) | N (do_nothing) and R (simple_rule) built | — | **B is missing**: add a non-AI search over the same thickness options |
| Agent tools | measure_state, retrieve_experiments, build_completion, validate_completion, submit_for_approval (sec. 8.1) | Not built yet; check() and score() will become tools | — | Session 3 |
| Failed proposals | Return violations to the agent, fixed attempt limit, then a predeclared fallback; failures stay in the results (sec. 7.3) | check() returns violations with reasons | — | Session 3: attempt limit + fallback (do_nothing) |
| Decision log | Store every attempt: state, model/version, operations, validator output, tool calls, time (sec. 8.3, App. A.3) | Planned run logs | — | Session 3 |
