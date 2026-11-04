"""
The calculation tool the AI agent (v1) and the non-AI search (method B) both get (decision D10).

  evaluate_design(wall_thickness_mm) -> plastic used and the allowed limit, a stiffness ESTIMATE, and the
  checker's rule violations, for a design the caller is considering. One call = one evaluation,
  and both methods get the same budget of calls, so neither has an advantage (proposal 8.5).

The stiffness estimate is the same formula as the score's main measure (for now). The peak-force
estimate in evaluate.score is NOT reported here, so it stays a check neither method can aim at.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from evaluate import *

TOOL_BUDGET = 10   # evaluations per case (decision D10)


class Toolbox:
    """Tools for one case, with a call counter and a log of every call."""
    def __init__(self, case, budget=TOOL_BUDGET):
        self.case, self.budget, self.calls = case, budget, []

    def evaluate_design(self, wall_thickness_mm):
        if len(self.calls) >= self.budget:
            return {"error": f"tool budget used up ({self.budget} calls); submit your final answer now"}
        fix = {"wall_thickness_mm": wall_thickness_mm}
        violations = check(self.case, fix)
        out = {"violations": violations}
        if not any(v["rule"] == "format" for v in violations):
            ratios = layer_area_ratios(self.case, fix)
            out.update({"material_used_mm3": round(material_used(self.case, fix), 1),
                        "material_limit_mm3": round(self.case.budget[BUDGET_MODE] * (1 + BUDGET_TOL), 1),   # the limit check() enforces
                        "stiffness_estimate_pct": round(100 * sum(r ** self.case.n for r in ratios) / len(ratios), 2)})
        self.calls.append({"wall_thickness_mm": wall_thickness_mm, **out})
        out["calls_left"] = self.budget - len(self.calls)
        return out
