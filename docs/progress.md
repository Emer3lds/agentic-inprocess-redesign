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
- **First full comparison (12 cases, 3 runs each):** the agent always followed the rules but never beat the simple rule (6 ties, 6 losses). Its main mistakes were correcting thickness instead of stiffness (over-extrusion), "fixing" layer shift and warpage that our score can't see, and giving different answers to the same case on different runs (6 of 12 cases).
- **Built agent v1 (not yet run in full):** the agent can now check designs with a calculation tool before submitting (plastic used, a stiffness estimate, rule violations; 10 calls per case). Also built the fair comparison the proposal requires: a non-AI search with the same tool and budget. With 10 calls the search reaches 95.9 to 101.1%; with 200 calls it reaches about 100% almost everywhere. Every fix now also gets a peak-force estimate, which the tool does not report.
- **Next steps (please flag anything that's off before I build it):**
  1. **Run agent v1 on all 12 cases** and compare it with v0, the simple rule and the search. The free Gemini tier allows 20 requests a day, so this needs a different free model, a few cents of paid use, or several days.
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
  - *Alternatives considered:* peak force (thickness squared, equally easy to add), a beam model of the walls (can see layer shift), full simulation (FEA, days of setup), and crush tests on your machine (the real judge, later).
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

### Next
- Run agent v1 in full (blocked by the free tier's 20 requests a day), then improve the agent one change at a time and compare: prompt written as code (code-prompting paper), or a calculation tool for plastic or stiffness (given to the non-AI search method too, to keep the comparison fair).
- Better stiffness estimate (beam model of the walls), so layer shift and changes to individual walls can be scored.
- Move toward letting the agent regenerate the whole remaining design as a graph (Ma's suggestion).

### Questions for Ma
1. For full regeneration: new walls must still sit on walls already printed (the printer cannot print on air). Is it OK to regenerate the design as a graph with that support rule, plus shape, size and connectivity, as constraints?
2. Is stiffness along Y a reasonable first measure of success, or would you rather we target peak force (or both) from the start?
3. Is "Code Prompting Elicits Conditional Reasoning Abilities in Text+Code LLMs" (Puerto et al., 2024) the paper your labmate presented? Could you also send the documents on prompts you mentioned?
