"""
E7: can we trust the beam model (fea/beam.py) before any prints arrive? Plain code, no AI, under a minute.

Check 1. Solver: single walls against the exact textbook answer (must match to 0.01%).
Check 2. Healthy parts against the Gibson & Ashby formula (target: within 10%), with the walls held
         where they meet the end plates. Also runs the model with walls that cannot stretch. Review
         (2026-11-07): the hexagon's close match is partly two effects cancelling (held plates add about
         40%, wall stretching removes about 20 to 30%), so this check does not validate absolute stiffness.
Check 3. For each of the 12 cases: does the score tell a fix apart from doing nothing?
         Fixes compared: do nothing, the simple rule (designed with the formula score), and the best
         single thickness for all remaining bands under the beam model ("beam-tuned", allowed by the checker).

Run: python fea/trust_checks.py     Writes out/results/e7_beam_checks.json and prints a short summary.
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "agent"))
import beam
from evaluate import load_cases, check, score as formula_score
from baselines import do_nothing, simple_rule

TIE = 0.005   # 0.5 percentage points, the same tie margin as compare.py
out = {}

# ---- check 1: single walls
def one_wall(p, q):
    return {"specimen_mm": [50, 50, 10], "plates": {"bottom": [0, 1.8], "top": [48.2, 50]},
            "nodes": [{"id": 0, "x": p[0], "y": p[1]}, {"id": 1, "x": q[0], "y": q[1]}],
            "edges": [{"id": 0, "u": 0, "v": 1, "t": 1.2}]}
t, d = 1.2, 10.0
c1 = []
for name, p, q in [("vertical wall", (25, 1.8), (25, 48.2)),
                   ("wall at 60 degrees", (10, 1.8), (10 + 46.4 / math.tan(math.radians(60)), 48.2))]:
    L = math.hypot(q[0] - p[0], q[1] - p[1]); phi = math.atan2(q[1] - p[1], q[0] - p[0])
    exact = beam.E_PLA * d * t / L * math.sin(phi) ** 2 + 12 * beam.E_PLA * d * t ** 3 / 12 / L ** 3 * math.cos(phi) ** 2
    k, _ = beam.layer_response(one_wall(p, q), t, depth=d)
    c1.append({"wall": name, "model_N_per_mm": round(k, 3), "exact_N_per_mm": round(exact, 3),
               "diff_pct": round(100 * (k / exact - 1), 4)})
out["check1_single_walls"] = c1

# ---- check 2: healthy parts vs Gibson & Ashby
def ga_relative_modulus(shape, p, t=1.2):
    if shape == "triangle":                      # stretching-dominated: E*/Es = density / 3 (Wang & McDowell 2004)
        return 2 / math.sqrt(3) * t / p["l"]
    th = math.radians(p.get("theta", 30.0)); sgn = -1 if shape == "reentrant" else 1
    h = p.get("h", p["l"])                       # bending-dominated, load along the vertical walls
    return (t / p["l"]) ** 3 * math.cos(th) / ((h / p["l"] + sgn * math.sin(th)) * math.sin(th) ** 2)

src = open(os.path.join(HERE, "beam.py"), encoding="utf8").read().replace(
    "a, b, k6, k4 = E_PLA * A / L,", "a, b, k6, k4 = 1000 * E_PLA * A / L,")
stiff_axial = {"__file__": os.path.join(HERE, "beam.py")}
exec(compile(src, "beam_walls_cannot_stretch", "exec"), stiff_axial)
c2 = []
for shape in ("hexagon", "reentrant", "triangle"):
    g = beam.load_graph(os.path.join(ROOT, "out", "base", f"{shape}_graph.json"))
    W, D = g["specimen_mm"][0], g["specimen_mm"][2]
    L = g["plates"]["top"][0] - g["plates"]["bottom"][1]
    k_ga = ga_relative_modulus(shape, g["cell_params_mm"]) * beam.E_PLA * W * D / L
    k, fy = beam.healthy_part(g)
    k_ns = stiff_axial["layer_response"](g, g["wall_thickness_mm"], depth=D)[0]
    c2.append({"shape": shape, "beam_N_per_mm": round(k), "formula_N_per_mm": round(k_ga),
               "diff_pct": round(100 * (k / k_ga - 1), 1), "within_10pct": bool(abs(k / k_ga - 1) <= 0.10),
               # only meaningful for bending shapes; the triangle carries load by stretching
               "diff_if_walls_cannot_stretch_pct": None if shape == "triangle" else round(100 * (k_ns / k_ga - 1), 1),
               "first_yield_N": round(fy)})
out["check2_healthy_vs_formula"] = c2

# ---- check 3: does the score tell a fix from doing nothing?
def best_uniform(case, bc):
    """Best single thickness for all remaining bands under the beam model, among allowed fixes.
    Stiffness rises with thickness, so halve the interval until the part is at 100% or the limit is hit."""
    allowed = lambda t: not check(case, {"wall_thickness_mm": [t] * case.n_bands})
    lo, hi = 0.8, 2.0
    while not allowed(hi):                       # thickest allowed (plastic budget and overhang rules)
        hi = round(hi - 0.01, 3)
    for _ in range(12):
        mid = round((lo + hi) / 2, 3)
        if bc.score({"wall_thickness_mm": [mid] * case.n_bands})["stiffness_ratio"] < 1: lo = mid
        else: hi = mid
    cands = [{"wall_thickness_mm": [t] * case.n_bands} for t in (lo, hi) if allowed(t)]
    return min(cands, key=lambda f: bc.score(f)["error"])

c3 = []
for case in load_cases():
    bc = beam.BeamCase(case.s)
    fixes = {"do_nothing": do_nothing(case), "simple_rule": simple_rule(case), "beam_tuned": best_uniform(case, bc)}
    row = {"id": case.s["id"], "type": case.s["defect"]["type"], "start_pct": case.s["defect_start_pct"]}
    for name, fix in fixes.items():
        f, b = formula_score(case, fix), bc.score(fix)
        row[name] = {"formula_stiffness": f["stiffness_ratio"], "beam_stiffness": b["stiffness_ratio"],
                     "formula_peak": f["peak_force_ratio"], "beam_peak": b["peak_force_ratio"],
                     "beam_first_yield": b["first_yield_ratio"]}
    row["beam_tuned_thickness_mm"] = fixes["beam_tuned"]["wall_thickness_mm"][0]
    nothing_err = abs(row["do_nothing"]["beam_stiffness"] - 1)
    tuned_err = abs(row["beam_tuned"]["beam_stiffness"] - 1)
    row["beam_sees_damage"] = bool(nothing_err > TIE)
    row["beam_separates_fix_from_nothing"] = bool(nothing_err - tuned_err > TIE)
    c3.append(row)
out["check3_separation"] = c3

os.makedirs(os.path.join(ROOT, "out", "results"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "out", "results", "e7_beam_checks.json"), "w"), indent=1)

# ---- short summary
print("Check 1, single walls (model vs exact):", ", ".join(f"{r['wall']} {r['diff_pct']:+.4f}%" for r in c1))
print("Check 2, healthy parts (beam model vs Gibson & Ashby):")
for r in c2:
    ns = r["diff_if_walls_cannot_stretch_pct"]
    print(f"  {r['shape']:9s} {r['diff_pct']:+6.1f}%  within 10%: {r['within_10pct']}   "
          + ("" if ns is None else f"(walls that cannot stretch: {ns:+.1f}%)"))
print("Check 3, stiffness % of healthy (formula -> beam model):")
print("  case                      do nothing        simple rule       beam-tuned       separates?")
for r in c3:
    cell = lambda k: f"{100*r[k]['formula_stiffness']:6.1f} -> {100*r[k]['beam_stiffness']:6.1f}"
    print(f"  {r['type'][:15]:15s} {r['start_pct']:3d}%  {cell('do_nothing')}  {cell('simple_rule')}  "
          f"{100*r['beam_tuned']['beam_stiffness']:6.1f} ({r['beam_tuned_thickness_mm']:.3f} mm)  {r['beam_separates_fix_from_nothing']}")
print("Force % of healthy, do nothing at 10% (formula peak | beam: layers' yield added up | whole part's first yield):")
for r in c3[::3]:
    d = r["do_nothing"]
    print(f"  {r['type']:15s} {100*d['formula_peak']:6.1f} | {100*d['beam_peak']:6.1f} | {100*d['beam_first_yield']:6.1f}")
