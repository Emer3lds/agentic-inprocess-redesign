"""
Experiment E9: the 3D solid model (fea/solid3d.py) on the re-entrant defect parts. Plain code, no AI.
Design: docs/pipeline_diagrams.md section 11.

  Whole parts (no half model): healthy out/base/reentrant.stl and the 4 medium defect parts
  (under-extrusion, over-extrusion, layer shift at 10% height; warpage), at piece sizes 1.2 and
  0.8 mm. For each: stiffness, pieces, seconds, and % of healthy at the same size.
  "Settled": % of healthy changes by less than 0.5 points between 1.2 and 0.8 mm.
  Held and pushed faces: the nodes at the part's lowest y and highest y (solid3d faces="minmax").
  Over-extrusion is also run with faces="planes" (every node at y <= 0 and y >= 50), because its
  thicker plates stick out 0.18 mm past y = 0 and y = 50 only in the 1 mm band z = 1..2.
  Next to the 3D numbers: the beam model's and the formula's % for "do nothing" on the matching z10
  repair case, from out/results/e7_beam_checks.json (check3_separation).

Run: python fea/e9_defect_checks.py [--sizes 1.2 0.8] [--rerun]
Runs one part at a time (memory). Finished runs are reused from out/fea3d/e9_<run>/result.json.
Writes out/results/e9_defect_checks.json.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import solid3d as s3

DEF = os.path.join(ROOT, "out", "defects", "reentrant")
PARTS = {  # label -> (STL, e7 case id)
    "healthy": (os.path.join(ROOT, "out", "base", "reentrant.stl"), None),
    "under_extrusion": (os.path.join(DEF, "reentrant_under_extrusion_medium_z10.stl"), "reentrant_under_extrusion_medium_z10"),
    "over_extrusion": (os.path.join(DEF, "reentrant_over_extrusion_medium_z10.stl"), "reentrant_over_extrusion_medium_z10"),
    "layer_shift": (os.path.join(DEF, "reentrant_layer_shift_medium_z10.stl"), "reentrant_layer_shift_medium_z10"),
    "warpage": (os.path.join(DEF, "reentrant_warpage_medium.stl"), "reentrant_warpage_medium_z10"),
}
EXTRA = {"over_extrusion_planes": ("over_extrusion", "planes")}  # extra face choice
SETTLED = 0.5   # points of % of healthy (tie margin of E7)
E7 = os.path.join(ROOT, "out", "results", "e7_beam_checks.json")
OUT = os.path.join(ROOT, "out", "results", "e9_defect_checks.json")


def run(label, stl, size, faces, rerun):
    name = f"e9_{label}_h{size:g}".replace(".", "p")
    r = s3.stiffness(stl, size, name=name, reuse=not rerun, faces=faces)
    print(f"  {label:22s} {size:g} mm: {r['stiffness_N_per_mm']:8.1f} N/mm, {r['n_elements']:7d} pieces, "
          f"{r['seconds']:5.1f} s, worst quality {r.get('min_quality')}, {r.get('n_poor_pieces')} under 0.01", flush=True)
    return r


def e7_do_nothing():
    """{case id: do_nothing beam_stiffness and formula_stiffness} from check3_separation.
    E7 stores them as fractions of healthy; here they are turned into % of healthy."""
    if not os.path.exists(E7):
        return {}
    return {r["id"]: {"beam_pct_healthy": round(100 * r["do_nothing"]["beam_stiffness"], 2),
                      "formula_pct_healthy": round(100 * r["do_nothing"]["formula_stiffness"], 2)}
            for r in json.load(open(E7))["check3_separation"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=float, nargs="+", default=[1.2, 0.8])
    ap.add_argument("--rerun", action="store_true")
    a = ap.parse_args()
    jobs = [(lab, stl, "minmax") for lab, (stl, _) in PARTS.items()] + \
           [(lab, PARTS[src][0], f) for lab, (src, f) in EXTRA.items()]
    runs = {}
    for size in a.sizes:   # one run at a time
        print(f"piece size {size:g} mm")
        for lab, stl, faces in jobs:
            try:
                runs.setdefault(lab, {})[f"{size:g}"] = run(lab, stl, size, faces, a.rerun)
            except Exception as e:
                print(f"  {lab}: FAILED: {e}", flush=True)
                runs.setdefault(lab, {})[f"{size:g}"] = {"error": str(e)}
    beam = e7_do_nothing()
    s1, s2 = f"{a.sizes[0]:g}", f"{a.sizes[-1]:g}"
    table = {}
    for lab in runs:
        row = {}
        for s in (s1, s2):
            h, r = runs["healthy"].get(s, {}), runs[lab].get(s, {})
            if "stiffness_N_per_mm" in h and "stiffness_N_per_mm" in r:
                row[f"pct_healthy_{s}"] = round(100 * r["stiffness_N_per_mm"] / h["stiffness_N_per_mm"], 2)
        if len(row) == 2:
            row["change_points"] = round(row[f"pct_healthy_{s2}"] - row[f"pct_healthy_{s1}"], 2)
            row["settled"] = abs(row["change_points"]) < SETTLED
        cid = PARTS.get(lab, PARTS.get(EXTRA.get(lab, ("",))[0], (None, None)))[1]
        b = beam.get(cid, {}) if cid else {}
        row["e7_case"] = cid
        row.update(b)
        table[lab] = row
    print(f"\n{'part':22s} {s1+' mm %':>9s} {s2+' mm %':>9s} {'change':>7s} settled  beam % formula %")
    for lab, row in table.items():
        print(f"{lab:22s} {row.get('pct_healthy_'+s1, ''):>9} {row.get('pct_healthy_'+s2, ''):>9} "
              f"{row.get('change_points', ''):>7} {str(row.get('settled', '')):7s} "
              f"{row.get('beam_pct_healthy', '')} {row.get('formula_pct_healthy', '')}")
    res = {"design": "docs/pipeline_diagrams.md section 11", "settled_rule_points": SETTLED,
           "faces": "minmax = nodes at the part's lowest and highest y; planes = all nodes at y <= 0 and y >= 50",
           "runs": runs, "table": table}
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
