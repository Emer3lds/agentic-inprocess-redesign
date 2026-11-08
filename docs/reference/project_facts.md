# Project facts (reference)

Moved word for word from `CLAUDE.md` on 2026-11-07 so the always-read file stays short. Open this when a task needs setup details, fixed design decisions or past status.

## Setup
- This folder: `C:\Users\amber\Research\AI_Benchmark\lattices` (renamed from `lattice_week2`). Papers are in `../papers/`.
- GitHub: public repo https://github.com/Emer3lds/agentic-inprocess-redesign (renamed from `lattice-defects`), branch `master`. `out/` is tracked so Ma can download the STL files.
- Bambu Studio is installed (`C:\Program Files\Bambu Studio`) for viewing and slicing the STL files. To open a file, use File → Import (Ctrl+I) or drag from Windows File Explorer. Dragging from VS Code does not work.
- Materials available: PLA, maybe TPU.

## Fixed decisions
- Specimen size: 50 × 50 mm in XY, 10 mm in Z. Set by Ma. Z is the print direction (layers stack up from the bed).
- Shapes: hexagonal honeycomb, triangular grid, re-entrant honeycomb. In-plane loading along Y.
- Wall thickness: 1.2 mm (3 lines of a 0.4 mm nozzle). End plates: 1.8 mm. Both match Ma's reference STL, `ref/ma_reentrant.stl` (60 × 60 × 12 mm).
- The end plates sit at the Y ends (y 0–1.8 and 48.2–50) and run the full 10 mm in Z. Keep them.
- Density matching (Option D): the triangle stays at edge 12 mm. The hexagon (edge 4.1 mm) and re-entrant (5.7 / 11.4 mm, 30°) cells were shrunk to match its lattice density. All three are 0.29 to 0.30. Cells across: hexagon 7.0, re-entrant 5.1, triangle 4.2.
- Defect type: **printing defects only**: under-extrusion, over-extrusion, layer shift, warpage. Keep them realistic, not extreme.
- Defect settings (agreed Oct 21, 2026; values in `defects.py` `SEVERITY`; sources in `docs/week2_defects.md`):
  - Under-extrusion walls 1.08 / 0.96 / 0.84 mm; over-extrusion 1.32 / 1.44 / 1.56 mm (90/80/70% and 110/120/130% flow). End plates change by the same ratio, so they may stick out past y = 0 and 50 (0.27 mm at severe).
  - Layer shift along X: 0.4 / 0.8 / 1.0 mm (estimates, no published values). Not 1.2 mm: that equals the wall thickness and leaves walls touching edge to edge.
  - Warpage corner lift: 0.3 / 0.6 / 1.0 mm, fading to 0 at 15 mm from each corner. Backed by Ramian et al. 2021 (ABS blocks 30 and 60 mm long lifted 0.86 and 1.57 mm; height did not matter). PLA warps less than ABS.
  - Under/over-extrusion bands are 1 mm tall. Under/over-extrusion and layer shift start at 10% and 20% of Z (Ma's examples). Layer shift continues to the top. Warpage is always at the bottom.
  - Each defect covers the whole layer in XY.
  - 63 parts: 3 shapes × 3 types × 3 levels × 2 heights = 54, plus 3 shapes × 3 warpage levels = 9.

## Status (as last written in CLAUDE.md, 2026-11-06)
- Week 1 (lattice selection): done. ICML date already settled with Ma.
- Week 2 (from the meeting with Ma): all done.
  1. Store each lattice design as a graph: `out/base/*_graph.json`.
  2. Convert each graph to STL: `out/base/*.stl`.
  3. Use the literature to choose cell repetition and wall thickness: see `docs/week2_defects.md`.
  4. Inject defects, convert to STL, check they sit on the structure and are not floating: `out/defects/`, 63 parts, all pass. Write-up with sources in `docs/week2_defects.md`.
- Week 3 (next meeting with Ma ~2026-11-09; interim update due Thu 2026-10-29):
  - Ma's asks: parts cut right after the defect; a first single-agent framework that redesigns the unprinted part; keep the loading axis fixed (Y); sweep defect height 10% to 90% over several designs; track prompts; try different input formats (Ma's labmate mentioned "design as code" papers, name unknown); add more agent roles later.
  - Amber's goal: learn nameable agent-engineering principles (decision making, experimenting, problem solving). Log every decision in `docs/decisions.md`, every experiment in `docs/experiments.md`, and an interview summary per session in `docs/learning_log.md`. Lay out options plus a recommendation; Amber makes the call.
  - Plan: session 1 cut parts + scenario file (done), session 2 checker + simple methods (no AI), session 3 single agent v0 on Gemini free tier, session 4 results + update for Ma.

