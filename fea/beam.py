"""
Beam model of the lattice walls: the fast FEA calculator (decision D12). Plain code, no AI.

What it does, in plain words:
  - Each wall in the design graph becomes a beam that can stretch and bend (a 2D frame model).
  - The end plates are treated as rigid: the bottom plate is held still, the top plate is pushed
    down along Y (the loading direction) by a small amount.
  - Solving the beam equations gives the force needed for that push, so stiffness = force / push.
  - Peak-force estimate: the force at which the most-stressed wall first reaches the plastic's
    yield stress (first yield). Real crush peaks come later than first yield, so only ratios to a
    healthy part are meaningful, not the absolute value.
  - The part is a stack of 0.2 mm layers squeezed side by side (like springs in parallel), the same
    idea as the formula score (D8). Each layer is its own 2D beam model with its own wall thickness.

What it sees that the formula (agent/evaluate.py) does not:
  - which walls are where (a wall near a corner vs in the middle), and wall thickness per wall;
  - warpage as missing walls near the corners of the lowest layers, not just as missing area.
What it still cannot see:
  - layer shift (each layer on its own looks healthy; only a 3D model can see layers sliding);
  - how well layers bond, contact between walls, and large crushing. CalculiX (3D) is the judge for that.

Units: mm, N, MPa. Material values are placeholders for PLA until Yichen's data arrives; they
cancel out in every ratio to a healthy part.
"""
import json, math, os, sys
import numpy as np
import shapely.geometry as sg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

E_PLA = 3500.0        # MPa, placeholder Young's modulus for printed PLA
YIELD_PLA = 50.0      # MPa, placeholder yield stress for printed PLA
LAYER_H = 0.2         # mm
SIZE = 50.0           # mm, specimen in X and Y
TOL = 1e-6


def load_graph(path):
    return json.load(open(path))


def _wall_segments(g, thickness, holes=()):
    """Walls clipped to the lattice zone between the plates, minus any missing regions (holes).
    Returns a list of (p0, p1, t). thickness: one number for all walls, or a dict edge id -> t."""
    y0, y1 = g["plates"]["bottom"][1], g["plates"]["top"][0]
    zone = sg.box(-1.0, y0, g["specimen_mm"][0] + 1.0, y1)
    for h in holes:
        zone = zone.difference(h)
    xy = {n["id"]: (n["x"], n["y"]) for n in g["nodes"]}
    segs = []
    for e in g["edges"]:
        t = thickness if not isinstance(thickness, dict) else thickness.get(e["id"], e["t"])
        piece = sg.LineString([xy[e["u"]], xy[e["v"]]]).intersection(zone)
        for part in getattr(piece, "geoms", [piece]):
            if part.geom_type == "LineString" and part.length > 1e-3:
                c = list(part.coords)
                segs.append((c[0], c[-1], t))
    return segs, y0, y1


def layer_response(g, thickness, depth=1.0, holes=(), delta=0.01, plates="clamped"):
    """One layer, `depth` mm thick in Z. Returns (stiffness N/mm, first-yield force N).
    thickness: wall thickness in mm (one number, or a dict edge id -> t)."""
    segs, y0, y1 = _wall_segments(g, thickness, holes)
    nodes, index = [], {}
    def nid(p):
        key = (round(p[0], 5), round(p[1], 5))
        if key not in index:
            index[key] = len(nodes); nodes.append(key)
        return index[key]
    elems = [(nid(a), nid(b), t) for a, b, t in segs]
    n = len(nodes)
    K = np.zeros((3 * n, 3 * n))
    geo = []
    for i, j, t in elems:
        (xi, yi), (xj, yj) = nodes[i], nodes[j]
        L = math.hypot(xj - xi, yj - yi); c, s = (xj - xi) / L, (yj - yi) / L
        A, I = depth * t, depth * t ** 3 / 12.0
        a, b, k6, k4 = E_PLA * A / L, 12 * E_PLA * I / L ** 3, 6 * E_PLA * I / L ** 2, 4 * E_PLA * I / L
        kl = np.array([[a, 0, 0, -a, 0, 0], [0, b, k6, 0, -b, k6], [0, k6, k4, 0, -k6, k4 / 2],
                       [-a, 0, 0, a, 0, 0], [0, -b, -k6, 0, b, -k6], [0, k6, k4 / 2, 0, -k6, k4]])
        T = np.zeros((6, 6)); R = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]]); T[:3, :3] = R; T[3:, 3:] = R
        dofs = [3 * i, 3 * i + 1, 3 * i + 2, 3 * j, 3 * j + 1, 3 * j + 2]
        K[np.ix_(dofs, dofs)] += T.T @ kl @ T
        geo.append((dofs, T, kl, A, I, t))
    # boundary: nodes on the bottom plate face are held; nodes on the top plate face move -delta in Y.
    # "clamped" (default): the solid end plates stop the walls they join from sliding or turning
    #   (the plates are stiff printed bars, so this matches the specimen).
    # "slip": walls may slide sideways and turn on the plates; only used to check the solver against
    #   the textbook formula, which assumes an endless lattice with nothing holding it at the sides.
    u = np.zeros(3 * n); fixed = np.zeros(3 * n, bool)
    pinned = False
    for k, (x, y) in enumerate(nodes):
        if abs(y - y0) < TOL or abs(y - y1) < TOL:
            if plates == "clamped":
                fixed[3 * k:3 * k + 3] = True
            else:
                fixed[3 * k + 1] = True
                if not pinned:
                    fixed[3 * k] = True; pinned = True
            if abs(y - y1) < TOL:
                u[3 * k + 1] = -delta
    free = ~fixed
    Kff = K[np.ix_(free, free)] + np.eye(free.sum()) * 1e-9 * np.trace(K) / len(K)  # tiny term for loose wall pieces
    u[free] = np.linalg.solve(Kff, -K[np.ix_(free, fixed)] @ u[fixed])
    f = K @ u
    force = -sum(f[3 * k + 1] for k, (x, y) in enumerate(nodes) if abs(y - y1) < TOL)
    sig_max = 0.0
    for dofs, T, kl, A, I, t in geo:
        q = kl @ (T @ u[dofs])                      # local end forces: N, V, M at each end
        sig = abs(q[0]) / A + max(abs(q[2]), abs(q[5])) * (t / 2) / I
        sig_max = max(sig_max, sig)
    stiffness = force / delta
    first_yield = force * YIELD_PLA / sig_max if sig_max > 0 else 0.0
    return stiffness, first_yield


def warp_holes(dtype_rec, z):
    """Missing regions in the layer at height z for a warpage defect (same lift surface as defects.py):
    lift = value * (1 - d/R)^2, so material is missing where d < R * (1 - sqrt(z / value))."""
    v, R = dtype_rec["corner_lift_mm"], dtype_rec["lift_radius_mm"]
    if z >= v:
        return ()
    r = R * (1 - math.sqrt(z / v))
    return tuple(sg.Point(cx, cy).buffer(r, 64) for cx in (0, SIZE) for cy in (0, SIZE))


class BeamCase:
    """Beam-model judge for one repair case (same case format as agent/evaluate.py)."""
    def __init__(self, s):
        self.s = s
        self.g = load_graph(os.path.join(ROOT, s["base_graph"]))
        self.t0 = self.g["wall_thickness_mm"]
        self.h = s["layer_height_mm"]
        self.n_prefix = round(s["z_cut_mm"] / self.h)
        self.per_band = round(1.0 / self.h)
        self._cache = {}
        self.healthy = self.layer(self.t0)
        d = s["defect"]
        self.prefix = []
        for k in range(self.n_prefix):
            z = (k + 0.5) * self.h
            if d["type"] in ("under_extrusion", "over_extrusion") and d["z_range_mm"][0] <= z < d["z_range_mm"][1]:
                self.prefix.append(self.layer(d["wall_thickness_mm"]))
            elif d["type"] == "warpage" and z < d["corner_lift_mm"]:
                self.prefix.append(layer_response(self.g, self.t0, self.h, warp_holes(d, z)))
            else:                                    # healthy layer; layer shift also lands here (blind spot)
                self.prefix.append(self.healthy)

    def layer(self, t):
        t = round(t, 3)
        if t not in self._cache:
            self._cache[t] = layer_response(self.g, t, self.h)
        return self._cache[t]

    def score(self, fix):
        """Same output keys as agent/evaluate.py score(), but from the beam model."""
        layers = self.prefix + [self.layer(t) for t in fix["wall_thickness_mm"] for _ in range(self.per_band)]
        n_total = round(self.s["specimen_mm"][2] / self.h)
        assert len(layers) == n_total, (len(layers), n_total)
        k = sum(x[0] for x in layers) / (self.healthy[0] * n_total)
        # Two force estimates, neither checked against a crush test yet (review, 2026-11-07):
        #  - first_yield_ratio: all layers are squeezed by the same amount, so the part first yields
        #    when its weakest layer does. Cautious.
        #  - peak_force_ratio: each layer's own yield force added up, which assumes a layer keeps carrying
        #    load after it yields while the others catch up. Closer to a crush peak only if that holds.
        squeeze_at_yield = min(f / s for s, f in layers)
        healthy_squeeze = self.healthy[1] / self.healthy[0]
        fy = sum(s for s, f in layers) * squeeze_at_yield / (self.healthy[1] * n_total)
        p = sum(x[1] for x in layers) / (self.healthy[1] * n_total)
        assert abs(healthy_squeeze * self.healthy[0] - self.healthy[1]) < 1e-6 * self.healthy[1]
        return {"stiffness_ratio": round(k, 4), "error": round(abs(k - 1), 4),
                "first_yield_ratio": round(fy, 4),
                "peak_force_ratio": round(p, 4), "peak_error": round(abs(p - 1), 4)}


def healthy_part(g):
    """Whole healthy part (10 mm deep): stiffness N/mm and first-yield force N."""
    return layer_response(g, g["wall_thickness_mm"], depth=g["specimen_mm"][2])
