# Decision log

One entry per real choice. Format: the question, the options, how we judged them, the choice, why, and what would make us change it.
"Status" says who decided: **Amber**, **proposed** (waiting for Amber), or **ask Ma**.

---

## D1. Which AI model to use (2026-10-26)
- **Question:** The agent needs an AI model. There is no funding.
- **Options:** Google Gemini free tier; Groq or OpenRouter free tiers (open models); Claude Code through Amber's Pro plan; a model running on the laptop.
- **Judged on:** cost (free preferred), quality, whether the exact model version can be recorded, speed on Amber's laptop.
- **Choice:** Gemini free tier.
- **Why:** free, no card, good quality, the model name is fixed per request. Free-tier data may be used by Google; fine for lattice geometry.
- **Change if:** free limits are too low for the sweep, or results need a second model to compare against. The code keeps the model swappable (one function), so switching is cheap.
- **Status:** Amber.

## D2. When does the printer stop? (2026-10-26)
- **Question:** Ma asked for parts that print "until the defect and then stop". Where exactly is the cut?
- **Options:** (a) cut where the defect starts; (b) cut where the defect ends; (c) cut after a detection delay.
- **Judged on:** realism. In a real print, a camera or sensor notices a defect only after a few layers, then the printer pauses.
- **Choice:** (c). Defect starts at z0, keeps printing for 1 mm (5 layers), then the printer pauses at z_cut = z0 + 1 mm. Everything below z_cut is fixed.
  - Under/over-extrusion: the 1 mm defect band is exactly the part printed before detection.
  - Layer shift: the 1 mm above the shift is printed shifted; the agent decides what happens after.
  - Warpage: starts at the bed; z0 only sets when the printer is stopped.
- **Change if:** Ma's group knows their real detection delay. The delay is one setting (`DETECT_DELAY`).
- **Status:** Amber ("whatever makes the most sense").

## D3. Start with a small set (2026-10-26)
- **Question:** Ma wants defect heights from 10% to 90% over several designs. That is hundreds of cases.
- **Choice:** first 12 cases: re-entrant shape (the proposal's case), medium severity, defect start at 10%, 50%, 80%, all 4 defect types.
  - 90% is left out: at 90% + 1 mm delay the part is already finished, so nothing can be fixed.
- **Why:** the full sweep only helps once the pipeline works end to end. Small first means fast, cheap debugging.
- **Change if:** the pipeline works on these 12. Then add shapes, severities and the 10% to 80% steps.
- **Status:** Amber (shape choice); set size proposed.

## D4. What the agent is told about the defect (2026-10-26)
- **Question:** In reality, the defect is measured (with error) from a camera. What does the agent see?
- **Options:** (a) the exact answer key (type, size, height); (b) the answer key plus noise; (c) a picture.
- **Choice:** (a) for now.
- **Why:** first test whether the agent can redesign at all when it knows the problem exactly. Measurement error is a separate question to add later; mixing both makes failures impossible to explain.
- **Change if:** the agent works with perfect information. Then try (b).
- **Status:** Amber (2026-10-27).

## D5. What the agent is allowed to change (2026-10-26)
- **Question:** Ma said "change the future shape". How much freedom?
- **Options (as levels):** Level 1: wall thickness only, above the cut. Level 2: plus gradual wall moves (walls slide a little per layer). Level 3: plus new walls. Also possible but not geometry: printer settings (flow, speed).
- **Hard limit from physics:** the printer cannot put plastic on thin air. Every wall in the first new layer must sit on a wall already printed, and walls can only move a little per layer. So "free" redesign really means gradual change from the existing walls.
- **Judged on:** can it be printed on top of the fixed part; can our checker verify it; can a simple (non-AI) method use the same options, so the comparison is fair; build time.
- **Choice:** Level 1 to start. Code written so levels 2 and 3 can be added.
- **Why:** easy to undo, matches section 7.1 of the proposal, quickest to check, fewest invalid proposals.
- **Change if:** Ma wants shape changes, or thickness cannot fix a defect (likely for layer shift: thickness cannot realign shifted walls, so Level 2 is the probable next step).
- **Status:** Amber (2026-10-27).
- **Ma's answer (message, 2026-10-28):** "I feel like all. Think about how do you currently represent it, the design, like a graph? Image? And then let agent completely regenerate. Giving some constraints like the overall shape, size, etc. Connectivity."
  - This goes past Level 3: the agent outputs a whole new design for the part above the stop height. We already store designs as graphs (nodes + walls with thickness), so the agent could output a new graph.
  - Differs from the proposal (sec. 7.1 starts with thickness only; sec. 4.3 and 7.3 say a shape-editing agent must be compared with a non-AI method that has the same operations).
  - Missing from Ma's constraint list: **support**. New walls in the first new layer must sit on printed walls. Raise with Ma.
  - **Next:** revisit D5 after the Thursday update. Level 1 stays as the working version for now.

## D6. One axis convention (2026-10-26)
- **Choice:** Z = print direction (layers stack up from the bed), Y = loading direction (crush between the end plates), X = layer shift direction. Stored once as `AXES` in `agent/scenarios.py` and written into every scenario.
- **Why:** Ma asked that the loading axis never switch between X and Y.
- **Status:** fixed (Ma).

---

## D7. Checker rules (2026-10-28)
- **Rules:** only bands above the stop height change; wall thickness 0.8 to 2.0 mm (2 nozzle lines; cells stay open); a wall may grow at most 0.4 mm from one band to the next, including from the printed top layer (0.2 mm per side, so it does not hang over air); material within budget + 1%; end plates unchanged.
- **Budget question:** may a repair spend plastic the defect "saved"?
  - Proposal, section 5.4: no. "Missing material already printed does not automatically increase the permitted future budget."
  - Options: (a) "remaining": the plastic the original design would use above the cut (proposal); (b) "total": the finished part may use as much plastic as a healthy part. Under-extrusion then gets extra, over-extrusion gets less.
  - **Choice:** (a), the proposal's rule (Amber, 2026-10-28, changed from (b) the same day). Both values are still stored for every case; switching is one setting (`BUDGET_MODE` in `agent/evaluate.py`).
  - **Consequence:** under (a), an under-extruded part can only get stiffer by moving plastic around (thicker in some bands, thinner in others), not by adding plastic.
- **Status:** Amber.

## D8. How to score a fix, version 1 (2026-10-28)
- **Options:** formula estimate; beam model of the walls; full simulation (FEA).
- **Choice:** formula now; beam model next.
- **How:** layers act like springs side by side, so part stiffness = average layer stiffness. Layer stiffness = (lattice area / healthy lattice area) to the power 3 for bending shapes (re-entrant, hexagon), power 1 for the triangle (Gibson & Ashby). Printed layers are measured by slicing the STL, not read from the defect label.
- **Target:** 100% of a healthy part. Over 100% also counts as error (the goal is to match, not to maximize).
- **Known blind spots:** cannot see layer shift or layer bonding; stiffness only, not peak force; thick-thin stacks score higher than they should (Goodhart's law; partly limited by the 0.8 mm minimum).
- **Change if:** the beam model is ready, or crush tests disagree with the formula.
- **Status:** Amber.

## D9. Agent version 0 setup (2026-10-29)
- **A. What the agent sees:** the checker's feedback only, not the score. Reason: during a real print the true result (the crush test) does not exist yet (proposal 8.2), and with the exact score the AI could just try numbers, which a non-AI search (method B) does cheaper. Later: a `predict_from_history` tool with uncertainty (proposal 8.1), given to method B too.
- **B. Stiffness formula in the prompt:** no for v1. Adding it in v2 is a clean "change one thing" experiment.
- **C. Attempts:** at most 3, then fall back to "do nothing" (proposal 7.3). Fallbacks count as failures in the results.
- **Model:** Gemini free tier, `gemini-3.5-flash` requested by its pinned name. Every attempt logs the version Google reports back (see E4: it reported `gemini-3.6-flash`).
- **Prompt:** `agent/prompts/v1.md`, drafted by Amber, revised together. Versions are never edited once used.
- **Status:** Amber.

## D10. Agent v1: a calculation tool, a matched non-AI search, and a second measure (2026-11-02)
- **Why:** E5 showed the agent can't aim: the checker only reports broken rules, so it estimated plastic and stiffness in its head and missed. The proposal's agent uses deterministic tools before submitting (sections 2.3, 8.1).
- **A. Tool:** `evaluate_design` returns plastic used and budget, a stiffness *estimate*, and rule violations (option b; Amber). The stiffness estimate is the same formula as the score for now, which is a known weakness: the score's other measures (peak force; later the beam model) are not reported by the tool.
- **B. Budget:** 10 tool calls per case, plus up to 3 submissions (Amber).
- **C. Method B (non-AI search):** built now with the same tool and budget (proposal 8.5). COBYLA from scipy, starting from the original design. Also run at 200 calls to show what search can do with many evaluations (Amber).
- **D. Second measure:** peak force reported for every fix: same layers-in-parallel idea, strength goes with relative area squared for bending shapes (Gibson & Ashby). Beam model later, as its own session (Amber).
- **Change if:** the tool's estimate and the judge are made different (beam model or crush tests), or Ma prefers another measure.
- **Status:** Amber.

---

# Ideas for later (not decided)

## I1. Let the agent decide: continue, repair, or restart (Amber, 2026-10-27)
- **Idea:** instead of always repairing, the agent chooses between (a) keep printing the original design, (b) repair the rest of the part, (c) throw it out and restart.
- **What it needs first:** a way to estimate how well a repair would work (the score from session 2), and the cost of each choice (print time already spent, material, chance the repair works).
- **Two separate questions:** which defects and heights *can* be recovered is something our experiments will show. Whether a repair is *worth it* for a given part is the per-case decision the agent could make.
