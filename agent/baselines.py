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


def band_stiffness(case, t):
    """Stiffness of one band with walls t, relative to a healthy band (score version 1)."""
    return (case.band_lattice_area(t) / case.a0) ** case.n


def stiffness_gap(case):
    """How many healthy bands' worth of stiffness the printed part is missing (+) or has extra (-).
    Measured from the printed part itself, so it works the same for every defect type."""
    per_band = round(BAND_H / case.s["layer_height_mm"])
    return sum(1 - (a / case.a0) ** case.n for a in case.prefix_layer_areas) / per_band


def simple_rule(case):
    """Simple rule, version 2 (2026-10-28). Fix the lost stiffness, not the lost thickness.
    Too stiff : thin every remaining band by the same amount, just enough to cancel the extra
                stiffness (saves plastic, so the budget is never a problem).
    Too weak  : the budget allows no extra plastic, so move plastic instead: thin/thick pairs
                (1.0 / 1.4 mm) starting right above the defect. Because stiffness goes with
                thickness cubed, a thick band gains more than a thin band loses. Thin comes first
                so the thick band sits on a wall at most 0.4 mm narrower (overhang rule).
                Add pairs only while each pair brings the part closer to 100%.
    Nothing missing (layer shift under this score): do nothing."""
    t0 = case.g["wall_thickness_mm"]
    ts = [t0] * case.n_bands
    gap = stiffness_gap(case)
    if gap < 0:
        lo, hi = T_MIN, t0                     # find t where the thinner bands cancel the extra stiffness
        for _ in range(30):
            mid = (lo + hi) / 2
            if case.n_bands * (1 - band_stiffness(case, mid)) > -gap: lo = mid
            else: hi = mid
        ts = [round((lo + hi) / 2, 2)] * case.n_bands
    elif gap > 0:
        swing = MAX_STEP_UP / 2
        pair_gain = band_stiffness(case, t0 - swing) + band_stiffness(case, t0 + swing) - 2
        i = 0
        while i + 1 < case.n_bands and abs(gap - pair_gain) < abs(gap):
            ts[i], ts[i + 1] = round(t0 - swing, 3), round(t0 + swing, 3)
            gap -= pair_gain; i += 2
    return {"wall_thickness_mm": ts}


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
