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

## E1. How much damage does each defect do if we just keep printing? (2026-10-28)
- **Question:** With the "do nothing" fixer, how stiff is each part compared with a defect-free one?
- **Expectation (Amber, before running):** about 95% for under-extrusion starting at 10% (gut guess). Formula check afterwards: walls 0.8 as thick for 1 of 10 mm; 0.8 cubed is about 0.51, so that band is about half as stiff; (9 + 0.51) / 10 = 95%.
- **Setup:** `python agent/baselines.py` (plain Python, no AI). Score version 1 (formula, D8). Checker rules D7, budget mode "total".
- **Measure:** stiffness ratio (score); allowed or not (checker).
- **Result:**
  - Under-extrusion: 95.5% at every height (the 1 mm defect band is the same size wherever it is). Slightly above 95% because wall junctions overlap, so the area shrinks a bit less than the wall thickness.
  - Over-extrusion: 107.2%; **not allowed** under the "total" budget, because the printed part already used extra plastic.
  - Layer shift: 100.0%. The formula cannot see layer shift (known blind spot).
  - Warpage: 99.5%. Lifted corners remove only a little material at the bottom.
- **Failure groups:** none (no fixer is trying to fix yet).
- **Next:** write the simple rule (Amber); only under- and over-extrusion leave something for a thickness-only fixer to fix under this score.

## E2. Does Amber's simple rule fix the parts? (2026-10-28)
- **Question:** Does "make the rest of the walls off by the same amount in the other direction" bring stiffness back to 100% within the rules?
- **Expectation:** not written before the run.
- **Setup:** `python agent/baselines.py`. Same as E1, but budget mode now "remaining" (proposal rule, D7). Rule: under-extrusion → rest of walls 1.44 mm; over-extrusion → rest 0.96 mm; layer shift, warpage → do nothing.
- **Measure:** stiffness ratio; allowed or not, with reasons.
- **Result:**
  - Under-extrusion: **not allowed** at any height (two reasons: 1.44 mm on top of 0.96 mm printed walls grows 0.48 mm, limit 0.4; and uses about 14% more plastic than the budget). Stiffness would be 145% / 120% / 102% at 10 / 50 / 80%.
  - Over-extrusion: allowed, but overcorrects: 71% / 89% / 103% at 10 / 50 / 80%.
  - Layer shift, warpage: same as do nothing.
- **Failure groups:** breaks material budget: 3; breaks overhang limit: 3; overcorrects (more than 5% off target): 4 of 6.
- **Why:** the defect affected 1 mm, but the rule corrects every remaining millimetre. With the cubed rule the correction grows with the remaining height. It is about right only at 80%, where 1 mm is left (the same size as the defect).
- **Next:** Amber revises the rule (match the lost *stiffness*, not the lost *thickness*). Note: under the "remaining" budget, a part stopped at 80% with under-extrusion cannot be fully recovered (1 band left, no extra plastic).
