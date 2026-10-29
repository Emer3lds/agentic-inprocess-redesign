# Progress summary

Running summary of the work, one section per week, written to send to Ma.

---

## Week 3 (meeting 2026-10-22; next meeting about 2026-11-09)

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

### Next
- First single AI agent (Gemini), checked by the same checker, compared against the two baselines.
- Better stiffness estimate (beam model of the walls), so layer shift and changes to individual walls can be scored.
- Move toward letting the agent regenerate the whole remaining design as a graph (Ma's suggestion).

### Questions for Ma
1. For full regeneration: new walls must still sit on walls already printed (the printer cannot print on air). Is it OK to regenerate the design as a graph with that support rule, plus shape, size and connectivity, as constraints?
2. Could you send the name of the "design as code" paper your labmate presented, and the documents on prompts you mentioned?
