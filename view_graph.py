"""Draw a lattice graph: walls as lines (drawn at their thickness), nodes as dots, wall ids as labels.

Run: python view_graph.py                                    (all three base designs)
     python view_graph.py out/defects/reentrant/<name>_graph.json   (any graph file)
Writes <graph file name>_view.png next to the graph file.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lattice import *


def view(path):
    g = load_graph(path)
    P = {n["id"]: (n["x"], n["y"]) for n in g["nodes"]}
    fig, ax = plt.subplots(figsize=(8, 8))
    for name, (y0, y1) in g["plates"].items():
        ax.axhspan(y0, y1, color="#ccc", zorder=0)
        ax.text(SIZE_X + 1, (y0 + y1) / 2, f"{name} plate", va="center", fontsize=7)
    pts_per_mm = 8 * 72 / 54                     # figure is 8 in wide for about 54 mm
    for e in g["edges"]:
        (x0, y0), (x1, y1) = P[e["u"]], P[e["v"]]
        ax.plot([x0, x1], [y0, y1], color="#4a6fa5", lw=e["t"] * pts_per_mm, alpha=0.5, solid_capstyle="round")
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, str(e["id"]), fontsize=5, ha="center", va="center")
    ax.scatter(*zip(*P.values()), s=6, color="k", zorder=3)
    ax.annotate("", xy=(-3, 40), xytext=(-3, 10), arrowprops=dict(arrowstyle="<->"))
    ax.text(-4, 25, "load (Y)", rotation=90, va="center", ha="right", fontsize=8)
    ax.set_xlim(-6, 58); ax.set_ylim(-2, 52); ax.set_aspect("equal")
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
    ax.set_title(f"{os.path.basename(path)}: {len(g['nodes'])} nodes, {len(g['edges'])} walls "
                 f"(numbers = wall id, line width = thickness)", fontsize=8)
    out = path.replace(".json", "_view.png")
    fig.tight_layout(); fig.savefig(out, dpi=130); plt.close(fig)
    return out


if __name__ == "__main__":
    paths = sys.argv[1:] or [f"out/base/{s}_graph.json" for s in ("hexagon", "triangle", "reentrant")]
    for p in paths:
        print("wrote", view(p))
