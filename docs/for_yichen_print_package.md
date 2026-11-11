# Print package for Yichen (first calibration batch)

Prepared 2026-11-07, updated 2026-11-11 after Amber chose option (b) (decision D14).

Purpose, in two parts:
1. **Healthy parts:** calibrate the FEA models (computer simulations of the part under load) against real crush tests (decision D12, from the 2026-11-05 meeting).
2. **Defect parts:** find out whether each defect type really weakens a part. Our beam model says warpage costs about 1% of stiffness and layer shift costs nothing, and only a crush test can check that.

## Files: 21 parts (7 designs, 3 copies each)
All in the GitHub repo https://github.com/Emer3lds/agentic-inprocess-redesign.

| # | Design | File | Copies | Why it is in the batch |
|---|---|---|---|---|
| 1 | Healthy hexagon | `out/base/hexagon.stl` | 3 | Calibration |
| 2 | Healthy triangle | `out/base/triangle.stl` | 3 | Calibration |
| 3 | Healthy re-entrant | `out/base/reentrant.stl` | 3 | Calibration, and the reference for the defect parts |
| 4 | Re-entrant, under-extrusion | `out/defects/reentrant/reentrant_under_extrusion_medium_z10.stl` | 3 | Does it weaken the part? |
| 5 | Re-entrant, over-extrusion | `out/defects/reentrant/reentrant_over_extrusion_medium_z10.stl` | 3 | Does it change the part? |
| 6 | Re-entrant, layer shift | `out/defects/reentrant/reentrant_layer_shift_medium_z10.stl` | 3 | Our model can't see it; does it matter? |
| 7 | Re-entrant, warpage | `out/defects/reentrant/reentrant_warpage_medium.stl` | 3 | Our model sees about 1%; does it matter? |

Why 3 copies: two prints of the same file never come out exactly the same. With 3, we can tell print-to-print scatter apart from simulation error.

## What each defect file contains (medium severity)
These files have the defect drawn into the shape. Printed normally, they reproduce the defect's shape, not how it forms on a real printer.
- **Under-extrusion:** walls 0.96 mm instead of 1.2 mm (80% flow) in a 1 mm band starting at 10% of the height (Z = 1.0 to 2.0 mm).
- **Over-extrusion:** walls 1.44 mm (120% flow) in the same band.
- **Layer shift:** everything above 10% of the height moved 0.8 mm sideways along X.
- **Warpage:** bottom corners lifted 0.6 mm, fading to 0 at 15 mm from each corner. The lifted corners would print on air, so this file cannot be printed flat without support material.

## Design parameters (healthy parts)

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

## Questions for Yichen
1. Could the defect parts be made on the printer instead, by changing settings during the print? For example, 80% flow for 1 mm for under-extrusion, 120% for over-extrusion, or a 0.8 mm sideways offset for layer shift. That would be more realistic (real under-extrusion also bonds layers more weakly), but it takes more of your time.
2. For warpage: print the file with supports under the lifted corners, try to cause real warping, or leave it out of this batch?

## What we need back
1. Force–displacement curve for each part (raw data file), plus test speed and machine.
2. Measured wall thickness on a few walls per part (calipers or microscope). Printed walls usually differ from the design, and this is the main cause of simulation errors in the literature.
3. Material values for the PLA: stiffness (Young's modulus) and yield stress, ideally from small test bars printed with the same settings and direction.
4. Photos of how each part failed.

---

## Paste-ready message for Teams

Hi Yichen, here are the files and design parameters for the first calibration batch. It's 21 parts: 7 designs, 3 copies each.

- Healthy hexagon, triangle and re-entrant (out/base/hexagon.stl, triangle.stl, reentrant.stl), to calibrate the FEA model.
- Four re-entrant parts with one defect each, to see whether each defect weakens a real part: under-extrusion, over-extrusion, layer shift and warpage (out/defects/reentrant/, the four files ending in medium_z10.stl, and reentrant_warpage_medium.stl).

Repo: https://github.com/Emer3lds/agentic-inprocess-redesign. All parts are 50 × 50 × 10 mm with 1.2 mm walls and 1.8 mm end plates. Print with Z up, 0.2 mm layers, PLA, and compress along Y between the end plates.

Two questions:
1. The defect files have the defect drawn into the shape. Could you instead make the defects on the printer, for example 80% flow for 1 mm or a 0.8 mm sideways shift? That would be more realistic.
2. The warpage file has its bottom corners lifted 0.6 mm, so it would need supports. Would you rather print it with supports, try to cause real warping, or skip it for now?

Could you send back the force–displacement data, a few measured wall thicknesses per part, and the PLA stiffness and yield values (or the filament details)? Thanks!
