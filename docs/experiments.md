# Experiment log

One entry per experiment. Write the first four lines **before** running.

Template:
- **Question:** what we want to learn.
- **Expectation:** what we think will happen, and why.
- **Setup:** what changes (only one thing at a time) and what stays fixed.
- **Measure:** the numbers we will look at.
- **Result:** what happened (including failures).
- **Failure groups:** bad outputs sorted by kind, with counts.
- **Next:** what this tells us to do.

---

## E0. Can we build the repair cases? (2026-10-26)
- **Question:** Can every defect be cut at the moment the printer stops, as one clean piece?
- **Expectation:** yes; the cut is a simple box intersection.
- **Setup:** 12 cases (D3), stop rule D2.
- **Measure:** one piece, watertight, top at the cut height.
- **Result:** first run 11 / 12. Under-extrusion at 10% left zero-volume scraps because the cut sat exactly on the top of the defect band. Cutting 0.1 micron lower fixed it: 12 / 12.
- **Failure groups:** cut on a boundary between two bands: 1.
- **Next:** build the checker and the simple methods (session 2).
