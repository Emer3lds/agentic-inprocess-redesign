"""
Build repair scenarios: a part printed only up to the moment the printer is stopped.

Story of one scenario (see docs/decisions.md, D2):
  1. A defect starts at height z0.
  2. A camera or sensor notices it DETECT_DELAY mm later, and the printer pauses.
  3. Everything printed so far (z <= z_cut) is fixed. That is the "prefix" STL.
  4. The agent may redesign only what is above z_cut, using no more material than the
     original design would have used there (the material budget).

Output: out/scenarios/<shape>/<id>_prefix.stl, one scenarios.json describing every case,
and one side-view picture.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import trimesh
from defects import *
import defects

# One place for the axis convention (Ma: never mix X and Y up). Everything else reads from here.
AXES = {"print_direction": "Z", "load_direction": "Y", "layer_shift_direction": "X"}
LAYER_H = 0.2                     # mm, one printed layer
DETECT_DELAY = defects.BAND_H     # mm, how long a defect keeps printing before it is noticed (5 layers)

BASE = os.path.join(os.path.dirname(HERE), "out", "base")
OUT = os.path.join(os.path.dirname(HERE), "out", "scenarios")

# First small set (D3): one shape, medium severity, defect start at 10%, 50% and 80% of the height.
SHAPES = ["reentrant"]
SEVERITIES = ["medium"]
START_PCT = [10, 50, 80]


def cut_below(mesh, z_cut):
    """Keep only the part of the mesh at or below z_cut (what has been printed).
    Cut 0.1 micron low: a cut exactly on a band boundary leaves zero-volume scraps."""
    keep = trimesh.creation.box(bounds=[[-5, -5, -1], [SIZE_X + 5, SIZE_Y + 5, z_cut - 1e-4]])
    return to_trimesh(to_manifold(mesh) ^ to_manifold(keep))


def make_scenario(g, shape, dtype, sev, pct):
    z0 = pct / 100 * SIZE_Z
    z_cut = round(round((z0 + DETECT_DELAY) / LAYER_H) * LAYER_H, 3)
    # warpage always starts at the bed; pct then only sets when the printer is stopped
    mesh, rec = inject(g, dtype, sev, z0=None if dtype == "warpage" else z0)
    prefix = cut_below(mesh, z_cut)

    area = graph_to_polygon(g).area                   # cross-section of one normal layer, mm2
    checks = check_mesh(prefix)
    sid = f"{shape}_{dtype}_{sev}_z{pct}"
    scenario = {
        "id": sid,
        "shape": shape,
        "axes": AXES,
        "specimen_mm": g["specimen_mm"],
        "layer_height_mm": LAYER_H,
        "defect_start_pct": pct,
        "z_cut_mm": z_cut,
        "remaining_height_mm": round(SIZE_Z - z_cut, 3),
        "defect": rec,                                # assumed measured exactly (D4)
        "material_budget_mm3": round(area * (SIZE_Z - z_cut), 1),
        "prefix_volume_mm3": checks["volume_mm3"],
        "nominal_prefix_volume_mm3": round(area * z_cut, 1),
        "base_graph": f"out/base/{shape}_graph.json",
        "prefix_stl": f"out/scenarios/{shape}/{sid}_prefix.stl",
        "prefix_checks": {"one_piece": checks["pieces"] == 1, "watertight": checks["watertight"],
                          "top_mm": checks["bounds_mm"][1][2]},
    }
    return scenario, prefix


if __name__ == "__main__":
    scenarios, pics = [], []
    for shape in SHAPES:
        os.makedirs(f"{OUT}/{shape}", exist_ok=True)
        g = load_graph(f"{BASE}/{shape}_graph.json")
        for dtype in SEVERITY:
            for sev in SEVERITIES:
                for pct in START_PCT:
                    s, prefix = make_scenario(g, shape, dtype, sev, pct)
                    prefix.export(os.path.join(os.path.dirname(HERE), s["prefix_stl"]))
                    scenarios.append(s); pics.append((s, prefix))

    json.dump(scenarios, open(f"{OUT}/scenarios.json", "w"), indent=1)

    # side view of every prefix: a cut through the middle (y = 25), or near the edge for warpage
    fig, axes = plt.subplots(len(pics), 1, figsize=(8, 1.1 * len(pics)))
    for ax, (s, prefix) in zip(axes, pics):
        y_cut = 1.0 if s["defect"]["type"] == "warpage" else 25.0
        for line in prefix.section(plane_origin=[0, y_cut, 0], plane_normal=[0, 1, 0]).discrete:
            ax.plot(line[:, 0], line[:, 2], color="#333", lw=0.6)
        ax.axhline(s["z_cut_mm"], color="tab:red", lw=0.8)
        ax.set_xlim(-2, 52); ax.set_ylim(-0.5, 10.5); ax.set_yticks([0, 10])
        ax.set_title(f"{s['id']} (red line = printer stops, y = {y_cut:g} mm)", fontsize=7)
    fig.tight_layout(); fig.savefig(f"{OUT}/{SHAPES[0]}_prefix_side_views.png", dpi=110); plt.close(fig)

    bad = [s["id"] for s in scenarios if not (s["prefix_checks"]["one_piece"] and s["prefix_checks"]["watertight"])]
    print(f"scenarios: {len(scenarios)}, prefixes one piece and watertight: {len(scenarios) - len(bad)}")
    for s in scenarios:
        print(f"  {s['id']:38s} cut at {s['z_cut_mm']:4.1f} mm, top {s['prefix_checks']['top_mm']:4.1f}, "
              f"budget {s['material_budget_mm3']:7.1f} mm3")
    if bad: print("FAILED:", bad)
