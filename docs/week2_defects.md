# Week 2: Lattice design → graph → STL → defects

## Files
- `lattice.py`: builds a lattice graph, turns it into a 2D cross-section, and extrudes it into an STL.
- `build_base.py`: builds the three defect-free lattices.
- `out/base/<shape>_graph.json`: the graph (nodes, edges, wall thickness, plates, defect list).
- `out/base/<shape>.stl`: the printable part.
- `out/base/<shape>.png`: top view.
- `out/base/summary.json`: checks and measurements.
- `defects.py`: adds one printing defect to a lattice and checks the result.
- `build_defects.py`: builds the full defect set (63 parts, about 25 seconds).
- `out/defects/<shape>/<name>.stl`: part with one defect. Name = shape, defect type, level, and height (for example `hexagon_layer_shift_medium_z20` = medium layer shift starting at 20% of the height).
- `out/defects/<shape>/<name>_graph.json`: the graph plus the answer key (`defects` list: type, level, height range, size) and the check results.
- `out/defects/<shape>_side_views.png`: side cuts of one severe example per defect type.
- `out/defects/summary.json`: check results for all 63 parts.

## Fixed setup (all shapes)
| Item | Value | Why |
|---|---|---|
| Size | 50 × 50 mm (XY), 10 mm (Z) | Set by Ma |
| Wall thickness | 1.2 mm | 3 lines of a 0.4 mm nozzle; matches Ma's re-entrant STL (measured 1.2 mm) |
| Top and bottom plates | 1.8 mm solid | Matches Ma's STL; gives a flat surface for the crush machine |
| Loading direction | Y (between the plates) | In-plane compression |
| Edges of the specimen | Cut cells at the sides are trimmed; any wall left hanging with a free end is removed | Avoids loose stubs |
| Vertical shift | Chosen so no hole near the plates is tiny | Avoids holes too small to print |

## Per-shape setup
| Shape | Cell size | Cells across 50 mm | Relative density (lattice region, measured) | Ideal relative density, infinite lattice (Gibson–Ashby formula) |
|---|---|---|---|---|
| Hexagonal honeycomb | edge l = 4.1 mm | 7.0 | 0.30 | 0.34 |
| Triangular grid | edge l = 12 mm | 4.2 | 0.29 | 0.35 |
| Re-entrant honeycomb | inclined l = 5.7 mm, vertical h = 11.4 mm, angle 30° | 5.1 | 0.29 | 0.32 |

Relative density means the fraction of the volume that is solid. The measured value is lower than the ideal one because cells at the sides are cut off.

## Literature behind the choices
- **Cell size.** Iyibilgin et al. 2013 printed FDM honeycombs with edge lengths of 3.1 to 7.6 mm. At equal porosity, 7.6 mm gave the highest yield strength and the shortest build time. Our hexagon edge of 4.1 mm is inside that range.
- **How many cells.** Results from small specimens depend on specimen size.
  - Tekoglu, Gibson, Pardoen & Onck 2011 (*Progress in Materials Science* 56:109–138) found that 2D simulations need about 16 to 32 cells before compression results stop depending on size. In experiments on real foams, the effect faded at about 6 cells.
  - Wang & McDowell 2003 used 32 × 32 cells or more in their simulations.
  - In a 50 mm printed part, about 4 to 6 cells across is a compromise between enough repetition and walls thick enough to print. Ma's sample uses 4 cells across 60 mm.
- **Wall thickness.** Walls of 2 to 3 nozzle widths print reliably on FDM printers. This is common practice rather than a published standard.

## Decisions (week 2)
- Walls stay 1.2 mm thick.
- Top and bottom plates stay.
- Option D for density:
  - The triangle stays as it is (edge 12 mm, density 0.29).
  - The hexagon and re-entrant cells were made smaller so their density matches the triangle.
  - Hexagon edge: 5 → 4.1 mm. Re-entrant: 6 / 12 mm → 5.7 / 11.4 mm (same shape, same 30° angle).
  - Result: densities are 0.29 to 0.30 for all three shapes.
  - The hexagon cannot hit 0.29 exactly. Between edge 4.12 and 4.14 mm, one column of cells at the sides is trimmed, and the density jumps from 0.30 to 0.27. We chose 0.30 as the closer value.
  - Trade-off: the hexagon now has more cells across (7.0) than the triangle (4.2).

## Defects (week 2, step 4)

### How a defect is added
- The printer builds the part from the bed upward, one 0.2 mm layer at a time (about 50 layers for 10 mm). Z is the print direction.
- Printing defects happen during certain layers, so each defect covers a height range.
- The part is built as stacked slices: normal slices outside the defect range, changed slices inside it. The slices are then joined into one solid (manifold3d).
- Each defect covers the whole layer (lattice walls and end plates). Defects in only part of a layer can come later.

### Defect types and sizes
| Defect | What changes | Small | Medium | Severe | Basis |
|---|---|---|---|---|---|
| Under-extrusion (too little plastic) | Walls and plates thinner in a 1 mm band | walls 1.08 mm (90% flow) | 0.96 mm (80%) | 0.84 mm (70%) | Printer flow range in [the 2025 flow study](https://reference-global.com/article/10.2478/bipcm-2025-0023) (85–102%); flow scales line width ([CNC Kitchen](https://cnckitchen.com/blog/the-effect-of-extrusion-width-on-strength-and-quality-of-3d-prints?format=amp)) |
| Over-extrusion (too much plastic) | Walls and plates thicker in a 1 mm band | 1.32 mm (110%) | 1.44 mm (120%) | 1.56 mm (130%) | Same, mirrored upward |
| Layer shift | Everything above the shift height moved along X | 0.4 mm (one nozzle line) | 0.8 mm | 1.0 mm | Estimate; no published sizes found |
| Warpage | Bottom corners lifted off the bed, fading to 0 at 15 mm from each corner | 0.3 mm | 0.6 mm | 1.0 mm | [Ramian et al. 2021](https://www.mdpi.com/1996-1944/14/22/7070/htm) |

- Plates change by the same ratio as the walls. At severe over-extrusion the plates stick out 0.27 mm past each end in Y.
- Severe layer shift is 1.0 mm, not 1.2 mm. At 1.2 mm (the wall thickness) the upright walls would touch the walls below only edge to edge.
- Under-extrusion, over-extrusion and layer shift start at 10% and 20% of the height (1 mm and 2 mm), as suggested in the meeting.
- Warpage is always at the bottom, where it happens in real prints.

### Why these sizes
- **No standard levels exist.** Defect datasets label the type only, not the size: [Kaggle FDM defects](https://www.kaggle.com/datasets/wengmhu/fdm-3d-printing-defect-dataset), [Roboflow defect classes](https://universe.roboflow.com/project-jkfnh/defects-classification-in-3d-printing-fwsu3). A [review of printing defects](https://www.researchgate.net/publication/374427434_Defects_in_3D_Printing_and_Strategies_to_Enhance_Quality_of_FFF_Additive_Manufacturing_A_Review) groups them by size but gives no levels.
- **Small thickness changes matter.** A [2026 lattice study](https://link.springer.com/article/10.1007/s00170-026-19103-4) found walls 12% thinner cut stiffness and strength by about 40% (from the abstract). So even the small level should change how the part behaves.
- **Same kinds of changes used by others.** A [lattice study](https://www.sciencedirect.com/science/article/pii/S0263822323008474) thinned walls and shifted joints sideways on purpose.
- **Warpage.** [Ramian et al. 2021](https://www.mdpi.com/1996-1944/14/22/7070/htm) printed ABS blocks on an open printer: corners lifted 0.86 mm (30 mm long) and 1.57 mm (60 mm long). Block height did not matter, which supports keeping warpage at the bottom. We print PLA (maybe TPU), which warps less than ABS, so 0.3–1.0 mm for a 50 mm part is reasonable.
- **Layer shift.** No published sizes found. Values are estimates: one nozzle line up to just under one wall thickness.

### Checks (all 63 parts pass)
- One piece (nothing floating).
- Watertight (closed surface, no holes).
- The defect region overlaps the solid (the defect sits on the structure).
- Inside the 50 × 50 × 10 mm box, except intended overhangs: layer shift in X, grown plates in Y.
- Volume change from the defect-free part: −2.8% to +2.7%.

### To confirm with Ma
- Are these sizes realistic on the Bambu printer with PLA?
- Is a layer shift along X fine?
- Is 63 parts the right number?
