"""Stronger defect parts for Yichen's first print batch (decision D15). Plain code, no AI.

Why: the repair-case defects (a 1 mm band) change stiffness by only about 3 to 5%, which is
within the usual scatter between printed copies. These parts use stronger defects so a crush test
can show whether each defect really weakens a printed part (proposal sections 10.1 and 10.2).
Healthy parts for the batch are out/base/<shape>.stl.

Output: out/print_batch/<name>.stl and <name>_graph.json, plus summary.json.
Run: python build_print_batch.py
"""
import copy, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "fea"))
from defects import *
import beam

OUT = os.path.join(HERE, "out", "print_batch")
START = 1.0   # mm: the defect starts at 10% of the 10 mm height, as in the repair cases
PARTS = [  # name, defect type, severity level, wall thickness or shift (None = table value), band height mm
    # walls are whole nozzle lines (0.4 mm nozzle) so they print as drawn; end plates stay 1.8 mm
    ("reentrant_under_extrusion_3mm_0p84", "under_extrusion", "severe", 0.84, 3.0),   # 2 lines (70%)
    ("reentrant_over_extrusion_3mm_1p6", "over_extrusion", "severe", 1.6, 3.0),       # 4 lines (133%)
    ("reentrant_layer_shift_1p0mm", "layer_shift", "severe", None, None),            # 1.0 mm shift from 1 mm up
]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    g = load_graph(os.path.join(HERE, "out", "base", "reentrant_graph.json"))
    base_volume = graph_to_mesh(g).volume
    k0, _ = beam.layer_response(g, g["wall_thickness_mm"], 0.2)
    summary = {}
    for name, dtype, sev, value, band_h in PARTS:
        mesh, rec = inject(g, dtype, sev, z0=START, band_h=band_h, value=value, keep_plates=True)
        rec["id"] = 0; rec["height_pct"] = 10
        checks = check_defect(mesh, rec, base_volume)
        # predicted stiffness, % of healthy: layers side by side, each 0.2 mm (formula and beam model)
        if dtype == "layer_shift":
            pred = {"formula_pct": 100.0, "beam_pct": 100.0, "note": "both models are blind to layer shift"}
        else:
            t, (z0, z1), t0 = rec["wall_thickness_mm"], rec["z_range_mm"], g["wall_thickness_mm"]
            frac = (z1 - z0) / SIZE_Z
            k, _ = beam.layer_response(g, t, 0.2)
            pred = {"formula_pct": round(100 * (1 - frac * (1 - (t / t0) ** 3)), 1),
                    "beam_pct": round(100 * (1 - frac * (1 - k / k0)), 1)}
        gd = copy.deepcopy(g); gd["defects"] = [rec]; gd["checks"] = checks; gd["predicted"] = pred
        save_graph(gd, os.path.join(OUT, f"{name}_graph.json"))
        mesh.export(os.path.join(OUT, f"{name}.stl"))
        summary[name] = {"defect": rec, "checks": checks, "predicted": pred}
        ok = all(checks[c] for c in ("one_piece", "watertight", "defect_on_structure", "inside_box"))
        print(f"{name:40s} checks {'pass' if ok else 'FAIL'}  volume {checks['volume_change_pct']:+.2f}%  "
              f"predicted stiffness: formula {pred['formula_pct']}%, beam {pred['beam_pct']}%")
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
