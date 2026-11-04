"""
Method B: a non-AI search that gets the same information and the same tool as agent v1 (proposal 8.5).

  - Starts from the original design (as the agent may).
  - Learns about a design only through tools.evaluate_design, with the same call budget as the agent.
  - The rules the prompt states in words (thickness range, overhang) it checks itself, as the agent can.
  - Optimizer: COBYLA (scipy), a standard method that needs no formula, only evaluations.
  - Returns the best allowed design it evaluated (closest stiffness estimate to 100%); none -> do nothing.

Run: python agent/search.py    (plain Python, no AI, a few seconds)
Writes out/results/search.json: one result per case for each budget in BUDGETS.
BUDGETS includes the agent's budget (fair comparison) and a large one (what search can do with many tries).
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from scipy.optimize import minimize
from tools import Toolbox, TOOL_BUDGET
from baselines import do_nothing
from evaluate import *

BUDGETS = [TOOL_BUDGET, 200]


class OutOfBudget(Exception):
    pass


def search(case, budget):
    tb, seen = Toolbox(case, budget=budget), {}

    def ev(x):
        key = tuple(round(float(t), 3) for t in x)
        if key not in seen:
            r = tb.evaluate_design(list(key))
            if "error" in r:
                raise OutOfBudget
            seen[key] = r
        return seen[key]

    def overhang_margins(x):
        below = np.concatenate([[case.top_wall_t], x[:-1]])
        return MAX_STEP_UP - (x - below)

    cons = [{"type": "ineq", "fun": lambda x: x - T_MIN}, {"type": "ineq", "fun": lambda x: T_MAX - x},
            {"type": "ineq", "fun": overhang_margins},
            {"type": "ineq", "fun": lambda x: ev(x).get("material_limit_mm3", 0) - ev(x).get("material_used_mm3", 1e9)}]
    x0 = np.array(do_nothing(case)["wall_thickness_mm"], dtype=float)
    try:
        minimize(lambda x: abs(ev(x)["stiffness_estimate_pct"] - 100), x0, method="COBYLA", constraints=cons,
                 options={"rhobeg": 0.1, "maxiter": budget})   # COBYLA's maxiter counts evaluations
    except OutOfBudget:   # backup only; maxiter normally stops it first
        pass
    allowed = [(abs(r["stiffness_estimate_pct"] - 100), list(k)) for k, r in seen.items() if not r["violations"]]
    fix = {"wall_thickness_mm": min(allowed)[1]} if allowed else do_nothing(case)
    return {"case": case.s["id"], "fixer": f"search_b{budget}", "budget": budget, "n_tool_calls": len(tb.calls),
            "fallback_used": not allowed, "fix": fix, "violations": check(case, fix), **score(case, fix)}


if __name__ == "__main__":
    results = []
    print(f"{'case':38s} " + "  ".join(f"{'search, ' + str(b) + ' calls':>18s}" for b in BUDGETS))
    for case in load_cases():
        row = [search(case, b) for b in BUDGETS]
        results += row
        print(f"{case.s['id']:38s} " + "  ".join(f"{r['stiffness_ratio']:9.1%} ({r['n_tool_calls']:3d} used)" for r in row))
    json.dump(results, open(os.path.join(ROOT, "out", "results", "search.json"), "w"), indent=1)
