# Lattice defect project: handoff notes

## Working rules
- Do only what I ask. No extra checks, backups, or comparisons unless something fails.
- Never delete files. If something should be deleted, tell me and I will do it.
- Only create or edit files inside `C:\Users\amber\Research\AI_Benchmark` (widened by Amber on 2026-10-26).
- Stop after each step: summarize in a few short bullets and wait for me.
- Ask me before generating more than 20 files or running anything expected to take more than 5 minutes.
- Keep script output short: print summaries, not full data.
- Don't install new packages without telling me why.
- Write to me in plain words, short bullets, no jargon.
- Teach before you build (agent framework, from 2026-10-26): give me a short lesson on the principle and walk me through applying it to this project, let me make the key choices, then build.
- After every step, explain the whole pipeline: what was added, what exists vs. not yet, and one worked example with real numbers. When you say you "ran" something, name the script and say whether it is plain code or AI.
- The learning log only records what I actually did or was walked through.
- Commit often (after each finished step), one logical change per commit, clear message saying what and why. Briefly tell me what was committed. Never commit secrets (API keys stay in environment variables).
- The proposal `../Agentic_IPQI_AM_Research_Proposal.docx` is the main reference. Cite it for decisions; when my instructions, Ma's directions or the pipeline differ from it, say so and update `docs/proposal_differences.md`.
- `docs/learning_log.md` and `docs/tutor_brief.md` are personal and kept off GitHub (in `.gitignore`). `docs/tutor_brief.md` is a briefing for a separate study-buddy chat. Keep its pipeline status and open decisions up to date when they change.

## Who and what
- Amber, an undergraduate in industrial engineering at Georgia Tech. Codes in Python at a beginner to intermediate level. New to 3D printing, so explain printing terms.
- Research: a multi-agent framework for AI-driven repair of defects in 3D-printed lattices. Mentor: Ma. Results target end of December 2026.
- Amber's parts: lattice design, defect definition and injection, and agent design. Ma's group does printing and data collection.
- Writing style for Amber: plain words, short bullets, no jargon or shorthand. Ask before guessing.

## Setup
- This folder: `C:\Users\amber\Research\AI_Benchmark\lattices` (renamed from `lattice_week2`). Papers are in `../papers/`.
- GitHub: private repo https://github.com/Emer3lds/agentic-inprocess-redesign (renamed from `lattice-defects`), branch `master`. `out/` is tracked so Ma can download the STL files.
- Bambu Studio is installed (`C:\Program Files\Bambu Studio`) for viewing and slicing the STL files. To open a file, use File → Import (Ctrl+I) or drag from Windows File Explorer. Dragging from VS Code does not work.
- Materials available: PLA, maybe TPU.

## Status
- Week 1 (lattice selection): done. ICML date already settled with Ma.
- Week 2 (from the meeting with Ma): all done.
  1. Store each lattice design as a graph: `out/base/*_graph.json`.
  2. Convert each graph to STL: `out/base/*.stl`.
  3. Use the literature to choose cell repetition and wall thickness: see `README.md`.
  4. Inject defects, convert to STL, check they sit on the structure and are not floating: `out/defects/`, 63 parts, all pass. Write-up with sources in `README.md`.
- Week 3 (next meeting with Ma ~2026-11-09; interim update due Thu 2026-10-29):
  - Ma's asks: parts cut right after the defect; a first single-agent framework that redesigns the unprinted part; keep the loading axis fixed (Y); sweep defect height 10% to 90% over several designs; track prompts; try different input formats (Ma's labmate mentioned "design as code" papers, name unknown); add more agent roles later.
  - Amber's goal: learn nameable agent-engineering principles (decision making, experimenting, problem solving). Log every decision in `docs/decisions.md`, every experiment in `docs/experiments.md`, and an interview summary per session in `docs/learning_log.md`. Lay out options plus a recommendation; Amber makes the call.
  - Plan: session 1 cut parts + scenario file (done), session 2 checker + simple methods (no AI), session 3 single agent v0 on Gemini free tier, session 4 results + update for Ma.

## Fixed decisions
- Specimen size: 50 × 50 mm in XY, 10 mm in Z. Set by Ma. Z is the print direction (layers stack up from the bed).
- Shapes: hexagonal honeycomb, triangular grid, re-entrant honeycomb. In-plane loading along Y.
- Wall thickness: 1.2 mm (3 lines of a 0.4 mm nozzle). End plates: 1.8 mm. Both match Ma's reference STL, `ref/ma_reentrant.stl` (60 × 60 × 12 mm).
- The end plates sit at the Y ends (y 0–1.8 and 48.2–50) and run the full 10 mm in Z. Keep them.
- Density matching (Option D): the triangle stays at edge 12 mm. The hexagon (edge 4.1 mm) and re-entrant (5.7 / 11.4 mm, 30°) cells were shrunk to match its lattice density. All three are 0.29 to 0.30. Cells across: hexagon 7.0, re-entrant 5.1, triangle 4.2.
- Defect type: **printing defects only**: under-extrusion, over-extrusion, layer shift, warpage. Keep them realistic, not extreme.
- Defect settings (agreed Oct 21, 2026; values in `defects.py` `SEVERITY`; sources in `README.md`):
  - Under-extrusion walls 1.08 / 0.96 / 0.84 mm; over-extrusion 1.32 / 1.44 / 1.56 mm (90/80/70% and 110/120/130% flow). End plates change by the same ratio, so they may stick out past y = 0 and 50 (0.27 mm at severe).
  - Layer shift along X: 0.4 / 0.8 / 1.0 mm (estimates, no published values). Not 1.2 mm: that equals the wall thickness and leaves walls touching edge to edge.
  - Warpage corner lift: 0.3 / 0.6 / 1.0 mm, fading to 0 at 15 mm from each corner. Backed by Ramian et al. 2021 (ABS blocks 30 and 60 mm long lifted 0.86 and 1.57 mm; height did not matter). PLA warps less than ABS.
  - Under/over-extrusion bands are 1 mm tall. Under/over-extrusion and layer shift start at 10% and 20% of Z (Ma's examples). Layer shift continues to the top. Warpage is always at the bottom.
  - Each defect covers the whole layer in XY.
  - 63 parts: 3 shapes × 3 types × 3 levels × 2 heights = 54, plus 3 shapes × 3 warpage levels = 9.

## Open questions
- For Ma (also listed in `README.md`):
  - Are the defect sizes realistic on his Bambu printer with PLA? Is "severe" too mild or too extreme?
  - Layer shift along X only, or also Y (18 more parts)?
  - Is 63 parts the right number?
  - Is it OK that severe over-extrusion makes the plates stick out 0.27 mm past each end?
  - Should defects also cover only part of a layer (for example one corner)?
  - Which Bambu printer model does he use?
  - Should defect sizes differ for TPU?
  - Week 3: print these parts, or start the agent design?
- For Amber:
  - Repo already renamed by Amber. Reorganize for the whole project (project overview in `README.md`, week 2 write-up moved to `docs/week2_defects.md`, code stays at the top level for now)? Suggested, not yet answered.
  - Other (non-printing) defect types: Ma mentioned "small cracks". No record of what else was discussed earlier.
  - `build_defects_test.py` is out of date and can be deleted by Amber.

## Code
- `lattice.py`:
  - `build_graph` tiles a unit cell, clips it to 50 × 50 mm, and removes dangling walls.
  - `graph_to_polygon` gives the 2D cross-section. Each edge has its own thickness `t`. `plate_scale` grows or shrinks the end plates.
  - `polygon_to_mesh` extrudes the cross-section.
  - `check_mesh` reports whether the mesh is watertight, how many pieces it has, and its relative density.
- `build_base.py` builds the three base designs into `out/base/`. Run it with `python build_base.py`.
- `defects.py`:
  - `inject(graph, type, severity, z0)` builds the part with one defect and returns the mesh and its answer-key entry.
  - Under/over-extrusion and layer shift: the part is built as stacked Z bands (normal outside the defect band, changed inside) and merged with manifold3d.
  - Warpage: material below a curved surface at the bottom corners is cut away (same shape as lifted corners for straight-walled parts).
  - `check_defect` checks: one piece, watertight, defect region overlaps the solid, inside the box except intended overhangs (layer shift in X, grown plates in Y).
  - Meshes are kept as manifold3d outputs them (no vertex merging). Merging nearly equal points gave false "not watertight" results.
- `agent/scenarios.py`: builds repair cases (stop rule: defect start + 1 mm detection delay). Writes `out/scenarios/<shape>/<id>_prefix.stl`, `out/scenarios/scenarios.json` and a side-view picture. 12 cases now (re-entrant, medium, 10/50/80%).
- `build_defects.py`: full set, 63 parts, written to `out/defects/<shape>/` (STL plus `_graph.json` with the answer key in `defects` and the check results in `checks`), with `summary.json` and one side-view picture per shape. About 25 seconds.
- Python packages: trimesh, shapely, manifold3d, rtree, numpy, matplotlib.

## How to communicate

These are important. Follow them in every response, summary, and report.

- **Be concise.** Use bullet points instead of paragraphs. Keep each bullet short.
- **Be clear and jargon-free.** Use plain, everyday words. If a technical term is unavoidable, explain it.
- **No shorthand.** Short does not mean cryptic. Each bullet should be a clear, complete thought that Amber can understand without guessing what you meant.
- **No flourish.** No filler, no hype, no decorative language.
- **Ask when unsure.** Ask questions instead of guessing.** Whenever anything is unclear, or there is more than one reasonable way to do a task, stop and ask Amber before acting. Amber would much rather answer a question up front than have you do something slightly wrong that she then has to go back and correct. There is no limit on how many questions you can ask. When in doubt, ask.
