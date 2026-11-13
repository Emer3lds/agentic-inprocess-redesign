# Print package for Yichen (first calibration batch)

Prepared 2026-11-07. Updated 2026-11-11 (decision D14) and 2026-11-12 (decision D15: stronger defects, warpage dropped).

Purpose, in two parts:
1. **Healthy parts:** calibrate the FEA models (computer simulations of the part under load) against real crush tests (decision D12, from the 2026-11-05 meeting).
2. **Defect parts:** find out whether each defect type really weakens a printed part. The defects are made strong enough (about 20% predicted change) to stand out from the usual scatter between printed copies (proposal sections 10.1 and 10.2).

## Files: 18 parts (6 designs, 3 copies each)
All in the GitHub repo https://github.com/Emer3lds/agentic-inprocess-redesign.

| # | Design | File | Copies | Predicted stiffness (% of healthy) | Why it is in the batch |
|---|---|---|---|---|---|
| 1 | Healthy hexagon | `out/base/hexagon.stl` | 3 | 100 | Calibration |
| 2 | Healthy triangle | `out/base/triangle.stl` | 3 | 100 | Calibration |
| 3 | Healthy re-entrant | `out/base/reentrant.stl` | 3 | 100 | Calibration, and the reference for the defect parts |
| 4 | Re-entrant, under-extrusion | `out/print_batch/reentrant_under_extrusion_3mm_70pct.stl` | 3 | about 80 to 82 | Does it weaken the part as predicted? |
| 5 | Re-entrant, over-extrusion | `out/print_batch/reentrant_over_extrusion_3mm_120pct.stl` | 3 | about 117 to 122 | Does it stiffen the part as predicted? |
| 6 | Re-entrant, layer shift | `out/print_batch/reentrant_layer_shift_1p0mm.stl` | 3 | 100 (our models can't see it) | Does it matter in a real part? |

Predicted values are from the simple stiffness formula and the 2D beam model (`out/print_batch/summary.json`).

Why 3 copies: two prints of the same file never come out exactly the same. With 3, we can tell print-to-print scatter apart from simulation error.

Why no warpage part: every model predicts about 1% or less, which a crush test of 3 copies can't show, and the file would need supports under its lifted corners.

## What each defect file contains
These files have the defect drawn into the shape. Printed normally, they reproduce the defect's shape, not how it forms on a real printer.
- **Under-extrusion:** walls 0.84 mm instead of 1.2 mm (70% flow) in a 3 mm band from 1 to 4 mm height. The end plates are 70% as thick in that band too. Not thinner: 0.84 mm is just above two 0.4 mm nozzle lines.
- **Over-extrusion:** walls 1.44 mm (120% flow) in the same band. The end plates are 120% as thick in that band, so they stick out 0.18 mm on each side.
- **Layer shift:** everything above 1 mm height moved 1.0 mm sideways along X.

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
1. Could the defect parts be made on the printer instead, by changing settings during the print? For example, 70% flow for 3 mm for under-extrusion, 120% for over-extrusion, or a 1 mm sideways offset for layer shift. That would be more realistic (real under-extrusion also bonds layers more weakly), but it takes more of your time.
2. How big are real layer shifts on your printers? Ours is 1.0 mm, and we don't have a published value.
3. Loading direction: we plan to compress along Y only (between the end plates), as Ma asked for one fixed axis (decision D6). Should some parts also be tested along Z, the print direction? Z loads the bonds between layers, which is where layer shift and real under-extrusion would matter most.
4. How do you read stiffness from the curve: right at first contact, or after the part has settled against the plates? The over-extruded part's end plates stick out 0.18 mm, so this changes its result (decision brief O3).

## What we need back
1. Force–displacement curve for each part (raw data file), plus test speed and machine.
2. Measured wall thickness on a few walls per part (calipers or microscope). Printed walls usually differ from the design, and this is the main cause of simulation errors in the literature.
3. Material values for the PLA: stiffness (Young's modulus) and yield stress, ideally from small test bars printed with the same settings and direction.
4. Photos of how each part failed.

The full paste-ready message, with the progress update, is at the top of `docs/progress.md`.
