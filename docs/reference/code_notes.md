# Code notes (reference)

Moved word for word from `CLAUDE.md` on 2026-11-07. Open this before changing or running code.

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


## Added 2026-11-07
- `fea/beam.py`: beam model of the walls, the fast FEA calculator (D12). Plain numpy, no new package.
  - `layer_response(g, thickness, depth, holes, plates)`: one layer as a 2D frame (each wall a beam that stretches and bends); returns stiffness (N/mm) and first-yield force (N). Walls are held where they meet the end plates (`plates="clamped"`); `"slip"` is only for comparisons.
  - `BeamCase(case).score(fix)`: same keys as `agent/evaluate.py score()`, plus `first_yield_ratio` (whole part first yields when its weakest layer does). `peak_force_ratio` adds up each layer's own yield force; neither force number is trusted yet.
  - Material values are placeholders (E 3500 MPa, yield 50 MPa); only ratios to a healthy part are meaningful.
  - Blind to layer shift. About 0.01 to 0.08 s per layer.
- `fea/trust_checks.py`: experiment E7. `python fea/trust_checks.py`, about 1 minute; writes `out/results/e7_beam_checks.json`.
- `agent/quick_check.py`: loads the 12 cases and scores "do nothing" (about 6 s). A quick test that the pipeline still runs after code changes.
- OpenSeesPy was tried and removed: its Windows build needs Python 3.12 (this laptop has 3.13).
- `fea/solid3d.py`: 3D solid model (gmsh 10-node tetrahedra + CalculiX from the `fea` conda environment); `stiffness(path, size)` returns N/mm. Reads an STL, or builds a healthy part from its design graph. STLs made before 2026-11-12 had zero-thickness internal faces for the triangle and re-entrant; rebuilt files read fine. Run files go to `out/fea3d/<run>/`.
- `fea/e8_solid_checks.py`: experiment E8 (block check, piece-size check, healthy parts vs beam model). `python fea/e8_solid_checks.py --sizes 1.2 0.8 0.6 --size 1.2`; reuses finished runs; writes `out/results/e8_solid_checks.json`.
