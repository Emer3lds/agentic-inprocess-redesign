# Experiment log

One entry per experiment. Write the first four lines **before** running.

**What an "E" is:** one experiment = one question, answered by one run of the pipeline with one thing changed. It names the versions it used (agent, prompt, model, score), so results stay comparable. Versions of the code and prompts are recorded separately (git history, `agent/prompts/README.md`); an E records what we *learned* with them.

## Index
| E | Question | Versions | Main result |
|---|---|---|---|
| E0 | Can we build the 12 repair cases? | scenarios.py | Yes, all 12 pass checks (after one cutting bug) |
| E1 | How much damage does each defect do? | do nothing, score v1 | Under-extrusion 95.5%, over-extrusion 107.2%; layer shift invisible to the score |
| E2 | Does simple rule v1 fix the parts? | rule v1 | No: overcorrects, breaks budget and overhang |
| E3 | Does simple rule v2 (fix lost stiffness) work? | rule v2 | Yes: about 100% except late under-extrusion; the bar to beat |
| E4 | Does agent v0 run end to end? | agent v0, prompt v1 | Yes (plumbing test) |
| E5 | How does agent v0 compare with the baselines? | agent v0, prompt v1, gemini-3.6-flash | 0 wins, 6 ties, 6 losses vs rule; answers vary between runs |
| E6 | Does a calculation tool help the agent? | agents v0 and v1, Nemotron with thinking off, search (method B) | Calculator cuts average error from 2.76% to 1.17%. About level with the 10-use search; no wins against the simple rule |
| E7 | Can we trust the beam model (fast FEA calculator)? | fea/beam.py, fea/trust_checks.py | Ratios to a healthy part yes; absolute stiffness not validated; peak force not trustworthy yet |

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

## E6. Does a calculation tool help the agent? (planned 2026-11-02, run 2026-11-05)
- **Question:** with a tool that reports plastic used, a stiffness estimate and rule violations (10 calls per case), does the agent get closer to 100% than v0, the simple rule, and a non-AI search with the same tool and budget?
- **Expectation (Amber, written 2026-11-02 before the run):**
  1. Agent v1 beats agent v0.
  2. Unsure whether it beats the simple rule.
  3. Agent v1 beats the search at 10 calls (written 2026-11-05 before the run, while Amber believed the agent had unlimited calculator uses; both actually get 10).
  4. Agent v1 uses about 7 of its 10 calculator calls on average (gut guess).
  - **Revised by Amber (2026-11-05, after learning both get 10 calls, before seeing any results):** agent v1 does better than the search at 10 calls, but not by much, partly because the designs are simple and only wall thickness can change.
- **Setup:** `python agent/agent_v0.py --runs 3 --experiment e6_v0_nemotron` and `python agent/agent_v1.py --runs 3 --experiment e6_v1_nemotron` (use the AI, thinking off, D11). Only change from E5: the tool and the prompt section describing it (prompt v2_tools = v1 with OUTPUT replaced by TOOLS). Same cases, checker, attempts and fallback; both agents run on free Nemotron 3 Ultra (D11), so agent v0 is rerun on it first. Compared with `python agent/search.py` (COBYLA, same tool, same 10-call budget; also shown at 200 calls).
- **Measure:** stiffness error (main), peak-force error (the tool does not report it), tool calls used, wins/ties/losses against rule v2 and search at 10 calls, spread across runs.
- **Already known (no AI):** search at 10 calls: 95.9 to 101.1% (mean error 0.9%); at 200 calls it reaches about 100% except late under-extrusion (95.9%). Against E5's agent v0 the 10-call search has 4 wins, 8 ties.
- **Result:** 72 runs, none skipped. Full table: `out/results/e6_table.md` (built by `agent/results_table.py`). Average error from 100%, stiffness / peak force:
  - Do nothing 3.05% / 2.00%; simple rule 0.79% / 0.90%; search at 10 uses 1.01% / 0.82%; search at 200 uses 0.41% / 0.60%.
  - Agent v0 (no calculator) 2.76% / 1.84%; agent v1 (calculator) 1.17% / 0.96%.
  - Agent v1 case by case (tie = within 0.5 points): against v0 4 wins, 8 ties, 0 losses; against the 10-use search 2 wins, 8 ties, 2 losses; against the simple rule 0 wins, 9 ties, 3 losses.
- **Predictions checked:**
  1. v1 beats v0: **right.**
  2. Unsure against the simple rule: it did not beat the rule.
  3. Revised, v1 slightly better than the 10-use search: **not supported.** They are about level, and the search's average is slightly better. Three runs per case are too few to separate them.
  4. About 7 of 10 calculator uses: 4.8 overall, but **7.5** on under- and over-extrusion, and 2.0 on layer shift and warpage, where there is little to fix.
- **Failure groups (from the logged reasoning):**
  - **Under-extrusion, did not find the idea of moving plastic between bands:** it mostly tried making all bands thicker, hit the plastic limit, and concluded the original design was best. 5 of 9 runs ended on the original design (95.5%). One of them had already checked an allowed design at 96.6%.
  - **Stops too early:** over-extrusion at 80%, run 3 used 2 calculator uses and stopped at 103.3%; the other two runs reached 100.5%.
- **Only the 6 under- and over-extrusion cases separate the methods.** The score barely registers layer shift and warpage (known since E1), so those 6 cases tie almost by default and dilute the averages. On the 6 cases, average stiffness error: do nothing 5.86%, v0 5.27%, v1 2.15%, search at 10 uses 1.91%, simple rule 1.34%, search at 200 uses 0.79%. v1 against the rule: 0 wins, 3 ties, 3 losses; against the search: 2 wins, 2 ties, 2 losses.
- **Limits:** thinking was off for both agents, so scores may understate the model. On Gemini with thinking on, the calculator-free agent averaged 1.67% (E5), much better than the 2.76% here, so the size of the calculator's benefit may be smaller with thinking on. The calculator's stiffness estimate is the same formula as the score, so only peak force is a measure the agent could not aim at.
- **Next:** teach or tool the agent to redistribute plastic only if a test calls for it; the larger step is the full redesign Ma asked for, where a simple rule and a small search have a harder job.

## E7. Can we trust the beam model? (2026-11-07)
- **Question:** does the new beam model (fast FEA calculator, decision D12) give answers we can believe? Three checks: exact single-wall answers, healthy parts against the Gibson & Ashby textbook formula (target within 10%), and the 12 re-entrant cases against the formula score.
- **Expectation:** no prediction was recorded.
- **Setup:** `python fea/trust_checks.py` (plain code, no AI, about 1 minute). The beam model is `fea/beam.py`: a 2D frame model written with numpy (OpenSeesPy does not run on this laptop's Python 3.13). Each wall is a beam that stretches and bends. Walls are held where they meet the end plates. The top plate is pushed down along Y. Run time about 0.01 to 0.08 seconds per layer.
- **Measure:** difference from exact answers; difference from the formula on healthy parts; stiffness as % of a healthy part for each of the 12 cases; peak force. Results: `out/results/e7_beam_checks.json`.
- **Result:**
  - **Check 1, single wall:** the solver matches the exact answers (0.0000% difference).
  - **Check 2, healthy parts vs the formula (target within 10%):** hexagon -6.3% (pass), triangle -3.7% (pass), re-entrant -19.3% (fails). With walls that cannot stretch, re-entrant is +3.2%. So most of the gap comes from wall stretching, which the formula leaves out and which matters because these walls are thick for their length.
  - **Check 3, the 12 re-entrant cases, "do nothing"** (stiffness % of healthy, formula -> beam model):
    | Defect | Formula | Beam model |
    |---|---|---|
    | Under-extrusion | 95.5 | 95.5 |
    | Over-extrusion | 107.2 | 105.8 |
    | Layer shift | 100.0 | 100.0 |
    | Warpage | 99.5 | 99.0 |
    The beam model is blind to layer shift, like the formula. For warpage it sees twice the damage, still small.
  - **Simple rule's fixes:** about 1 point lower under the beam model (for example over-extrusion at 50%: 99.6 formula, 98.5 beam), because the rule was designed with the formula.
  - **Does the beam score tell a fix from doing nothing?** (tie margin 0.5 points) Yes for under-extrusion at 10% and 50%, all over-extrusion cases, and warpage at 10% and 50% (by about 1 point, just over the margin). No for layer shift (blind). No for under-extrusion at 80%: the case rules cause this, not the model. The only allowed fix (1.21 mm walls) reaches 95.8%; 1.36 mm would reach 99.3% but breaks the plastic budget.
  - **Peak force:** a review found that adding up each layer's own yield force assumes a layer keeps carrying load after it yields. A second, cautious number was added: the whole part's first yield (all layers squeezed by the same amount). For "do nothing" at 10%, added up vs first yield: under-extrusion 96.4% vs 95.5%; over-extrusion 104.2% vs 95.2%; warpage 98.3% vs 68.3% (one cut wall near a corner yields first).
- **Failure groups:** healthy part outside the 10% target: 1 of 3 shapes (re-entrant).
- **What it means:**
  - The solver is correct on exact cases.
  - Trust only ratios to a healthy part. A review noted the hexagon's close match is partly two effects cancelling (holding the walls at the plates adds about 40%, wall stretching removes about 20 to 30%), so absolute stiffness is not validated.
  - The beam score separates fixes from doing nothing in most under-extrusion, over-extrusion and warpage cases.
  - No peak-force claim until CalculiX (3D judge) or crush tests.
- **Limits:** only re-entrant cases were tested; hexagon and triangle cases do not exist yet. Blind to layer shift. Absolute stiffness not validated. Peak force not trustworthy yet.
- **Next:** CalculiX judge; compare with Yichen's physical prints once they arrive.
