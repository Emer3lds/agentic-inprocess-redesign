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
- **Status:** Amber (2026-10-27); **ask Ma** what "change the future shape" meant in the Thursday update.

## D6. One axis convention (2026-10-26)
- **Choice:** Z = print direction (layers stack up from the bed), Y = loading direction (crush between the end plates), X = layer shift direction. Stored once as `AXES` in `agent/scenarios.py` and written into every scenario.
- **Why:** Ma asked that the loading axis never switch between X and Y.
- **Status:** fixed (Ma).

---

# Ideas for later (not decided)

## I1. Let the agent decide: continue, repair, or restart (Amber, 2026-10-27)
- **Idea:** instead of always repairing, the agent chooses between (a) keep printing the original design, (b) repair the rest of the part, (c) throw it out and restart.
- **What it needs first:** a way to estimate how well a repair would work (the score from session 2), and the cost of each choice (print time already spent, material, chance the repair works).
- **Two separate questions:** which defects and heights *can* be recovered is something our experiments will show. Whether a repair is *worth it* for a given part is the per-case decision the agent could make.
