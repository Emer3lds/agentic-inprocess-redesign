"""Build the three defect-free lattices: graph JSON + STL + preview image."""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lattice import *

OUT = os.path.join(os.path.dirname(__file__), "out", "base")
os.makedirs(OUT, exist_ok=True)

# Cell sizes (see docs/week2_defects.md for the reasoning). Option D: the triangle is the reference;
# hexagon and re-entrant cells are shrunk so their lattice density matches it (about 0.29).
# Offsets centre the pattern on the specimen.
DESIGNS = {
    "hexagon":   dict(params={"l": 4.1}),
    "triangle":  dict(params={"l": 12.0}),
    "reentrant": dict(params={"l": 5.7, "h": 11.4, "theta": 30.0}),
}


def centre_offset(g_probe_params, shape):
    """Shift so the pattern is symmetric left-right about x = 25."""
    if shape == "hexagon":
        a = math.sqrt(3) * g_probe_params["l"]
        return (SIZE_X / 2 - a / 2 * 0, 0.0)            # vertical wall on the centre line
    if shape == "triangle":
        return (SIZE_X / 2, 0.0)                         # node on the centre line
    if shape == "reentrant":
        return (SIZE_X / 2, 0.0)
    return (0.0, 0.0)


def preview(g, poly, path, title):
    fig, ax = plt.subplots(figsize=(5, 5))
    polys = list(poly.geoms) if poly.geom_type == "MultiPolygon" else [poly]
    for p in polys:
        x, y = p.exterior.xy; ax.fill(x, y, color="#333")
        for r in p.interiors:
            x, y = r.xy; ax.fill(x, y, color="white")
    ax.set_xlim(-2, 52); ax.set_ylim(-2, 52); ax.set_aspect("equal")
    ax.set_title(title, fontsize=10); ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


if __name__ == "__main__":
    summary = {}
    for shape, d in DESIGNS.items():
        # pick the vertical shift that avoids tiny, unprintable holes next to the plates
        ox, _ = centre_offset(d["params"], shape)
        a2y = build_graph(shape, d["params"], offset=(ox, 0))["lattice_vectors_mm"][1][1]
        best = None
        for k in range(12):
            oy = a2y * k / 12
            gg = build_graph(shape, d["params"], offset=(ox, oy))
            pp = graph_to_polygon(gg)
            ps = list(pp.geoms) if pp.geom_type == "MultiPolygon" else [pp]
            min_hole = min(shapely.geometry.Polygon(r).area for p in ps for r in p.interiors)
            if best is None or min_hole > best[0] + 1e-6:
                best = (min_hole, oy)
        d["offset"] = (ox, round(best[1], 3)); d["min_hole_mm2"] = round(best[0], 1)
        g = build_graph(shape, d["params"], offset=d["offset"])
        g["offset_mm"] = list(d["offset"])
        poly = graph_to_polygon(g)
        mesh = polygon_to_mesh(poly)
        info = check_mesh(mesh, outline=poly)
        # relative density of the lattice part only (plates removed)
        lat_area = poly.area - 2 * PLATE_T * SIZE_X
        info["lattice_relative_density"] = round(lat_area / (SIZE_X * (SIZE_Y - 2 * PLATE_T)), 3)
        a1 = g["lattice_vectors_mm"][0][0]
        info["cell_width_mm"] = round(a1, 2)
        info["cells_across_x"] = round(SIZE_X / a1, 1)
        info["nodes"], info["edges"] = len(g["nodes"]), len(g["edges"]); info["smallest_hole_mm2"] = d["min_hole_mm2"]
        save_graph(g, f"{OUT}/{shape}_graph.json")
        mesh.export(f"{OUT}/{shape}.stl")
        preview(g, poly, f"{OUT}/{shape}.png", f"{shape}  {d['params']}  rho={info['lattice_relative_density']}")
        summary[shape] = info
        print(shape, info)
    json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1)
