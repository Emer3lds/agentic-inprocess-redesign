# Progress summary

Running summary of the work, one section per week, written to send to Ma. Each week has a short version (a few lines to paste into a message) and a detailed version.

---

## Week 3 (meeting 2026-10-22; next meeting about 2026-11-09)

### Short version
- **Key decision: how we judge a fix.** Each fix is scored by how close the finished part's stiffness along Y (the loading axis) comes to a healthy part's: 100% is the target, and both weaker and stiffer count as error. Stiffness is a stand-in for the force response Ma and the proposal care about, chosen because it's the one part of it we can estimate from the geometry before any crush tests.
- Made 12 "stopped print" parts: the print pauses 1 mm after a defect starts (defect at 10%, 50% or 80% of the height, all 4 defect types).
- Built an automatic checker for proposed fixes (wall limits, no printing over air, material budget) and the stiffness score above.
- Tested two non-AI baselines. Keeping the original design leaves under-extrusion at 95.5% of healthy stiffness and over-extrusion at 107%. A simple rule brings most cases back to about 100%, but late defects (80%) can't be fixed within the material budget.
- Built the first AI agent (Gemini). It proposes a fix, the checker judges it, and it retries with the checker's reasons, up to 3 times. First test on one case: allowed on the first try, 98.8% stiffness (simple rule: 100.3%).
- **Next steps (please flag anything that's off before I build it):**
  1. **Finish the first comparison:** run the agent on all 12 cases, 3 times each, against both baselines.
  2. **Success measure:** keep stiffness along Y for now, or switch to peak force (or both)? Peak force is as easy to add. A beam model of the walls would also let the score see layer shift.
  3. **Full redesign as a graph (your suggestion):** move from "thickness only" to the agent regenerating the whole unprinted design as a graph (points plus walls). Constraints: outer shape and size, connectivity (nothing floating), and new walls must sit on walls already printed. The checker will need a connectivity check, and the non-AI comparison method must get the same freedom so the comparison stays fair.
  4. **Later:** more defect heights (10% to 90%), the other two lattice shapes, testing prompt and input-format changes (incl. "design as code"), and more agent roles.

### Detailed version

**Goal from the meeting:** make parts that stop printing right after a defect, and build a first framework where an AI agent redesigns the rest of the part.

### Key decisions
- **How we judge a fix (the most important choice this week).**
  - *What:* every method's fix gets the same two checks. First a pass/fail checker (the rules), then a score: the finished part's stiffness along Y as a percentage of a healthy part. The target is 100%. Over 100% also counts as error, because the goal is to recover the original response, not to make the part as strong as possible (proposal, page 1).
  - *Why stiffness:* the proposal's real target is the force–displacement curve (sections 5.2 and 5.3), and your goal was the force along one axis. Without crush tests or a simulation, stiffness (the start of that curve) is the piece we can estimate from the geometry with a standard formula (Gibson & Ashby: stiffness goes with wall thickness cubed). It lets us compare all methods fairly now, before printing anything.
  - *Alternatives considered:* peak force (thickness squared, equally easy to add), a beam model of the walls (can see layer shift), full simulation (FEA, days of setup), and crush tests on your machine (the real judge, later).
  - *Limits:* it can't see layer shift; it scores stiffness only, not peak force or energy absorbed; and it rewards alternating thick/thin bands more than a real crush test might.
  - *The agent:* the prompt states the goal (match a healthy part's stiffness along Y), but the agent never sees its score, because the true result is unknown mid-print.
- **What the agent can change:** wall thickness only, per 1 mm band above the stop (proposal section 7.1), as a first step toward full regeneration.
- **Material budget:** a fix may use only the plastic the original design would have used above the stop (proposal section 5.4).

### Done
- **Stopped-print parts.** Each defect starts at a set height, keeps printing for 1 mm (as if a camera noticed it 5 layers later), and the print stops there. 12 cases so far: re-entrant shape, medium severity, defect start at 10%, 50% and 80% of the height, all 4 defect types. All checked: one piece, closed surface, correct height.
- **Fixed axes in the code:** Z = print direction, Y = loading direction, X = layer shift direction.
- **Checker for proposed fixes.** A fix is a list of wall thicknesses, one per 1 mm of height above the stop. Rules: walls 0.8 to 2.0 mm; a wall may grow at most 0.4 mm over the one below it (so it does not print on air); total plastic within the original design's plastic for that height (proposal section 5.4). Returns pass/fail with the reason.
- **Stiffness estimate along Y (first version).** Layers act like springs side by side; each layer's stiffness goes with its wall area cubed (Gibson & Ashby, bending-dominated cells). Printed layers are measured from the STL.
- **Two non-AI baselines:** "keep printing the original design" and a simple correction rule.
- **First AI agent (version 0).** One Gemini model (free tier) in a loop: it gets the case's facts, proposes one wall thickness per remaining 1 mm band, the checker judges it, and rejected answers go back with the reasons (at most 3 attempts, then fall back to the original design; failures still count). The agent sees the checker but not the stiffness score, because the real result is unknown mid-print. The prompt is stored as a versioned file, and every attempt is logged (prompt version, model version, text sent, reply, checker result).
- **First test (one case, under-extrusion at 10%):** allowed on the first attempt, 98.8% stiffness (keeping the original design: 95.5%; simple rule: 100.3%). Without being told, the agent reasoned that stiffness scales with wall thickness cubed. It estimated the material budget slightly wrong, which explains most of the gap to 100%.

### Results so far (stiffness as % of a defect-free part)
| Defect | Keep original design | Simple rule (10% / 50% / 80% start) |
|---|---|---|
| Under-extrusion | 95.5% | 100.3% / 97.9% / 95.5% |
| Over-extrusion | 107.2% | 100.2% / 99.6% / 100.5% |
| Layer shift | 100.0% | 100.0% (the estimate cannot see layer shift yet) |
| Warpage | 99.5% | 99.5% |

- Later defects leave less height to fix them: at 80%, under-extrusion cannot be recovered without extra plastic.
- The under-extrusion fix uses alternating thinner/thicker bands. This raises bending stiffness, but thin bands may fail first in a real crush test.

### Next
- Run the agent on all 12 cases, 3 times each (answers vary), and compare it with the two baselines.
- Better stiffness estimate (beam model of the walls), so layer shift and changes to individual walls can be scored.
- Move toward letting the agent regenerate the whole remaining design as a graph (Ma's suggestion).

### Questions for Ma
1. For full regeneration: new walls must still sit on walls already printed (the printer cannot print on air). Is it OK to regenerate the design as a graph with that support rule, plus shape, size and connectivity, as constraints?
2. Is stiffness along Y a reasonable first measure of success, or would you rather we target peak force (or both) from the start?
3. Could you send the name of the "design as code" paper your labmate presented, and the documents on prompts you mentioned?
