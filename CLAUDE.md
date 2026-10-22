# Lattice defect project: week 2 handoff

## Working rules
- Do only what I ask. No extra checks, backups, or comparisons unless something fails.
- Never delete files. If something should be deleted, tell me and I will do it.
- Only create or edit files inside this folder.
- Stop after each step: summarize in a few short bullets and wait for me.
- Ask me before generating more than 20 files or running anything expected to take more than 5 minutes.
- Keep script output short: print summaries, not full data.
- Don't install new packages without telling me why.
- Write to me in plain words, short bullets, no jargon.

## Who and what
- Amber, an undergraduate in industrial engineering at Georgia Tech. Codes in Python at a beginner to intermediate level.
- Research: a multi-agent framework for AI-driven repair of defects in 3D-printed lattices. Mentor: Ma. Results target end of December 2026.
- Amber's parts: lattice design, defect definition and injection, and agent design. Ma's group does printing and data collection.
- Writing style for Amber: plain words, short bullets, no jargon or shorthand. Ask before guessing.

## Week 2 task (from the meeting with Ma)
1. Store each lattice design as a graph. Done: `out/base/*_graph.json`.
2. Convert each graph to STL. Done: `out/base/*.stl`.
3. Use the literature to choose cell repetition and wall thickness. Done: see `README.md`.
4. Inject defects, convert them to STL, and check that the defects sit on the structure and are not floating. Done: `out/defects/`, 63 parts, all pass. Write-up in `README.md`.

## Fixed decisions
- Specimen size: 50 × 50 mm in XY, 10 mm in Z. Set by Ma.
- Shapes: hexagonal honeycomb, triangular grid, re-entrant honeycomb. In-plane loading along Y.
- Wall thickness: 1.2 mm (3 lines of a 0.4 mm nozzle). Top and bottom plates: 1.8 mm. Both match Ma's reference STL, `ref/ma_reentrant.stl` (60 × 60 × 12 mm).
- Defect type: **printing defects only**. These are layer shift, over-extrusion, under-extrusion, and warpage. They affect a band of layers (a height range in Z), not the full height. Inject them at different heights (for example 10% or 20% of Z) and at small, medium, and severe levels. Keep them realistic, not extreme.
- Printer: Ma uses Bambu Studio.
- Keep the top and bottom plates.
- Density matching (Option D): the triangle stays at edge 12 mm. The hexagon (edge 4.1 mm) and re-entrant (5.7 / 11.4 mm, 30°) cells were shrunk to match its lattice density. All three are 0.29 to 0.30.

- Defect settings (agreed Oct 21, 2026; values in `defects.py` `SEVERITY`; sources in chat and to go in `README.md`):
  - Under-extrusion walls 1.08 / 0.96 / 0.84 mm; over-extrusion 1.32 / 1.44 / 1.56 mm (90/80/70% and 110/120/130% flow).
  - Layer shift along X 0.4 / 0.8 / 1.0 mm (not 1.2: equals wall thickness, walls touch edge to edge); warpage corner lift 0.3 / 0.6 / 1.0 mm (both estimates, no paper numbers).
  - Defect band 1 mm tall, whole layer in XY, starting at 10% and 20% of Z (Ma's examples). Warpage always at the bottom: corners lifted, fading to 0 at 15 mm from each corner.
  - Extrusion defects change the end plates by the same ratio as the walls (plates may stick out past y = 0 and 50).
  - Warpage values backed by Ramian et al. 2021 (`../papers/`): ABS cuboids 30 and 60 mm long lifted 0.86 and 1.57 mm on an open printer; height did not matter. We print PLA (maybe TPU), which warps less, so our 0.3 to 1.0 mm is reasonable.
- Note: the plates sit at the Y ends (y 0–1.8 and 48.2–50) and run the full 10 mm in Z. Z is the print direction.

## Open questions (ask Amber)
- None right now. Ma still to confirm sizes, shift direction, and file count (listed in `README.md`).

## Code
- `lattice.py`:
  - `build_graph` tiles a unit cell, clips it to 50 × 50 mm, and removes dangling walls.
  - `graph_to_polygon` gives the 2D cross-section. Each edge has its own thickness `t`.
  - `polygon_to_mesh` extrudes the cross-section.
  - `check_mesh` reports whether the mesh is watertight, how many pieces it has, and its relative density.
- `build_base.py` builds the three base designs. Run it with `python3 build_base.py`.
- `defects.py`: `inject(graph, type, severity, z0)` builds the part with one defect and returns the mesh and its answer-key entry. `check_defect` runs the checks.
- `build_defects_test.py`: early test, `out/defects_test/` is out of date (made before plates changed with flow).
- `build_defects.py`: full set, 63 parts, written to `out/defects/<shape>/` with `summary.json` and one side-view picture per shape. About 25 seconds.
- Python packages: trimesh, shapely, manifold3d, rtree, numpy, matplotlib.

## Plan for defect injection
- Build the part as stacked Z bands. The normal walls go outside the defect band, and the changed geometry goes inside it:
  - Thinner walls for under-extrusion.
  - Thicker walls for over-extrusion.
  - An XY offset for everything above the shift layer, for layer shift.
  - Corners of the lower layers lifted, for warpage.
- Merge the bands with manifold3d into one watertight solid.
- Save each defect as an entry in the graph JSON `defects` list (type, Z range, location, severity). This is the answer key for the agent.
- Checks for each defect:
  - The defect region overlaps the solid.
  - The result is still one piece and watertight.
  - Its size and position are within the 50 × 50 × 10 mm box (except an intended layer shift).

## How to communicate

These are important. Follow them in every response, summary, and report.

- **Be concise.** Use bullet points instead of paragraphs. Keep each bullet short.
- **Be clear and jargon-free.** Use plain, everyday words. If a technical term is unavoidable, explain it.
- **No shorthand.** Short does not mean cryptic. Each bullet should be a clear, complete thought that Amber can understand without guessing what you meant.
- **No flourish.** No filler, no hype, no decorative language.
- **Ask when unsure.** Ask questions instead of guessing.** Whenever anything is unclear, or there is more than one reasonable way to do a task, stop and ask Amber before acting. Amber would much rather answer a question up front than have you do something slightly wrong that she then has to go back and correct. There is no limit on how many questions you can ask. When in doubt, ask.