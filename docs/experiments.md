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

## E3. Simple rule version 2: fix the lost stiffness, not the lost thickness (2026-10-28)
- **Question:** Does a rule that measures the missing (or extra) stiffness and corrects exactly that amount get close to 100% within the rules?
- **Expectation (Claude, said before running but not written here first):** under-extrusion about 100% at 10%, about 99% at 50%, stuck at 95.5% at 80% (one band left, no spare plastic); over-extrusion about 100% at every height; layer shift and warpage unchanged.
- **Setup:** `python agent/baselines.py`. Rule v2 (Amber asked Claude to write it): measure the stiffness gap from the printed part. Too stiff: thin all remaining bands equally. Too weak: thin/thick pairs (1.0 / 1.4 mm) right above the defect, as many as help. Budget "remaining".
- **Result:** all 12 allowed.
  - Under-extrusion: 100.3% / 97.9% / 95.5% at 10 / 50 / 80% (fixes: 4 pairs, 2 pairs, none possible).
  - Over-extrusion: 100.2% / 99.6% / 100.5% (all bands thinned to 1.16 / 1.11 / 0.8 mm).
  - Layer shift 100% (blind spot), warpage 99.5% (one pair would overshoot, so the rule does nothing).
- **Failure groups:** more than 1% off target: 2 (under-extrusion at 50% and 80%: not enough bands left).
- **Caveat:** the under-extrusion fix relies on thick/thin stacking, the effect flagged under D8 (Goodhart's law). The math holds for bending stiffness, but thin bands may break first in a real crush test. Strength is not scored yet.
- **Next:** this rule is now the bar the AI agent must beat. Also missing: a non-AI search over thicknesses (proposal method B).

## E4. Smoke test: does agent v0 run end to end? (2026-10-29)
- **Question:** does the loop (prompt -> AI -> checker -> log) work on one case? This is a plumbing test, not an experiment, so no prediction.
- **Setup:** `python agent/agent_v0.py --cases under_extrusion_medium_z10 --runs 1 --experiment smoke_v1` (uses the AI). Prompt v1, `gemini-3.5-flash`. Log: `out/runs/smoke_v1.jsonl`.
- **Result:** allowed on the first attempt. Fix `[1.36, 1.58, 1.11 x 6]`, stiffness **98.8%** (simple rule v2: 100.3%; do nothing: 95.5%). Material 6823 of 6831 mm3. 30 s per call, about 550 tokens.
- **Observations:**
  - The prompt did not mention the cubed rule, but the agent used it on its own ("stiffness scales with the cube of the wall thickness").
  - It treated the material budget as "sum of thicknesses = 8 x 1.2 = 9.6 mm". That is close, but not exact, because walls overlap at junctions. Its own math said about 100%; the score says 98.8%.
  - It used the full 0.4 mm overhang step correctly (0.96 -> 1.36).
  - Google reported model version `gemini-3.6-flash`, although we asked for `gemini-3.5-flash`. The name we request is not a guarantee of the model that answers, which is why each attempt logs the reported version.
- **Next:** the full run (12 cases x 3 runs), with Amber's prediction written first.

## E5. Agent v0 on all 12 cases, 3 runs each (2026-10-29)
- **Question:** how does the AI agent (prompt v1) compare with "do nothing" and simple rule v2, and how much do its answers vary?
- **Expectation (Amber, written before the run):**
  1. It beats the simple rule in about half of the 12 cases (gut guess).
  2. It does worst on layer shift and warpage, because wall thickness changes can't do much for them.
  3. Its 3 runs of the same case give the same answer, since it's a simple question.
- **Setup:** `python agent/agent_v0.py --runs 3 --experiment e5_v1_full` (uses the AI). Prompt v1, `gemini-3.5-flash` requested, at most 3 attempts, fallback "do nothing". Log: `out/runs/e5_v1_full.jsonl`.
- **Measure:** stiffness error from 100% (mean and spread of the 3 runs); allowed on which attempt; fallbacks; wins/ties/losses against simple rule v2 (a tie is within 0.5%).
- **Result:** 36 runs (one duplicate log line ignored). Agent vs simple rule: **0 wins, 6 ties, 6 losses.** Every final answer passed the checker; only 1 of 37 attempts was rejected (material budget), so the retry loop was barely used.
  | Defect | 10% | 50% | 80% | vs rule |
  |---|---|---|---|---|
  | Under-extrusion | 96.2 / 98.8 / 95.5 | 99.0 / 95.5 / 98.7 | 95.5 (x3) | loss, tie, tie |
  | Over-extrusion | 102.0 / 100.6 / 100.6 | 102.1 / 102.1 / 100.4 | 102.7 (x3) | loss, loss, loss |
  | Layer shift | 100.0 (x3) | 100.0 / 103.6 / 100.9 | 100.0 (x3) | tie, loss, tie |
  | Warpage | 106.1 / 99.5 / 99.5 | 99.5 (x3) | 99.5 (x3) | loss, tie, tie |
  (Do nothing: under 95.5, over 107.2, shift 100.0, warpage 99.5. Simple rule: see E3.)
- **Predictions checked:**
  1. "Beats the rule in about half": **wrong.** No wins.
  2. "Worst on layer shift and warpage": **partly.** It lost one case each there, by "fixing" damage our score can't see. Its most consistent losses were over-extrusion (3 of 3).
  3. "Same answer every run": **wrong.** 6 of 12 cases gave different answers across runs; the identical ones were mostly cases with nothing to fix.
- **Failure groups (from the logged reasoning):**
  - **Corrects thickness instead of stiffness (over-extrusion):** at 80% it set the last band to 1.2 - 0.24 = 0.96 mm, the same mistake as simple rule v1. Result 102.7%; the rule's stiffness-based 0.8 mm gives 100.5%.
  - **Fixes what the score can't see (layer shift, warpage):** it reasoned that layer shift and warpage weaken the part (physically plausible) and added thick/thin bands, overshooting to 103.6% and 106.1%. This is partly a blind spot of our score (D8), not only an agent error.
  - **Inconsistent effort (under-extrusion):** on the same case, one run redistributed plastic (98.8%), another kept the original design (95.5%).
- **Also seen:** it knowingly used the thick/thin effect ("Jensen's inequality"), the loophole flagged under D8.
- **Next ideas (not decided):** prompt v2 written as code (code-prompting paper); give it a tool that calculates plastic used, or the stiffness formula, so feedback helps it aim and not only stay within the rules.
