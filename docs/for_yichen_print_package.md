# Print package for Yichen (first calibration batch)

Prepared 2026-11-07. Purpose: print and crush-test healthy parts, so the FEA models (computer simulations of the part under load) can be calibrated against real results (decision D12, from the 2026-11-05 meeting). Which defect parts to add is an open decision for Amber (see `docs/open_decisions.md`).

## Files (healthy parts, one per shape)
All in the GitHub repo https://github.com/Emer3lds/agentic-inprocess-redesign, folder `out/base/`:
- `hexagon.stl`
- `reentrant.stl`
- `triangle.stl`

## Design parameters

| | Hexagon | Re-entrant | Triangle |
|---|---|---|---|
| Specimen | 50 × 50 × 10 mm | 50 × 50 × 10 mm | 50 × 50 × 10 mm |
| Cell size | edge 4.1 mm | inclined walls 5.7 mm, vertical walls 11.4 mm, angle 30° | edge 12.0 mm |
| Cell width / cells across | 7.1 mm / 7.0 | 9.87 mm / 5.1 | 12.0 mm / 4.2 |
| Wall thickness | 1.2 mm | 1.2 mm | 1.2 mm |
| End plates (at both Y ends) | 1.8 mm | 1.8 mm | 1.8 mm |
| Lattice density (walls only) | 0.30 | 0.29 | 0.286 |
| Part volume | 8762.9 mm³ | 8539.0 mm³ | 8434.9 mm³ |

## How to print and test (so the simulation matches the test)
- **Print direction:** Z (the 10 mm side stands up from the bed). Layer height 0.2 mm.
- **Walls:** 1.2 mm = 3 lines of a 0.4 mm nozzle. Please note the slicer's line width and flow if they differ.
- **Material:** PLA. Please send the filament brand and any datasheet values.
- **Loading:** compress along Y, between the two end plates.
- **Replicates:** 3 of each shape if possible (9 parts). One part per shape gives no idea of the scatter.

## What we need back
1. Force–displacement curve for each part (raw data file), plus test speed and machine.
2. Measured wall thickness on a few walls per part (calipers or microscope). Printed walls usually differ from the design, and this is the main cause of simulation errors in the literature.
3. Material values for the PLA: stiffness (Young's modulus) and yield stress, ideally from small test bars printed with the same settings and direction.
4. Photos of how each part failed.

---

## Paste-ready message for Teams

Hi Yichen, here are the STL files and design parameters for the first calibration batch: three healthy lattices (hexagon, re-entrant, triangle), each 50 × 50 × 10 mm with 1.2 mm walls and 1.8 mm end plates. Files: https://github.com/Emer3lds/agentic-inprocess-redesign, folder out/base/ (hexagon.stl, reentrant.stl, triangle.stl). Print with Z up, 0.2 mm layers, PLA, and compress along Y between the end plates. 3 of each would be ideal. Could you send back the force–displacement data, a few measured wall thicknesses per part, and the PLA stiffness and yield values (or the filament details)? I'll use them to calibrate the FEA model. I'll follow up separately about adding a few defect parts.
