"""
Lattice design -> graph (JSON) -> STL.

A lattice is stored as a graph:
  nodes: list of {"id", "x", "y"}          (mm)
  edges: list of {"id", "u", "v", "t"}     (u, v = node ids, t = wall thickness in mm)
plus metadata (shape, cell size, specimen size, plates).

Specimen: 50 x 50 mm in XY, 10 mm in Z (fixed by Ma).
Loading direction: Y (compression between a bottom and a top plate).
"""
import json, math
import numpy as np
import shapely
from shapely.geometry import LineString, box, Point
from shapely.ops import unary_union
import trimesh

SIZE_X, SIZE_Y, SIZE_Z = 50.0, 50.0, 10.0
WALL_T = 1.2          # mm, 3 lines of a 0.4 mm nozzle (same as Ma's reference STL)
PLATE_T = 1.8         # mm, top and bottom solid plates (same as Ma's reference STL)


# ---------------------------------------------------------------- unit cells
def _tile(a1, a2, basis, bonds, nx_range, ny_range):
    """Repeat a unit cell. basis = list of (x, y); bonds = list of
    (basis_i, basis_j, di, dj): node i in cell (m, n) links to node j in cell (m+di, n+dj)."""
    pts, segs = {}, []
    for m in nx_range:
        for n in ny_range:
            for (i, j, di, dj) in bonds:
                p = np.array(basis[i]) + m * np.array(a1) + n * np.array(a2)
                q = np.array(basis[j]) + (m + di) * np.array(a1) + (n + dj) * np.array(a2)
                segs.append((tuple(p), tuple(q)))
    return segs


def hexagon_segments(l):
    """Regular hexagonal honeycomb, edge length l, vertical walls along Y (loading)."""
    a1 = (math.sqrt(3) * l, 0.0)
    a2 = (math.sqrt(3) * l / 2, 1.5 * l)
    basis = [(0.0, 0.0), (0.0, l)]
    bonds = [(0, 1, 0, 0), (1, 0, 0, 1), (1, 0, -1, 1)]
    return a1, a2, basis, bonds


def reentrant_segments(l, h, theta_deg=30.0):
    """Re-entrant (auxetic) honeycomb: vertical walls h, inclined walls l at -theta."""
    th = math.radians(theta_deg)
    a1 = (2 * l * math.cos(th), 0.0)
    a2 = (l * math.cos(th), h - l * math.sin(th))
    basis = [(0.0, 0.0), (0.0, h)]
    bonds = [(0, 1, 0, 0), (1, 0, 0, 1), (1, 0, -1, 1)]
    return a1, a2, basis, bonds


def triangle_segments(l):
    """Triangular grid, edge length l, one wall family along X."""
    a1 = (l, 0.0)
    a2 = (l / 2, math.sqrt(3) / 2 * l)
    basis = [(0.0, 0.0)]
    bonds = [(0, 0, 1, 0), (0, 0, 0, 1), (0, 0, -1, 1)]
    return a1, a2, basis, bonds


# ---------------------------------------------------------------- graph build
def build_graph(shape, params, offset=(0.0, 0.0), t=WALL_T):
    if shape == "hexagon":
        a1, a2, basis, bonds = hexagon_segments(params["l"])
    elif shape == "reentrant":
        a1, a2, basis, bonds = reentrant_segments(params["l"], params["h"], params.get("theta", 30.0))
    elif shape == "triangle":
        a1, a2, basis, bonds = triangle_segments(params["l"])
    else:
        raise ValueError(shape)

    N = 40
    segs = _tile(a1, a2, basis, bonds, range(-N, N), range(-N, N))
    frame = box(0, 0, SIZE_X, SIZE_Y)
    ox, oy = offset

    # clip every wall to the specimen outline
    clipped = []
    for p, q in segs:
        p = (p[0] + ox, p[1] + oy); q = (q[0] + ox, q[1] + oy)
        if max(p[0], q[0]) < -1 or min(p[0], q[0]) > SIZE_X + 1: continue
        if max(p[1], q[1]) < -1 or min(p[1], q[1]) > SIZE_Y + 1: continue
        c = LineString([p, q]).intersection(frame)
        if c.is_empty or c.geom_type != "LineString" or c.length < 1e-6: continue
        clipped.append(list(c.coords))

    # merge points into nodes (round to 1 micron)
    key = lambda xy: (round(xy[0], 3), round(xy[1], 3))
    nodes, edges = {}, set()
    for (p, q) in clipped:
        kp, kq = key(p), key(q)
        for k in (kp, kq):
            nodes.setdefault(k, len(nodes))
        if kp != kq:
            edges.add(tuple(sorted((nodes[kp], nodes[kq]))))
    pos = {i: k for k, i in nodes.items()}

    # remove dangling walls: a wall end that touches nothing (and is not on a plate)
    def on_plate(i):
        return pos[i][1] <= 1e-6 or pos[i][1] >= SIZE_Y - 1e-6
    changed = True
    while changed:
        changed = False
        deg = {}
        for u, v in edges:
            deg[u] = deg.get(u, 0) + 1; deg[v] = deg.get(v, 0) + 1
        for e in list(edges):
            u, v = e
            if (deg[u] == 1 and not on_plate(u)) or (deg[v] == 1 and not on_plate(v)):
                edges.discard(e); changed = True
    # drop tiny stubs that only sit inside a plate
    edges = {e for e in edges if not (on_plate(e[0]) and on_plate(e[1]) and pos[e[0]][1] == pos[e[1]][1])}

    used = sorted({n for e in edges for n in e})
    remap = {old: new for new, old in enumerate(used)}
    node_list = [{"id": remap[i], "x": pos[i][0], "y": pos[i][1]} for i in used]
    edge_list = [{"id": k, "u": remap[u], "v": remap[v], "t": t}
                 for k, (u, v) in enumerate(sorted(edges))]
    return {
        "shape": shape,
        "cell_params_mm": params,
        "lattice_vectors_mm": [list(a1), list(a2)],
        "specimen_mm": [SIZE_X, SIZE_Y, SIZE_Z],
        "loading_direction": "Y",
        "wall_thickness_mm": t,
        "plates": {"bottom": [0.0, PLATE_T], "top": [SIZE_Y - PLATE_T, SIZE_Y]},
        "nodes": node_list,
        "edges": edge_list,
        "defects": [],
    }


# ---------------------------------------------------------------- geometry
def graph_to_polygon(g, thickness_override=None, plate_scale=1.0):
    """2D cross-section: each edge becomes a wall of its own thickness, plus the plates.
    plate_scale grows or shrinks each plate about its centre line (used for extrusion defects);
    a grown plate may stick out past y = 0 and y = SIZE_Y."""
    P = {n["id"]: (n["x"], n["y"]) for n in g["nodes"]}
    walls = []
    for e in g["edges"]:
        t = e["t"] if thickness_override is None else thickness_override(e)
        if t <= 0: continue
        walls.append(LineString([P[e["u"]], P[e["v"]]]).buffer(t / 2, cap_style="round", join_style="round", quad_segs=4))
    plates = []
    for y0, y1 in (g["plates"]["bottom"], g["plates"]["top"]):
        c, half = (y0 + y1) / 2, (y1 - y0) / 2 * plate_scale
        plates.append(box(0, c - half, SIZE_X, c + half))
    lattice = unary_union(walls).intersection(box(0, 0, SIZE_X, SIZE_Y))
    if plate_scale < 1:   # walls must not poke out where a shrunken plate used to be
        lattice = lattice.intersection(box(0, plates[0].bounds[1], SIZE_X, plates[1].bounds[3]))
    poly = unary_union([lattice] + plates)
    return poly.buffer(0)


def polygon_to_mesh(poly, z0=0.0, z1=SIZE_Z):
    polys = list(poly.geoms) if poly.geom_type == "MultiPolygon" else [poly]
    meshes = []
    for p in polys:
        m = trimesh.creation.extrude_polygon(p, height=z1 - z0)
        m.apply_translation([0, 0, z0])
        meshes.append(m)
    return trimesh.util.concatenate(meshes)


def graph_to_mesh(g):
    return polygon_to_mesh(graph_to_polygon(g))


def check_mesh(m):
    return {
        "watertight": bool(m.is_watertight),
        "pieces": int(m.body_count),
        "bounds_mm": np.round(m.bounds, 3).tolist(),
        "volume_mm3": round(float(m.volume), 1),
        "relative_density": round(float(m.volume) / (SIZE_X * SIZE_Y * SIZE_Z), 3),
    }


def save_graph(g, path):
    with open(path, "w") as f:
        json.dump(g, f, indent=1)


def load_graph(path):
    with open(path) as f:
        return json.load(f)
