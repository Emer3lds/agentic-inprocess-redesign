# Open decisions for Amber

Agents write a short brief here when they reach a choice that shapes the research, then move on to other work. Amber answers in a few words. Answered decisions move to `docs/decisions.md`.

---

## O1. Which defect parts to add to Yichen's first print batch (2026-11-07)
1. **Goal it serves:** calibrate the FEA models (simulations of the part under load), and find out whether the defects matter in a real crush test. That decides which defects the paper can study (proposal sections 9 and 10).
2. **Options:**
   - (a) Healthy parts only (9 parts: 3 per shape). Cheapest. Calibrates the models but says nothing about defects.
   - (b) Healthy re-entrant plus 4 re-entrant defect parts, one per defect type (medium, starting at 10% height), 3 of each (15 re-entrant parts) plus 3 hexagon and 3 triangle healthy parts. Shows whether each defect really weakens the part.
   - (c) Like (b), but only under-extrusion and layer shift (the clearest and the most uncertain defect) to save printing time.
3. **Recommendation:** (b). Our beam model says warpage costs about 1% of stiffness and cannot see layer shift at all (E7). Only a crush test can tell us whether those two matter. If they don't, we can drop them from the paper and stop spending effort on them.
4. **How it could be wrong:** full defect parts are not the same as the paused-and-repaired parts in the proposal (section 10.3), so these tests show defect damage, not repair. Damage of about 1% may be smaller than the scatter between printed parts, so 3 replicates may not be enough to see it.
5. **What we could conclude:** whether each defect type changes stiffness and peak force by more than the part-to-part scatter, and how far the FEA predictions are from real results. We could not conclude anything about repairs yet.
- **Status:** waiting for Amber.
