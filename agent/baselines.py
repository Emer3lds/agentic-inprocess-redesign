"""
Fixers that use no AI, run on every case and judged by evaluate.py.

  do_nothing  : keep printing the original design (shows how much damage the defect does)
  simple_rule : what a person would try without AI (the bar the AI agent must beat).

Run: python agent/baselines.py   (plain Python, no AI, a few seconds)
Writes out/results/baselines.json and prints one line per case.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from evaluate import *


def do_nothing(case):
    return {"wall_thickness_mm": [case.g["wall_thickness_mm"]] * case.n_bands}


def simple_rule(case):
    """Amber's rule, version 1 (2026-10-28), as she wrote it:
    under-extrusion: make the rest of the walls thicker by however much they were too thin;
    over-extrusion: make the rest of the walls thinner by however much they were too thick;
    layer shift and warpage: do nothing (thickness cannot help / barely matters)."""
    d = case.s["defect"]
    t0 = case.g["wall_thickness_mm"]
    if d["type"] in ("under_extrusion", "over_extrusion"):
        error = d["wall_thickness_mm"] - t0          # negative = too thin
        return {"wall_thickness_mm": [round(t0 - error, 3)] * case.n_bands}
    return do_nothing(case)


FIXERS = {"do_nothing": do_nothing, "simple_rule": simple_rule}


if __name__ == "__main__":
    out_dir = os.path.join(ROOT, "out", "results")
    os.makedirs(out_dir, exist_ok=True)
    results = []
    print(f"budget mode: {BUDGET_MODE}")
    print(f"{'case':38s} {'fixer':11s} {'stiffness':>9s}  {'material / budget':>18s}  allowed?")
    for case in load_cases():
        for name, fixer in FIXERS.items():
            fix = fixer(case)
            violations = check(case, fix)
            sc = score(case, fix)
            results.append({"case": case.s["id"], "fixer": name, "fix": fix, "violations": violations, **sc,
                            "budget_mm3": case.budget})
            budget = case.budget[BUDGET_MODE]
            print(f"{case.s['id']:38s} {name:11s} {sc['stiffness_ratio']:9.1%}  {sc['material_mm3']:8.0f} / {budget:7.0f}  "
                  + ("yes" if not violations else "no: " + ", ".join(x["rule"] for x in violations)))
    json.dump(results, open(os.path.join(out_dir, "baselines.json"), "w"), indent=1)
