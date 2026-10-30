# Progress summary

Running summary of the work, one section per week, written to send to Ma. Each week has a short version (a few lines to paste into a message) and a detailed version.

---

## Week 3 (meeting 2026-10-22; next meeting about 2026-11-09)

### Short version
- Made 12 "stopped print" parts: the print pauses 1 mm after a defect starts (defect at 10%, 50% or 80% of the height, all 4 defect types).
- Built an automatic checker for proposed fixes and a first stiffness estimate along Y (the loading axis).
- Tested two non-AI baselines. Keeping the original design leaves under-extrusion at 95.5% of healthy stiffness and over-extrusion at 107%. A simple rule brings most cases back to about 100%, but late defects (80%) can't be fixed within the material budget.
- Built the first AI agent (Gemini). It proposes a fix, the checker judges it, and it retries with the checker's reasons, up to 3 times. First test on one case: allowed on the first try, 98.8% stiffness (simple rule: 100.3%).
- Next: run the agent on all 12 cases, 3 times each, and compare it with the baselines.

### Detailed version

**Goal from the meeting:** make parts that stop printing right after a defect, and build a first framework where an AI agent redesigns the rest of the part.

### Done
- **Stopped-print parts.** Each defect starts at a set height, keeps printing for 1 mm (as if a camera noticed it 5 layers later), and the print stops there. 12 cases so far: re-entrant shape, medium severity, defect start at 10%, 50% and 80% of the height, all 4 defect types. All checked: one piece, closed surface, correct height.
- **Fixed axes in the code:** Z = print direction, Y = loading direction, X = layer shift direction.
- **Checker for proposed fixes.** A fix is a list of wall thicknesses, one per 1 mm of height above the stop. Rules: walls 0.8 to 2.0 mm; a wall may grow at most 0.4 mm over the one below it (so it does not print on air); total plastic within the original design's plastic for that height (proposal section 5.4). Returns pass/fail with the reason.
- **Stiffness estimate along Y (first version).** Layers act like springs side by side; each layer's stiffness goes with its wall area cubed (Gibson & Ashby, bending-dominated cells). Printed layers are measured from the STL.
- **Two non-AI baselines:** "keep printing the original design" and a simple correction rule.

### Results so far (stiffness as % of a defect-free part)
| Defect | Keep original design | Simple rule (10% / 50% / 80% start) |
|---|---|---|
| Under-extrusion | 95.5% | 100.3% / 97.9% / 95.5% |
| Over-extrusion | 107.2% | 100.2% / 99.6% / 100.5% |
| Layer shift | 100.0% | 100.0% (the estimate cannot see layer shift yet) |
| Warpage | 99.5% | 99.5% |

- Later defects leave less height to fix them: at 80%, under-extrusion cannot be recovered without extra plastic.
- The under-extrusion fix uses alternating thinner/thicker bands. This raises bending stiffness, but thin bands may fail first in a real crush test.

- **First AI agent (version 0).** One Gemini model (free tier) in a loop: it gets the case's facts, proposes one wall thickness per remaining 1 mm band, the checker judges it, and rejected answers go back with the reasons (at most 3 attempts, then fall back to the original design; failures still count). The agent sees the checker but not the stiffness score, because the real result is unknown mid-print. The prompt is stored as a versioned file, and every attempt is logged (prompt version, model version, text sent, reply, checker result).
- **First test (one case, under-extrusion at 10%):** allowed on the first attempt, 98.8% stiffness (keeping the original design: 95.5%; simple rule: 100.3%). Without being told, the agent reasoned that stiffness scales with wall thickness cubed. It estimated the material budget slightly wrong, which explains most of the gap to 100%.

### Next
- Run the agent on all 12 cases, 3 times each (answers vary), and compare it with the two baselines.
- Better stiffness estimate (beam model of the walls), so layer shift and changes to individual walls can be scored.
- Move toward letting the agent regenerate the whole remaining design as a graph (Ma's suggestion).

### Questions for Ma
1. For full regeneration: new walls must still sit on walls already printed (the printer cannot print on air). Is it OK to regenerate the design as a graph with that support rule, plus shape, size and connectivity, as constraints?
2. Could you send the name of the "design as code" paper your labmate presented, and the documents on prompts you mentioned?
