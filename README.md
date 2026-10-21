# Week 2: Lattice design → graph → STL (→ defects)

## Files
- `lattice.py`: builds a lattice graph, turns it into a 2D cross-section, and extrudes it into an STL.
- `build_base.py`: builds the three defect-free lattices.
- `out/base/<shape>_graph.json`: the graph (nodes, edges, wall thickness, plates, defect list).
- `out/base/<shape>.stl`: the printable part.
- `out/base/<shape>.png`: top view.
- `out/base/summary.json`: checks and measurements.

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
| Hexagonal honeycomb | edge l = 5 mm | 5.8 | 0.23 | 0.28 |
| Triangular grid | edge l = 12 mm | 4.2 | 0.29 | 0.35 |
| Re-entrant honeycomb | inclined l = 6 mm, vertical h = 12 mm, angle 30° | 4.8 | 0.25 | 0.31 |

Relative density means the fraction of the volume that is solid. The measured value is lower than the ideal one because cells at the sides are cut off.

## Literature behind the choices
- **Cell size.** Iyibilgin et al. 2013 printed FDM honeycombs with edge lengths of 3.1 to 7.6 mm. At equal porosity, 7.6 mm gave the highest yield strength and the shortest build time. Our hexagon edge of 5 mm is inside that range.
- **How many cells.** Results from small specimens depend on specimen size.
  - Tekoglu, Gibson, Pardoen & Onck 2011 (*Progress in Materials Science* 56:109–138) found that 2D simulations need about 16 to 32 cells before compression results stop depending on size. In experiments on real foams, the effect faded at about 6 cells.
  - Wang & McDowell 2003 used 32 × 32 cells or more in their simulations.
  - In a 50 mm printed part, about 4 to 6 cells across is a compromise between enough repetition and walls thick enough to print. Ma's sample uses 4 cells across 60 mm.
- **Wall thickness.** Walls of 2 to 3 nozzle widths print reliably on FDM printers. This is common practice rather than a published standard.

## Open choice
The shapes cannot have the same wall thickness, the same density, and the same number of cells all at once. Right now the wall thickness is equal and the densities are close (0.23 to 0.29).
- **Triangle at equal density:** l would need to be about 15 mm, giving only about 3.3 cells across.
- **Triangle with about 6 cells across at the same density:** walls would need to be about 0.8 mm, which is 2 nozzle lines.
