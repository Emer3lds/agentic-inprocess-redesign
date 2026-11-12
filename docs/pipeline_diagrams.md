# Pipeline diagrams

## Quick reminder of terms

- **Case:** one test problem, such as a part with under-extrusion that paused at 2 mm.
- **Fix:** a list of wall thicknesses for the part left to print, one per 1 mm of height.
- **Checker:** our code that tests whether a fix follows the rules. No AI.
- **Score:** our formulas estimating the finished part's stiffness and peak force, as a % of a healthy part. No AI.
- **Do nothing (N):** keep printing the original design.
- **Simple rule (R):** a fixed recipe we wrote that cancels the stiffness the defect added or removed. No AI.
- **A0 (agent v0):** the AI, with no calculator.
- **A1 (agent v1):** the AI, with up to 10 calculator uses.
- **Calculator (`evaluate_design`):** reports a design's plastic use, estimated stiffness and rule problems.
- **10-call search (B):** our math program, with no AI, that tries designs using the same calculator, up to 10 times.
- **E0, E1, ...:** our numbered experiments.
- **Thinking off:** a model setting that skips the AI's long hidden reasoning.

## Start here: the four questions for every step

For each step: what do we have before it, what does it change, what do we have after it, and is it the AI or plain code? Example case: under-extrusion starting at 10% of the height.

### The building blocks

| Step | Before | What it changes | After | AI or code |
|---|---|---|---|---|
| **Build one case** | The healthy design, plus a defect type and start height | Builds the part with the defect and removes everything above the pause height (2.0 mm) | A 3D file of the printed part, and the facts of the case (8 mm left, budget 6831 mm³) | Code |
| **Propose a fix** | The facts of a case | Chooses a wall thickness for each remaining 1 mm band; the method varies (see below) | A list of 8 thicknesses | Depends on the method |
| **Check the fix** | One list of thicknesses | Nothing; it tests the rules (0.8 to 2.0 mm, at most 0.4 mm thicker than the band below, plastic within budget + 1%) | Allowed, or rejected with reasons | Code |
| **Score the fix** | The printed part plus the list of thicknesses | Nothing; it estimates the finished part with formulas | Stiffness % and peak force % of a healthy part | Code |
| **Compare** | Results of all methods, per case | Lines the methods up | A table, and wins, ties and losses | Code |

### The methods that propose a fix

| Method | What it gets | How it decides | AI or code |
|---|---|---|---|
| **N: do nothing** | The original design | Keeps 1.2 mm in every band | Code |
| **R: simple rule v2** | The printed part's measured stiffness gap | Follows a fixed recipe to cancel the gap | Code |
| **A0: agent v0** | The facts of the case in a prompt | Reasons and answers; hears back only if it broke a rule (3 tries) | AI, with code checking it |
| **A1: agent v1** | The same, plus a calculator it can use 10 times | Tries designs, reads the numbers, then submits | AI, with code checking it |
| **B: search** | The same calculator, with the same 10 uses | An optimizer tries designs and keeps the best allowed one | Code |

### The experiments

| Experiment | Before | What we changed | What came out | AI or code |
|---|---|---|---|---|
| **E0** | Healthy designs and defect definitions | Built the first test set | 12 cases, all pass the part checks | Code |
| **E1** | The 12 cases, with no repair | Tried "do nothing" | Under-extrusion 95.5%, over-extrusion 107.2%, warpage 99.5%; layer shift 100.0%, because the score can't see it | Code |
| **E2** | E1's damage numbers | Tried simple rule v1 (correct every remaining band by the lost thickness) | It overcorrects; under-extrusion breaks the rules | Code |
| **E3** | E2's failure | Rule v2 (correct the lost stiffness instead) | About 100% in most cases, except late under-extrusion. This is the bar to beat | Code |
| **E4** | The bar from E3 | Added the AI, on one case, to test that the code runs | It runs: 98.8% | AI |
| **E5** | E4's working loop | Ran all 12 cases, 3 times each | 0 wins, 6 ties, 6 losses against the rule; answers vary between runs | AI |
| **E6** | E5's finding that the agent can't tell how close it is | Adds the calculator, and compares with search B | See `docs/progress.md` (agent v1 beat v0, did not beat the rule) | AI, plus code for B |
| **E7 (trust checks for the beam model)** | The 12 cases and the formula score | Scores the same fixes with the new beam model (diagram 8) and compares it with the textbook formula on healthy parts | Not known yet | Code |

---

One diagram per stage of the pipeline and per agent version, naming the real functions (file → function) and what goes in and comes out, with real example values. These are for reference when debugging or changing the code. A new diagram is added for every new agent version or experiment setup, and old ones are kept, so each experiment's setup can always be looked up.

The diagrams are written in Mermaid. GitHub shows them as pictures. In VS Code, install the extension "Markdown Preview Mermaid Support" and open the Markdown preview (Ctrl+Shift+V).

**How to read them:**
- Rounded boxes are **functions** (`file.py → function()`), with one line on what they do.
- Slanted boxes are **files or data** going in or out.
- Purple boxes are where the **AI model** is called. Teal boxes are **tools** the AI can call. Everything else is plain Python.
- The words on an arrow say what is passed along it.

Example case used throughout: `reentrant_under_extrusion_medium_z10` (under-extrusion from 1.0 to 2.0 mm, printer paused at 2.0 mm, 8 bands of 1 mm left to print).

| # | Diagram | Used by experiments |
|---|---|---|
| 1 | Building the repair cases | E0 |
| 2 | The judge (checker and score) | every experiment |
| 3 | Baselines N and R | E1, E2, E3 |
| 4 | Agent v0 (A0) | E4, E5 |
| 5 | Agent v1 (A1) | E6 |
| 6 | Non-AI search (B) | E6 |
| 7 | Comparing results | E5, E6 |
| 8 | Beam model of the walls (fast FEA calculator) | E7 |

---

## 1. Building the repair cases (E0)
Run: `python agent/scenarios.py` (plain Python, about 9 s). Builds each defective part, cuts it where the printer would pause, and writes down the facts of each case.

```mermaid
flowchart TD
    G[/"out/base/reentrant_graph.json<br>points + walls, 1.2 mm thick"/] --> LG("lattice.py → load_graph()<br>reads the design")
    LG -->|design graph| MS("scenarios.py → make_scenario()<br>one case: shape, defect, start height")
    MS -->|"defect type, severity, start z0 = 1.0 mm"| INJ("defects.py → inject()<br>builds the full 10 mm part with the defect")
    INJ -->|"full defective part (mesh)"| CUT("scenarios.py → cut_below()<br>keeps only what is printed below the pause, z ≤ 2.0 mm")
    CUT -->|"printed part (prefix)"| CHK("lattice.py → check_mesh()<br>one piece? closed surface? right height?")
    CHK --> OUT1[/"out/scenarios/reentrant/..._z10_prefix.stl"/]
    MS --> OUT2[/"out/scenarios/scenarios.json<br>z_cut 2.0, remaining 8.0 mm, budget 6831.2 mm³, axes"/]
```

---

## 2. The judge: checker, then score (every experiment)
File: `agent/evaluate.py`. Every method's fix goes through these same functions. A fix is always `{"wall_thickness_mm": [one number per remaining 1 mm band]}`.

```mermaid
flowchart TD
    J[/"scenarios.json + prefix STL"/] --> LC("load_cases()<br>makes one Case per record")
    LC --> CASE("Case(...)<br>slices the printed part into 0.2 mm layers<br>and measures each layer's wall area")
    FIX[/"a fix, e.g. [1.36, 1.58, 1.11, 1.11, 1.11, 1.11, 1.11, 1.11]"/] --> CHECK
    CASE --> CHECK("check(case, fix)<br>format · thickness 0.8–2.0 mm · overhang ≤ 0.4 mm · material ≤ budget + 1%")
    CHECK -->|"list of violations, empty = allowed"| SCORE
    CASE --> SCORE("score(case, fix)<br>uses layer_area_ratios() and material_used()")
    SCORE --> RES[/"stiffness_ratio 0.988 · peak_force_ratio · error · material_mm3"/]
```

- `layer_area_ratios(case, fix)`: wall area of every 0.2 mm layer (the printed ones, then the proposed ones) divided by a healthy layer's.
- Stiffness = average of (ratio³). Peak force = average of (ratio²). Both are relative to a healthy part, so 1.0 = 100%.
- `material_used(case, fix)`: plastic in the proposed bands, in mm³.

---

## 3. Baselines N (do nothing) and R (simple rule) (E1, E2, E3)
Run: `python agent/baselines.py` (plain Python, about 9 s). No AI.

```mermaid
flowchart TD
    LC("evaluate.py → load_cases()") -->|each Case| DN("baselines.py → do_nothing(case)<br>original design: 1.2 mm in every band")
    LC -->|each Case| SR("baselines.py → simple_rule(case)<br>rule v2: fix the lost stiffness")
    SR --> GAP("stiffness_gap(case)<br>how much stiffness the printed part is missing")
    SR --> BS("band_stiffness(case, t)<br>stiffness of one band at thickness t")
    DN -->|"[1.2 × 8]"| JUDGE("evaluate.py → check() and score()")
    SR -->|"[1.0, 1.4, 1.0, 1.4, 1.0, 1.4, 1.0, 1.4]"| JUDGE
    JUDGE --> OUT[/"out/results/baselines.json<br>do nothing 95.5% · rule 100.3%"/]
```

---

## 4. Agent v0, A0 (E4, E5)
Run: `python agent/agent_v0.py --runs 3 --experiment e5_v1_full` (uses the AI). File: `agent/agent_v0.py`.

```mermaid
flowchart TD
    MAIN("main()<br>loops over cases and runs, resumes, writes the log") -->|each Case| RA("run_agent(case)")
    RA --> LP("load_prompt('v1')<br>reads prompts/v1.md and v1_retry.md")
    RA --> SL("slots_for(case)<br>the case facts: z_cut 2.0, top wall 0.96, 8 bands, ...")
    LP --> FILL("fill(template, slots)<br>puts the facts into the prompt text")
    SL --> FILL
    FILL -->|prompt text| CHAT("llm.chat(messages)<br>sends the conversation to the model, asks for JSON")
    CHAT:::ai -->|"JSON text: reasoning + wall_thickness_mm"| PARSE("parse(text)<br>reads the JSON")
    PARSE -->|fix| CHECK("evaluate.py → check(case, fix)")
    CHECK -->|"rejected: violations (at most 3 attempts)"| RETRY("fill(retry template, violations)<br>'The checker rejected your proposal for these reasons: ...'")
    RETRY -->|added to the conversation| CHAT
    CHECK -->|allowed| SCORE("evaluate.py → score(case, fix)")
    CHECK -->|"3 rejections"| FB("baselines.py → do_nothing(case)<br>fallback")
    FB --> SCORE
    SCORE --> LOG[/"out/runs/e5_v1_full.jsonl<br>one line per run: every attempt, reply, violations, score"/]
    classDef ai fill:#EEEDFE,stroke:#534AB7,color:#3C3489
```

Example from E5: allowed on the first attempt in 35 of 36 runs. Mean result 0 wins, 6 ties, 6 losses against the simple rule.

---

## 5. Agent v1, A1 (E6)
Run: `python agent/agent_v1.py --runs 3 --experiment e6_v1_nemotron` (uses the AI, free Nemotron with thinking off). File: `agent/agent_v1.py`; the tool is in `agent/tools.py`.

```mermaid
flowchart TD
    MAIN("agent_v0.py → main(run_agent_v1)<br>same loop, resume and logging as v0") -->|each Case| RA("run_agent_v1(case)")
    RA --> FILL("fill(prompts/v2_tools.md, slots_for(case))<br>v1 text + description of the two tools")
    FILL -->|"prompt + tool definitions (TOOL_DECLS)"| STEP("llm.step(contents, tools)<br>one turn: the model either calls a tool or submits")
    STEP:::ai -->|"evaluate_design([1.36, 1.36, 1.36, 1.2, ...])"| EV("tools.py → Toolbox.evaluate_design()<br>runs check(), material_used(), layer_area_ratios()<br>at most 10 calls")
    EV:::tool -->|"material 6887.4 / limit 6899.5 · stiffness 99.82% · violations [] · calls left 7"| STEP
    STEP -->|"submit_fix(wall_thickness_mm, reasoning)"| CHECK("evaluate.py → check(case, fix)")
    CHECK -->|"rejected: violations (at most 3 submissions)"| STEP
    CHECK -->|accepted| SCORE("evaluate.py → score(case, fix)<br>stiffness and peak force; peak force is never shown to the agent")
    CHECK -->|"3 rejections or 16 turns"| FB("baselines.py → do_nothing(case)<br>fallback") --> SCORE
    SCORE --> LOG[/"out/runs/e6_v1_nemotron.jsonl<br>every turn, every tool call and result, submissions, score, cost"/]
    classDef ai fill:#EEEDFE,stroke:#534AB7,color:#3C3489
    classDef tool fill:#E1F5EE,stroke:#0F6E56,color:#085041
```

Example from the one-case test (`out/runs/smoke_or_v1.jsonl`): 10 tool calls, best allowed design tried was 99.8%, but it submitted an unchecked design that scored 98.8%. That test showed the budget without the checker's +1%, so 6887.4 mm³ looked over budget although it was allowed. The tool now reports the real limit (6899.5 mm³).

---

## 6. Non-AI search, B (E6)
Run: `python agent/search.py` (plain Python, about 40 s). File: `agent/search.py`.

```mermaid
flowchart TD
    LC("evaluate.py → load_cases()") -->|each Case| S("search(case, budget)<br>budget = 10 (same as the agent) and 200")
    S -->|"start: do_nothing(case) = [1.2 × 8]"| OPT("scipy COBYLA → minimize()<br>tries designs, aims for stiffness 100%")
    OPT -->|a design to try| EVX("ev(x)<br>remembers designs already tried")
    EVX --> EV("tools.py → Toolbox.evaluate_design()<br>the same tool the agent uses")
    EV:::tool -->|"stiffness estimate, material, violations"| OPT
    OPT -->|"budget used up"| BEST("pick the best allowed design it tried")
    BEST --> JUDGE("evaluate.py → check() and score()")
    JUDGE --> OUT[/"out/results/search.json<br>10 calls: 97.9% · 200 calls: 100.0%"/]
    classDef tool fill:#E1F5EE,stroke:#0F6E56,color:#085041
```

The rules the prompt states in words (thickness range, overhang) the search checks itself with `overhang_margins(x)` and simple limits, just as the agent can read them in its prompt.

---

## 7. Comparing results (E5, E6)
Run: `python agent/compare.py out/runs/<experiment>.jsonl` (plain Python, instant).

```mermaid
flowchart LR
    RUNS[/"out/runs/&lt;experiment&gt;.jsonl<br>agent runs"/] --> CMP("compare.py<br>per case: mean of the runs,<br>spread, win / tie / loss")
    BASE[/"out/results/baselines.json<br>N and R"/] --> CMP
    SR[/"out/results/search.json<br>B at 10 calls"/] --> CMP
    CMP --> TABLE[/"table printed per case<br>+ totals vs rule and vs search"/]
```

A tie means the agent's mean error is within 0.5 percentage points of the other method's. It refuses to report if runs are missing, unless `--partial` is given.

---

## 8. Beam model of the walls: the fast FEA calculator (E7)
File: `fea/beam.py`. Plain code, no AI. FEA here means a computer simulation of how the part deforms under load (decision D12).

**The four questions:**

| | Plain answer | Example (healthy re-entrant part) |
|---|---|---|
| What do we have before it? | The design graph (points joined by walls), the case's defect record, and a fix (one wall thickness per remaining 1 mm band) | `out/base/reentrant_graph.json`, 114 walls |
| What does it change? | Nothing in the design. It turns every wall into a beam that can stretch and bend, holds the bottom plate still, pushes the top plate down along Y, and solves for the force | Push of 0.01 mm |
| What do we have after it? | Stiffness and a peak-force estimate (force when the most-stressed wall first reaches the plastic's yield stress), each as a % of a healthy part | Whole healthy part: 656 N/mm, first yield at 405 N (placeholder PLA values; only the % are meaningful) |
| AI or code? | Code | About 0.01 s per layer |

```mermaid
flowchart TD
    G[/"design graph<br>out/base/&lt;shape&gt;_graph.json"/] --> SEG("_wall_segments()<br>cuts walls at the plates,<br>removes missing corner regions (warpage)")
    SEG -->|"walls: start point, end point, thickness"| LR("layer_response()<br>one 0.2 mm layer as beams:<br>builds and solves the stiffness equations")
    LR -->|"stiffness N/mm, first-yield force N"| BC
    S[/"one case from scenarios.json"/] --> BC("BeamCase(case)<br>printed layers: healthy, thin/thick band,<br>or warped corners, from the defect record")
    FIX[/"a fix, e.g. 8 thicknesses"/] --> SC
    BC --> SC("BeamCase.score(fix)<br>adds up all 50 layers side by side,<br>divides by a healthy part")
    SC --> OUT[/"stiffness_ratio · peak_force_ratio · errors<br>(same keys as evaluate.py score)"/]
```

- **Sees, unlike the formula:** where each wall is (corner walls vs middle walls), and warpage as missing walls near the corners of the lowest layers.
- **Still blind to:** layer shift (each layer alone looks healthy), layer bonding, wall-to-wall contact and large crushing. The 3D CalculiX judge is planned for those.
- **Plates:** the walls are held where they meet the solid end plates (no sliding, no turning), because the plates are stiff printed bars.
- **E7 checks:** (1) solver against exact answers for single beams; (2) healthy parts against the Gibson & Ashby formula, target within 10%; (3) for each defect type, does the score tell a fix apart from doing nothing.

## 9. 3D solid model: the planned judge (E8, healthy parts only)
File: `fea/solid3d.py` (written during development; it moves to the locked `fea/judge/` folder only after Amber approves it). Plain code, no AI. Tools: gmsh splits the part into small 4-cornered pieces (tetrahedra), and CalculiX solves how every piece moves.

**The four questions:**

| | Plain answer | Example (healthy re-entrant part) |
|---|---|---|
| What do we have before it? | The part's 3D file (STL) and the plastic's stiffness (placeholder PLA: 3,500 MPa, Poisson's ratio 0.35) | `out/base/reentrant.stl` |
| What does it change? | Nothing in the design. It fills the part with small pieces, holds the bottom face (Y = 0) still, pushes the top face (Y = 50 mm) down along Y by 0.01 mm, and solves for the force | Piece size about 0.6 mm, so about 2 pieces across a 1.2 mm wall |
| What do we have after it? | Stiffness = force / push, in N/mm; later, as a % of a healthy part | Beam model gave 656 N/mm; the 3D number is what E8 measures |
| AI or code? | Code | Probably seconds to a few minutes per part; E8 measures it |

```mermaid
flowchart TD
    STL[/"part file<br>out/base/&lt;shape&gt;.stl"/] --> M("mesh_part(stl, size)<br>gmsh: turns the surface into a solid<br>and fills it with 10-node tetrahedra")
    M -->|"corner points, pieces"| W("write_inp(mesh, material, push)<br>CalculiX input: bottom face held,<br>top face pushed 0.01 mm along Y")
    W -->|"&lt;name&gt;.inp"| R("run_ccx(inp)<br>runs CalculiX from the 'fea' environment")
    R -->|"&lt;name&gt;.dat: total force on the top face"| F("read_force(dat)")
    F --> OUT[/"stiffness N/mm, number of pieces, run time"/]
```

**E8 checks (healthy parts only):**
1. **Tool check:** a solid 10 mm block, where the exact answer is known (stiffness × area ÷ length = 35,000 N/mm).
2. **Piece-size check:** healthy re-entrant at 3 piece sizes. Purpose: smaller pieces are more accurate but slower, so we use the largest size whose answer is within 2% of the next smaller size.
3. **Healthy parts against the beam model and the formula:** hexagon, re-entrant, triangle at the chosen size. Purpose: see whether the fast calculator (beam model) and the judge roughly agree. If they disagree a lot, the agent's calculator points it at the wrong target. No pass mark: the 3D model holds the plates differently and includes the 10 mm depth, so some gap is expected, and the result is reported as it is.

- **Sees, unlike the beam model:** the full 3D solid, including how each layer sits on the one below. That is what should let a later version see layer shift (E9, after Amber reviews E8).
- **Still blind to:** weak bonding between layers (layers are treated as one solid), permanent bending and crushing (stiffness only), and the real PLA values until Yichen's data arrives.
