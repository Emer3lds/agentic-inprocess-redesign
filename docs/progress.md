# Progress summary

Running summary of the work, one section per week, written to send to Ma. Each week has a short version (a few lines to paste into a message) and a detailed version.

---

## Next two weeks (meeting 2026-11-05; next full meeting in about 2 weeks)

### Short version
- **Goal from the meeting:** build a proper evaluator with FEA (finite element analysis), and check it against physical tests before testing prompts.
- **FEA:** find a mature Python package and try a simple design on the laptop first.
- **Physical tests:** Yichen sends the PLA material details. Amber sends STL files and design parameters by next week. Yichen prints and tests them, and Amber compares FEA with the results and calibrates it.
- **After FEA:** look into RSI (recursive self-improvement) over the agents, using the FEA evaluator to judge them. Yichen isn't sure of the exact definition yet, so part of the job is finding it. Prompt testing comes right after the evaluator is solid.
- **Full redesign:** letting the agent change more than wall thickness is still planned, to be thought through by the next meeting.
- **Where to publish:** Yichen said ICML probably isn't mechanical enough, so we may look at other journals. No venue is chosen.

### Paste-ready message for Yichen (to send 2026-11-13)
Covers everything since the 2026-11-05 meeting, including the two short versions below, plus the print request from `docs/for_yichen_print_package.md`.

Hi Yichen, here's my update and the files for the first print batch.

**Print batch: 21 parts**
- 3 copies each of the healthy hexagon, triangle and re-entrant, to calibrate the FEA model.
- 3 copies each of 4 re-entrant defect parts (under-extrusion, over-extrusion, layer shift, warpage), to see whether each defect really weakens a part.
- Files: https://github.com/Emer3lds/agentic-inprocess-redesign
  - out/base/: hexagon.stl, triangle.stl, reentrant.stl
  - out/defects/reentrant/: reentrant_under_extrusion_medium_z10.stl, reentrant_over_extrusion_medium_z10.stl, reentrant_layer_shift_medium_z10.stl, reentrant_warpage_medium.stl
  - Design parameters: docs/for_yichen_print_package.md
- All parts are 50 × 50 × 10 mm with 1.2 mm walls and 1.8 mm end plates. Print with Z up, 0.2 mm layers, PLA, and compress along Y between the end plates.
- Could you send back the force–displacement data, a few measured wall thicknesses per part, the PLA stiffness and yield values (or the filament details), and photos of how each part failed?

**Questions**
1. The defect files have the defect drawn into the shape. Could you instead make the defects on the printer, for example 80% flow for 1 mm or a 0.8 mm sideways shift? That would be more realistic.
2. The warpage file has its bottom corners lifted 0.6 mm, so it would need supports. Would you rather print it with supports, try to cause real warping, or skip it for now?
3. We plan to compress along Y only. Is that right, or would you also like some parts tested along Z (the print direction)? Z would load the bonds between layers, where layer shift and real under-extrusion probably matter most.
4. How do you measure stiffness from the curve: right at first contact, or after the part has settled against the plates? The over-extruded part's end plates stick out 0.18 mm in a 1 mm strip, so this changes its result.

**FEA progress**
- **Fast calculator (2D beam model, each wall is a beam):** matches exact single-wall answers, and matches OpenSeesPy to 0.0000% on all three shapes. It runs in well under a second, so the agent can use it to check designs.
- **Judge (3D model, gmsh + CalculiX):** gives the exact answer on a test block. Healthy parts (placeholder PLA values): hexagon 2418, re-entrant 986, triangle 4422 N/mm.
- **Fast calculator vs judge:** the beam model is lower by 15%, 33% and 5%, because it treats walls as lines and misses the solid joints. But as a % of a healthy part they agree within about 1 point for under- and over-extrusion, which is what we score.
- **Layer shift:** the 3D model sees it, but as 4.7% stiffer, because it treats the layers as perfectly bonded. Your crush tests on the layer-shift parts will show what really happens.
- **STL fix:** I found and fixed a problem in my STL export (hidden faces inside the part where walls cross). Shapes and volumes are unchanged, and the files on GitHub are the fixed ones.
- **Limits:** the 3D mesh size isn't fully settled yet; my laptop's memory (6 GB) limits finer meshes, so I may need PACE later; material values are placeholders until your data arrives.

**Next:** finish the mesh check, then calibrate the 3D model against your crush tests, then look into RSI using the 3D model as the judge.

### Short version: since the last message (2026-11-07)
- **FEA calculator built:** a beam model (each wall is a beam; fast, about 0.01 to 0.08 seconds per layer). I wrote it with numpy because OpenSeesPy's Windows version needs Python 3.12 and my laptop has 3.13. CalculiX (3D) is still planned as the locked judge.
- **Trust checks (E7):** the solver matches exact single-wall answers. Against the Gibson & Ashby formula on healthy parts (target within 10%): hexagon -6.3% and triangle -3.7% pass; re-entrant -19.3% fails, mostly because the formula leaves out wall stretching. The hexagon match is partly two effects cancelling, so only ratios to a healthy part are trusted, not absolute stiffness.
- **Does it tell a fix from doing nothing?** Yes for under-extrusion at 10% and 50%, all over-extrusion cases, and warpage at 10% and 50% (by about 1 point). No for layer shift (the model is blind to it) and no for under-extrusion at 80% (the case rules cause this).
- **Peak force:** a cautious "whole part first yields" number disagrees a lot with the added-up number (warpage 68.3% vs 98.3%). No peak-force claim until CalculiX or crush tests.
- **Print package for Yichen:** STL files, design parameters and a Teams message are drafted in `docs/for_yichen_print_package.md`. Due about 2026-11-12. The first batch is 21 parts (decision D14).

### Short version: since the last message (2026-11-11)
- **First print batch chosen (D14):** 21 parts. 3 copies each of the healthy hexagon, triangle and re-entrant, to calibrate the FEA model. Plus 3 copies each of 4 re-entrant defect parts (under-extrusion, over-extrusion, layer shift, warpage), to see whether each defect weakens a real part. 3 copies so print-to-print scatter can be told apart from simulation error.
- **Limit:** the defect files have the defect drawn into the shape. Printed normally, they copy the defect's shape but not how it forms. For example, a thinner wall printed at normal flow still bonds normally. Amber is asking Yichen whether he can make real defects by changing printer settings, and how to handle warpage, whose lifted corners would need supports.

### Done
- **All 71 other part files rebuilt (2026-11-12)** with the fixed STL method. Case records identical; scores unchanged except the 3 warpage cases (at most 0.06 points). A new check flags hidden inside faces automatically.
- **Beam model cross-checked against OpenSeesPy, E10 (2026-11-12):** identical (0.0000%) on all 3 shapes, with normal and with mixed wall thicknesses. So our beam code has no bugs; its gap to the 3D model comes from treating walls as lines.
- **3D model on defect parts, E9 first half (2026-11-12, 1.2 mm pieces):** % of healthy, 3D vs beam model: under-extrusion 96.5 vs 95.6; over-extrusion 107.1 vs 105.8 (whole end faces held); warpage 100.3 vs 99.0; layer shift 104.7 vs 100.0. The 3D model sees layer shift, but as stiffer, not weaker, because it treats layers as perfectly bonded. The 0.8 mm half needs more free memory. Open choice: how to hold over-extruded parts, whose end plates stick out 0.18 mm in a 1 mm strip.
- **First 3D solid model, E8 (2026-11-12):** `fea/solid3d.py` (gmsh + CalculiX). Exact on a block. Healthy parts at 1.2 mm pieces (provisional): hexagon 2418, re-entrant 986, triangle 4422 N/mm, stiffer than the beam model by 15%, 33% and 5%. Piece size not settled yet (re-entrant still falling 2.7% from 0.8 to 0.6 mm), and the laptop's memory limits finer pieces. It also found zero-thickness faces inside the triangle and re-entrant STLs where walls cross, caused by the method used to turn each cross-section into a solid. Fixed, and the 7 files for Yichen were rebuilt (same shape and volume); the 3D model now reads them directly. The other 71 part files are not rebuilt yet. Details in `docs/experiments.md` (E8).
- **3D FEA tools installed and tested (2026-11-12):** CalculiX 2.23 (the 3D solver) in its own conda environment `fea`, and gmsh 4.15 (splits a part into small pieces for the solver). Test: a 10 mm PLA cube pushed 0.01 mm gives 350 N, so 35,000 N/mm, exactly the textbook answer (stiffness × area ÷ length = 3500 × 100 ÷ 10). Took about 1.5 seconds.
- **First print batch package (2026-11-07, updated 2026-11-11):** `docs/for_yichen_print_package.md` lists all 21 parts with file paths and why each is there, describes each defect file, and has questions for Yichen plus a paste-ready Teams message. Due about 2026-11-12.
- **Beam model (`fea/beam.py`, decision D12):** OpenSeesPy was the plan but only works on Python 3.12 on Windows, and this laptop has 3.13. Written directly with numpy: a standard 2D frame model (each wall is a beam that stretches and bends; walls held where they meet the end plates; top plate pushed down along Y).
- **Experiment E7, trust checks** (`python fea/trust_checks.py`, plain code, no AI, about 1 minute; results in `out/results/e7_beam_checks.json`).

### Results so far
- **Check 1:** solver matches exact single-wall answers (0.0000% difference).
- **Check 2, healthy parts vs the Gibson & Ashby formula (target within 10%):** hexagon -6.3% (pass), triangle -3.7% (pass), re-entrant -19.3% (fails). With walls that cannot stretch, re-entrant is +3.2%, so most of the gap is wall stretching, which the formula leaves out and which matters because these walls are thick for their length.
- **Review:** the hexagon's close match is partly two effects cancelling (holding the walls at the plates adds about 40%, wall stretching removes about 20 to 30%). So the check does not validate absolute stiffness; only ratios to a healthy part are trusted.
- **Check 3, the 12 re-entrant cases, "do nothing"** (stiffness % of healthy, formula -> beam model): under-extrusion 95.5 -> 95.5; over-extrusion 107.2 -> 105.8; layer shift 100.0 -> 100.0 (beam model blind to it, like the formula); warpage 99.5 -> 99.0 (beam model sees twice the damage, still small).
- **Simple rule's fixes** score about 1 point lower under the beam model (for example over-extrusion at 50%: 99.6 formula, 98.5 beam), because the rule was designed with the formula.
- **Beam score vs doing nothing** (tie margin 0.5 points): separates them for under-extrusion at 10% and 50%, all over-extrusion cases, and warpage at 10% and 50% (by about 1 point, just over the margin). Not for layer shift (blind). Not for under-extrusion at 80%: the case rules cause this, not the model. The only allowed fix (1.21 mm walls) reaches 95.8%; 1.36 mm would reach 99.3% but breaks the plastic budget.
- **Peak force:** a review found that adding up each layer's own yield force assumes a layer keeps carrying load after it yields. A second, cautious number was added: the whole part's first yield. For "do nothing" at 10%, added up vs first yield: under-extrusion 96.4% vs 95.5%; over-extrusion 104.2% vs 95.2%; warpage 98.3% vs 68.3% (one cut wall near a corner yields first).
- **Limits:** only re-entrant cases were tested (hexagon and triangle cases do not exist yet); blind to layer shift; absolute stiffness not validated; peak force not trustworthy yet.

### Key decisions
- **Beam model with numpy (D12 update):** chosen because it sees each wall, is fast enough to call many times, and gives a force estimate. Alternatives: OpenSeesPy (blocked by Python version), scikit-fem 2D continuum, CalculiX 3D (still planned as the locked judge). Limits as above.
- **First-yield peak force added after review (D12 update):** no peak-force claim until CalculiX or crush tests.
- **First print batch (D14, 2026-11-11):** option (b), 21 parts. Alternatives: healthy parts only (9 parts, nothing about defects), or only 2 defect types. Defect STL files are printed as they are, and we ask Yichen about making real defects on the printer. Limits: shape-only defects, warpage needs supports, re-entrant only, damage of about 1% may be within print scatter.

### Next
- Send the print package to Yichen (due about 2026-11-12).
- CalculiX judge; hexagon and triangle cases.

## Week 3 (meeting 2026-10-22; next meeting about 2026-11-09)

### Short version: since the last message (2026-11-05)
- **First comparison finished:** I ran two AI agents on all 12 cases, 3 times each, on one free model (Nemotron 3 Ultra). One agent has no calculator. The other can check up to 10 designs before submitting, seeing plastic used against the limit, any broken rules, and estimated stiffness. That estimate uses the same formula as the final stiffness score, so for now the agent can aim directly at it. Only peak force is hidden.
- **Only 6 of the 12 cases separate the methods:** the stiffness formula can't see layer shift and barely registers warpage, so those 6 cases tie almost by default. Results below are for the 6 under- and over-extrusion cases.
- **Average distance from a healthy part's stiffness (lower is better):** keep original design 5.86%; agent, no calculator 5.27%; agent, calculator 2.15%; non-AI search, same 10 calculator uses 1.91%; simple rule 1.34%.
- **What this shows:** checking designs helped the agent a lot, and its answers with the calculator all followed the rules on the first submission. But against the simple rule it had 0 wins, 3 ties and 3 losses, and against the search 2 wins, 2 ties and 2 losses. So with only wall thickness changeable, the AI isn't adding value over simple methods. The proposal expected this could happen (section 4.3).
- **Where it fell short:** on under-extrusion, it mostly tried thickening all the bands, hit the plastic limit, and went back to the original design in 5 of 9 runs. It rarely found the idea of moving plastic between bands.
- **Peak force added:** every fix now also gets a peak-force estimate. The simple rule's under-extrusion fix at 10% reaches 100.3% stiffness but only 98.1% peak force, so stiffness alone can make a fix look better than it is.
- **Limits of these results:** the scores are formula estimates, not simulations or crush tests. The runs used a free model with its long hidden reasoning turned off, because otherwise it can take 15 minutes per request, so the agent scores may understate what a model can do. An earlier run of the no-calculator agent on Gemini, with reasoning on, averaged 2.54% on these 6 cases. Three runs per case is a small sample.
- **Correction to last week:** I said a beam model would let the score see layer shift. It probably wouldn't, because a shifted layer is the same lattice moved sideways.
- **Code prompting paper:** I read the paper your labmate presented, and plan to test writing the prompt as code as a later experiment.
- **Paper draft started:** a LaTeX draft holds the setup, formulas, methods, results and limitations, with tables generated from the run logs.
- **Prompts:** each prompt is saved as a numbered version, and every run records which one it used. We haven't tested prompt changes yet. The two prompts so far differ only in that the calculator agent's also describes its tools. Prompt tests are planned as separate experiments, changing one thing at a time, and the paper now describes this.
- **Proposed next steps:**
  1. Full redesign: let the agent regenerate the unprinted design as a graph of points and walls, with the non-AI search getting the same freedom.
  2. A better judge: a 3D simulation of a small squeeze, plus a check of how much each layer overlaps the one below, to see whether layer shift and warpage really matter. The agent would keep the simple formula as its calculator, so it can't aim directly at the judge. This differs from the proposal, which plans physical tests, so I would still plan a small physical batch near the end.
  3. More defect heights (10% to 90%) and the other two lattice shapes.
  4. Prompt and input-format tests, and more agent roles.
- **Questions:**
  1. Which should come first, the full redesign or the 3D simulation?
  2. Is simulation acceptable for now, with a small physical batch near the end? What would you expect from that batch, and how much of your group's time would it take?
  3. Is it OK to regenerate the design as a graph, with the support rule (new walls must sit on printed walls) plus shape, size and connectivity as constraints?
  4. Is ICML the right target? I'm not sure what the machine-learning contribution would be, or whether a workshop, a manufacturing conference or a journal would fit better. What do you recommend?
  5. If the simulation needs more memory than my laptop has, could you or your advisor sponsor my access to Georgia Tech's PACE computing cluster?
  6. Could you send the documents on prompts you mentioned?
- **Files:** full table at `out/results/e6_table.md`. All changes are on GitHub.

### Short version: sent to Ma about 2026-10-30
- **Key decision: how we judge a fix.** Each fix is scored by how close the finished part's stiffness along Y (the loading axis) comes to a healthy part's: 100% is the target, and both weaker and stiffer count as error. Stiffness is a stand-in for the force response Ma and the proposal care about, chosen because it's the one part of it we can estimate from the geometry before any crush tests.
- Made 12 "stopped print" parts: the print pauses 1 mm after a defect starts (defect at 10%, 50% or 80% of the height, all 4 defect types).
- Built an automatic checker for proposed fixes (wall limits, no printing over air, material budget) and the stiffness score above.
- Tested two non-AI baselines. Keeping the original design leaves under-extrusion at 95.5% of healthy stiffness and over-extrusion at 107%. A simple rule brings most cases back to about 100%, but late defects (80%) can't be fixed within the material budget.
- Built the first AI agent (Gemini). It proposes a fix, the checker judges it, and it retries with the checker's reasons, up to 3 times. First test on one case: allowed on the first try, 98.8% stiffness (simple rule: 100.3%).
- **First full comparison (12 cases, 3 runs each):** the agent always followed the rules but never beat the simple rule (6 ties, 6 losses). Its main mistakes were correcting thickness instead of stiffness (over-extrusion), "fixing" layer shift and warpage that our score can't see, and giving different answers to the same case on different runs (6 of 12 cases).
- **Built agent v1 (not yet run in full):** the agent can now check designs with a calculation tool before submitting (plastic used, a stiffness estimate, rule violations; 10 calls per case). Also built the fair comparison the proposal requires: a non-AI search with the same tool and budget. With 10 calls the search reaches 95.9 to 101.1%; with 200 calls it reaches about 100% almost everywhere. Every fix now also gets a peak-force estimate, which the tool does not report.
- **Next steps (please flag anything that's off before I build it):**
  1. **Done 2026-11-05 (see above).** Run agent v1 on all 12 cases and compare it with v0, the simple rule and the search. Google's free tier (20 requests a day) was too small, so the agents now run through OpenRouter on $10 of prepaid credit, with the same model that answered in the first comparison (gemini-3.6-flash). A full run of v1 costs about $2.50. The main model is now the free Nemotron 3 Ultra, so experiments use no credit.
  1b. **Later, one change at a time:** a prompt written as code (from the code-prompting paper).
  2. **Success measure:** keep stiffness along Y for now, or switch to peak force (or both)? Peak force is as easy to add. A beam model of the walls would also let the score see layer shift.
  3. **Full redesign as a graph (your suggestion):** move from "thickness only" to the agent regenerating the whole unprinted design as a graph (points plus walls). Constraints: outer shape and size, connectivity (nothing floating), and new walls must sit on walls already printed. The checker will need a connectivity check, and the non-AI comparison method must get the same freedom so the comparison stays fair.
  4. **Later:** more defect heights (10% to 90%), the other two lattice shapes, testing prompt and input-format changes (incl. "design as code"), and more agent roles.

### Detailed version

**Goal from the meeting:** make parts that stop printing right after a defect, and build a first framework where an AI agent redesigns the rest of the part.

### Key decisions
- **How we judge a fix (the most important choice this week).**
  - *What:* every method's fix gets the same two checks. First a pass/fail checker (the rules), then a score: the finished part's stiffness along Y as a percentage of a healthy part. The target is 100%. Over 100% also counts as error, because the goal is to recover the original response, not to make the part as strong as possible (proposal, page 1).
  - *Why stiffness:* the proposal's real target is the force–displacement curve (sections 5.2 and 5.3), and your goal was the force along one axis. Without crush tests or a simulation, stiffness (the start of that curve) is the piece we can estimate from the geometry with a standard formula (Gibson & Ashby: stiffness goes with wall thickness cubed). It lets us compare all methods fairly now, before printing anything.
  - *Alternatives considered:* peak force (thickness squared, equally easy to add), a beam model of the walls (sees which walls changed; probably not layer shift unless it links the layers), full simulation (FEA, days of setup), and crush tests on your machine (the real judge, later).
  - *Limits:* it can't see layer shift; it scores stiffness only, not peak force or energy absorbed; and it rewards alternating thick/thin bands more than a real crush test might.
  - *The agent:* the prompt states the goal (match a healthy part's stiffness along Y), but the agent never sees its score, because the true result is unknown mid-print.
- **What the agent can change:** wall thickness only, per 1 mm band above the stop (proposal section 7.1), as a first step toward full regeneration.
- **Material budget:** a fix may use only the plastic the original design would have used above the stop (proposal section 5.4).
- **Agent v1 gets a calculation tool, and the non-AI search gets the same one** (proposal sections 8.1 and 8.5). The tool's stiffness estimate is the same formula as the score for now; the score also reports peak force, which the tool does not, so there is one measure the agent can't aim at directly. A beam model as the judge is planned, so the agent's estimate and the judge differ, as in a real print-and-test setup.

### Done
- **Stopped-print parts.** Each defect starts at a set height, keeps printing for 1 mm (as if a camera noticed it 5 layers later), and the print stops there. 12 cases so far: re-entrant shape, medium severity, defect start at 10%, 50% and 80% of the height, all 4 defect types. All checked: one piece, closed surface, correct height.
- **Fixed axes in the code:** Z = print direction, Y = loading direction, X = layer shift direction.
- **Checker for proposed fixes.** A fix is a list of wall thicknesses, one per 1 mm of height above the stop. Rules: walls 0.8 to 2.0 mm; a wall may grow at most 0.4 mm over the one below it (so it does not print on air); total plastic within the original design's plastic for that height (proposal section 5.4). Returns pass/fail with the reason.
- **Stiffness estimate along Y (first version).** Layers act like springs side by side; each layer's stiffness goes with its wall area cubed (Gibson & Ashby, bending-dominated cells). Printed layers are measured from the STL.
- **Two non-AI baselines:** "keep printing the original design" and a simple correction rule.
- **First AI agent (version 0).** One Gemini model (free tier) in a loop: it gets the case's facts, proposes one wall thickness per remaining 1 mm band, the checker judges it, and rejected answers go back with the reasons (at most 3 attempts, then fall back to the original design; failures still count). The agent sees the checker but not the stiffness score, because the real result is unknown mid-print. The prompt is stored as a versioned file, and every attempt is logged (prompt version, model version, text sent, reply, checker result).
- **Agent v1 (tools), built 2026-11-02:** each turn the agent either calls `evaluate_design` (plastic used vs budget, stiffness estimate, rule violations; 10 calls per case) or submits. Same model, cases, checker, attempts and fallback as v0; the prompt is v1 with the output section replaced by a tool description.
- **Non-AI search (method B):** a standard optimizer (COBYLA) that starts from the original design and may learn about designs only through the same tool and budget. At 10 calls: 95.9 to 101.1%. At 200 calls: about 100% except late under-extrusion (95.9%), which shows how much the number of evaluations matters.
- **Model access moved to OpenRouter** ($10 prepaid credit, gemini-3.6-flash, the version that answered in E5). One-case tests work: v0 98.9% for about $0.02, v1 98.8% for about $0.07 and 84 seconds. In that test v1 used all 10 calculator calls and found an allowed design at 99.8%, but then submitted a different design it had not checked (98.8%).
- **Free-model test (one case, one run):** with agent v1, `nvidia/nemotron-3-ultra-550b-a55b:free` used all 10 calculator calls, narrowed in on the target and submitted a design it had checked: 100.4% stiffness, 97.2% peak force, 82 seconds, $0. With agent v0 it gave no answer within the 3-minute cap (cause not confirmed). `google/gemma-4-31b-it:free` was rate-limited and gave no answer. One run is not enough to judge a model's quality. A second v1 run, after the calculator was corrected to show the real plastic limit, reached 98.5% stiffness and 98.7% peak force.
- **Thinking-off setting:** with its default hidden reasoning, Nemotron did not answer agent v0's task within 9 minutes. With that reasoning turned off, both agents finish on Nemotron. Two-case test: under-extrusion at 10% and over-extrusion at 80%, v0 95.5% and 107.2% (it kept the original design), v1 98.6% and 101.1%.
- **Peak-force estimate** added to the score for every method (strength goes with wall area squared for bending cells). It already exposes the thick/thin trick: the simple rule's under-extrusion fix reaches 100.3% stiffness but 98.1% peak force.
- **First test (one case, under-extrusion at 10%):** allowed on the first attempt, 98.8% stiffness (keeping the original design: 95.5%; simple rule: 100.3%). Without being told, the agent reasoned that stiffness scales with wall thickness cubed. It estimated the material budget slightly wrong, which explains most of the gap to 100%.

### Results so far (stiffness as % of a defect-free part)
| Defect | Keep original design | Simple rule (10% / 50% / 80% start) | AI agent, mean of 3 runs (10% / 50% / 80%) |
|---|---|---|---|
| Under-extrusion | 95.5% | 100.3% / 97.9% / 95.5% | 96.9% / 97.7% / 95.5% |
| Over-extrusion | 107.2% | 100.2% / 99.6% / 100.5% | 101.0% / 101.5% / 102.7% |
| Layer shift | 100.0% | 100.0% (the estimate cannot see layer shift yet) | 100.0% / 101.5% / 100.0% |
| Warpage | 99.5% | 99.5% | 101.7% / 99.5% / 99.5% |

- Later defects leave less height to fix them: at 80%, under-extrusion cannot be recovered without extra plastic.
- The under-extrusion fix uses alternating thinner/thicker bands. This raises bending stiffness, but thin bands may fail first in a real crush test.
- **AI agent:** all 36 answers passed the checker (1 of 37 attempts was rejected once, for material), but it beat the simple rule in none of the 12 cases (6 ties, 6 losses). From its logged reasoning:
  - *Thickness instead of stiffness:* for over-extrusion it subtracted the extra thickness (1.2 - 0.24 = 0.96 mm) instead of cancelling the extra stiffness, so it stayed too stiff (102.7% at 80%; the rule gets 100.5%).
  - *Fixing what the score can't see:* it reasoned that layer shift and warpage weaken the part, which is plausible physically, and added thick/thin bands (up to 106%). Part of this "loss" is the score's blind spot, not only an agent error.
  - *Inconsistent:* 6 of 12 cases gave different answers across the 3 runs (spread up to 6.6 points).
  - *Feedback only checks rules:* the checker tells it when it breaks a rule, not how far it is from 100%, so retries can't help it aim. This follows from the choice not to show it the score.

- **Full comparison on Nemotron with thinking off (E6, 2026-11-05):** average stiffness error / peak-force error: do nothing 3.05% / 2.00%; agent v0 2.76% / 1.84%; agent v1 1.17% / 0.96%; search at 10 uses 1.01% / 0.82%; simple rule 0.79% / 0.90%; search at 200 uses 0.41% / 0.60%. Agent v1 case by case: against v0 4 wins, 8 ties, 0 losses; against the search 2 wins, 8 ties, 2 losses; against the rule 0 wins, 9 ties, 3 losses. Table: `out/results/e6_table.md`. Limit: on Gemini with thinking on, v0 averaged 1.67%, so the calculator's benefit may be smaller than this run suggests.

### Paper
- The living draft is in its own repo, `agentic-redesign-paper`, synced with Overleaf, and it compiled there before the Prompts section was added. That section covers how versions are tracked, which prompt produced which results, the planned prompt experiments, and the exact prompts in an appendix.

### Next
- Improve the agent one change at a time and compare: prompt written as code (code-prompting paper), or a calculation tool for plastic or stiffness (given to the non-AI search method too, to keep the comparison fair).
- Better stiffness estimate (beam model of the walls), so changes to individual walls can be scored. It would probably not see layer shift unless it links the layers. A small crush-test batch would show how much layer shift and warpage really matter.
- Move toward letting the agent regenerate the whole remaining design as a graph (Ma's suggestion).

### Questions for Ma
1. For full regeneration: new walls must still sit on walls already printed (the printer cannot print on air). Is it OK to regenerate the design as a graph with that support rule, plus shape, size and connectivity, as constraints?
2. Is stiffness along Y a reasonable first measure of success, or would you rather we target peak force (or both) from the start?
3. Could you send the documents on prompts you mentioned?
