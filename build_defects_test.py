"""Test: one defect of each type on the hexagon (medium level, band starting at 20% of Z)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from defects import *

BASE = os.path.join(os.path.dirname(__file__), "out", "base")
OUT = os.path.join(os.path.dirname(__file__), "out", "defects_test")
os.makedirs(OUT, exist_ok=True)

SHAPE, SEVERITY_LEVEL, Z0 = "hexagon", "medium", 0.2 * SIZE_Z

g = load_graph(f"{BASE}/{SHAPE}_graph.json")
base_volume = graph_to_mesh(g).volume

fig, axes = plt.subplots(4, 1, figsize=(9, 9))
for ax, dtype in zip(axes, SEVERITY):
    mesh, rec = inject(g, dtype, SEVERITY_LEVEL, z0=Z0)
    rec["id"] = 0
    checks = check_defect(mesh, rec, base_volume)
    name = f"{SHAPE}_{dtype}_{SEVERITY_LEVEL}"
    gd = copy.deepcopy(g); gd["defects"] = [rec]; gd["checks"] = checks
    save_graph(gd, f"{OUT}/{name}_graph.json")
    mesh.export(f"{OUT}/{name}.stl")
    print(name, {k: v for k, v in checks.items() if k != "bounds_mm"})

    # side view: cut through the lattice at y = 25 mm (warpage: at y = 1 mm, inside the end plate near the corners)
    y_cut = 1.0 if dtype == "warpage" else 25.0
    sec = mesh.section(plane_origin=[0, y_cut, 0], plane_normal=[0, 1, 0])
    for line in sec.discrete:
        ax.plot(line[:, 0], line[:, 2], color="#333", lw=0.8)
    ax.axhspan(*rec["z_range_mm"], color="tab:red", alpha=0.12)
    ax.set_xlim(-2, 52); ax.set_ylim(-0.5, 10.5); ax.set_aspect("equal")
    ax.set_title(f"{dtype} ({SEVERITY_LEVEL}), cut at y = {y_cut:g} mm, red = defect band", fontsize=9)
axes[-1].set_xlabel("x (mm)")
fig.tight_layout(); fig.savefig(f"{OUT}/side_views.png", dpi=110); plt.close(fig)
