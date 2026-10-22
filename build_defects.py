"""Full defect set: 3 shapes x defect types x severity levels x heights.

Under-extrusion, over-extrusion and layer shift start at 10% and 20% of Z (Ma's examples).
Warpage is always at the bottom, so it has no height choice.
Output per part: out/defects/<shape>/<name>.stl and <name>_graph.json (answer key in "defects").
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from defects import *

BASE = os.path.join(os.path.dirname(__file__), "out", "base")
OUT = os.path.join(os.path.dirname(__file__), "out", "defects")
SHAPES = ["hexagon", "triangle", "reentrant"]
HEIGHTS_PCT = [10, 20]


def jobs():
    for dtype in SEVERITY:
        for sev in SEVERITY[dtype]:
            if dtype == "warpage":
                yield dtype, sev, None
            else:
                for pct in HEIGHTS_PCT:
                    yield dtype, sev, pct


def side_view(mesh, rec, ax, title):
    y_cut = 1.0 if rec["type"] == "warpage" else 25.0
    sec = mesh.section(plane_origin=[0, y_cut, 0], plane_normal=[0, 1, 0])
    for line in sec.discrete:
        ax.plot(line[:, 0], line[:, 2], color="#333", lw=0.8)
    ax.axhspan(*rec["z_range_mm"], color="tab:red", alpha=0.12)
    ax.set_xlim(-2, 52); ax.set_ylim(-0.5, 10.5); ax.set_aspect("equal")
    ax.set_title(f"{title}, cut at y = {y_cut:g} mm", fontsize=8)


if __name__ == "__main__":
    summary, failed = {}, []
    for shape in SHAPES:
        os.makedirs(f"{OUT}/{shape}", exist_ok=True)
        g = load_graph(f"{BASE}/{shape}_graph.json")
        base_volume = graph_to_mesh(g).volume
        fig, axes = plt.subplots(4, 1, figsize=(9, 9))   # one example per type: severe, 20%
        for dtype, sev, pct in jobs():
            z0 = None if pct is None else pct / 100 * SIZE_Z
            mesh, rec = inject(g, dtype, sev, z0=z0)
            rec["id"] = 0
            if pct is not None: rec["height_pct"] = pct
            checks = check_defect(mesh, rec, base_volume)
            name = f"{shape}_{dtype}_{sev}" + ("" if pct is None else f"_z{pct}")
            gd = copy.deepcopy(g); gd["defects"] = [rec]; gd["checks"] = checks
            save_graph(gd, f"{OUT}/{shape}/{name}_graph.json")
            mesh.export(f"{OUT}/{shape}/{name}.stl")
            summary[name] = checks
            if not all(checks[k] for k in ("one_piece", "watertight", "defect_on_structure", "inside_box")):
                failed.append(name)
            if sev == "severe" and pct in (20, None):
                side_view(mesh, rec, axes[list(SEVERITY).index(dtype)], f"{shape}: {name}, red = defect band")
        axes[-1].set_xlabel("x (mm)")
        fig.tight_layout(); fig.savefig(f"{OUT}/{shape}_side_views.png", dpi=110); plt.close(fig)

    json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1, default=float)
    vols = [c["volume_change_pct"] for c in summary.values()]
    print(f"parts built: {len(summary)}, all checks passed: {len(summary) - len(failed)}")
    print(f"volume change range: {min(vols)}% to {max(vols)}%")
    if failed: print("FAILED:", failed)
