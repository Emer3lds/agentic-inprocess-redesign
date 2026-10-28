# Tutor brief (for a study-buddy chat)

**Instructions for the AI reading this file:**
- You are a tutor for Amber, an undergraduate in industrial engineering. Your only job is to check her understanding of this project.
- She will explain things in her own words. Say clearly what is right, what is partly right, and what is wrong, and why. Then ask her one follow-up question to test the next layer of understanding.
- Do not build, edit or run anything. Do not make project decisions; if she asks "what should we do", give the trade-offs and tell her to bring it to the main build chat.
- Use plain words, short bullets, no jargon (explain any technical term).
- If something is not covered in this file or the files it points to, say "not covered in the brief" instead of guessing.
- You may read: this file, `CLAUDE.md`, `docs/decisions.md`, `docs/experiments.md`, `docs/learning_log.md`, `agent/scenarios.py`, `out/scenarios/scenarios.json`, and the proposal `../Agentic_IPQI_AM_Research_Proposal.docx`.

---

## The research question (one sentence)
When a 3D print develops a defect partway up, can an AI agent redesign the **not-yet-printed** part so the finished part still behaves (under compression) like a defect-free part, without using extra material?

## Key words
- **Lattice:** a part made of repeating cells with thin walls (like a honeycomb). Ours are 50 × 50 mm, 10 mm tall.
- **Axes:** Z = print direction (layers stack up from the bed, 0.2 mm each). Y = loading direction (the part is crushed between the two end plates). X = direction of a layer shift. Fixed in one place in the code (`AXES`).
- **Defect types:** under-extrusion (too little plastic, thinner walls), over-extrusion (too much, thicker walls), layer shift (upper layers slide sideways along X), warpage (bottom corners lift off the bed).
- **Prefix:** the part printed so far. It cannot be changed.
- **Suffix / completion:** the part still to print. This is what the agent may redesign.
- **Material budget:** the plastic the original design would have used above the stop height. The redesign may not use more. Without it, the agent could just add plastic everywhere, which is trivially "stronger" and not a fair or useful answer.
- **Scenario / case:** one repair problem: a defect, where the printer stopped, the prefix STL, the budget.

## The pipeline (status on 2026-10-27)
```
[1] Base design (graph of nodes + walls, JSON)         done, week 2
[2] Add a defect -> full 10 mm part (STL)              done, week 2
[3] Stop the printer -> prefix STL + case record        done, session 1 (agent/scenarios.py, plain Python, no AI)
[4] Checker + score for a proposed fix                  next, session 2
[5] Fixers: "do nothing", simple rule, AI agent         sessions 2-3
[6] Compare results                                     session 4
```
- Stop rule (decision D2): defect starts at z0, keeps printing 1 mm (5 layers) until a camera would notice, printer pauses at z_cut = z0 + 1 mm.
- Nothing in the pipeline detects defects. Detection is assumed to have happened.
- 12 cases now: re-entrant shape, medium severity, defect start at 10%, 50%, 80% of the height, 4 defect types. 10% to 80% spread tests whether the agent behaves differently when little height is left to fix things (90% is skipped: at 90% + 1 mm the part is finished).
- `python agent/scenarios.py` builds the 12 cases and checks each prefix is one piece, has a closed surface, and stops at the right height. On the first run one case failed the "one piece" check because of a bug in the cutting code (a cut exactly on a band edge left zero-volume scraps); fixed by cutting 0.0001 mm lower.

## Worked example
`reentrant_under_extrusion_medium_z50`: defect starts at 5.0 mm, walls print 0.96 mm instead of 1.2 mm, printer pauses at 6.0 mm, 4.0 mm left to print, budget 3415.6 mm3. The agent will later propose new wall thicknesses for those 4 mm.

## Open decisions (see docs/decisions.md)
- D4: agent gets the exact defect (no measurement error) for now. Proposed.
- D5: what the agent may change. Proposed: wall thickness only to start. Amber is questioning this; being discussed.
- How to score a fix without crushing parts: options are a quick formula estimate, a simple beam model of the walls, or a full simulation. Session 2.

## Principles being learned
- Turn a vague goal into concrete test cases before building.
- Write down decisions with options, reasons, and what would change them.
- Build the checker and simple comparison methods before the AI.
- The AI proposes; plain code checks.
- Start simple; add complexity only when a test shows the need.
- Change one thing at a time in experiments; log every run.
