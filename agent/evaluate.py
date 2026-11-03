"""
Judge a proposed fix: a checker (is it allowed?) and a score (how good is it?).

A fix is the same format for every fixer (do nothing, simple rule, AI agent):
  {"wall_thickness_mm": [t1, t2, ...]}   one wall thickness per 1 mm band above the stop height,
                                          bottom band first. End plates stay as designed.
(Level 1 of decision D5: thickness only, the same for all walls in a band.)

Score, version 1 (decision D8): "formula" stiffness along Y (the load direction).
  - The layers are squeezed side by side, like springs in parallel, so the part's stiffness
    is the average of the layer stiffnesses.
  - A layer's stiffness grows with its lattice cross-section area to the power n
    (Gibson & Ashby): n = 3 for bending shapes (re-entrant, hexagon), n = 1 for the triangle.
    Area is used as a stand-in for wall thickness, so the printed part is judged by its actual
    geometry (sliced from the STL), not by the defect label.
  - Known blind spots: it cannot see layer shift (each layer keeps its area) or how well layers
    are bonded, and it scores stiffness only, not peak force.
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import manifold3d
import trimesh
from defects import *

BAND_H = 1.0              # mm, height of one band the fixer controls
T_MIN, T_MAX = 0.8, 2.0   # mm, 2 nozzle lines; cells must stay open (D7)
MAX_STEP_UP = 0.4         # mm, a wall may grow at most 0.2 mm per side from one layer to the next (overhang)
BUDGET_TOL = 0.01         # fraction over budget allowed
BUDGET_MODE = "remaining" # "remaining": original plastic above the cut (proposal 5.4); "total": whole part = healthy part (D7)
EXPONENT = {"reentrant": 3, "hexagon": 3, "triangle": 1}
# Peak force (collapse strength), second measure (D10): Gibson & Ashby plastic collapse goes with
# relative density squared for bending shapes, to the power 1 for stretching shapes (triangle).
STRENGTH_EXPONENT = {"reentrant": 2, "hexagon": 2, "triangle": 1}


def lattice_area(cs):
    """Area of a cross-section without the end plates (the plates do not bend)."""
    keep = manifold3d.CrossSection.square([SIZE_X + 10, SIZE_Y - 2 * PLATE_T]).translate([-5, PLATE_T])
    return (cs ^ keep).area()


class Case:
    """Everything the judge needs about one scenario, computed once."""
    def __init__(self, s):
        self.s = s
        self.g = load_graph(os.path.join(ROOT, s["base_graph"]))
        self.z_cut = s["z_cut_mm"]
        self.n_bands = round(s["remaining_height_mm"] / BAND_H)
        self.n = EXPONENT[s["shape"]]
        self._area_cache = {}
        self.a0 = self.band_lattice_area(self.g["wall_thickness_mm"])
        self.full_area0 = graph_to_polygon(self.g).area
        # the printed part, one slice through the middle of each 0.2 mm layer
        prefix = to_manifold(trimesh.load(os.path.join(ROOT, s["prefix_stl"])))
        n_layers = round(self.z_cut / s["layer_height_mm"])
        h = s["layer_height_mm"]
        self.prefix_layer_areas = [lattice_area(prefix.slice((k + 0.5) * h)) for k in range(n_layers)]
        self.top_wall_t = s["defect"].get("wall_thickness_mm", self.g["wall_thickness_mm"])
        healthy_total = self.full_area0 * SIZE_Z
        self.budget = {"remaining": s["material_budget_mm3"],
                       "total": round(healthy_total - s["prefix_volume_mm3"], 1)}

    def band_lattice_area(self, t):
        """Lattice area of one layer printed with all walls at thickness t (end plates normal)."""
        t = round(t, 3)
        if t not in self._area_cache:
            poly = graph_to_polygon(self.g, thickness_override=lambda e: t)
            self._area_cache[t] = poly.intersection(shapely.geometry.box(-5, PLATE_T, SIZE_X + 5, SIZE_Y - PLATE_T)).area
        return self._area_cache[t]

    def band_full_area(self, t):
        return self.band_lattice_area(t) + (self.full_area0 - self.a0)


def check(case, fix):
    """Return a list of rule violations. Empty list = the fix is allowed.
    Reports every problem at once (not just the first), because this list is the agent's feedback."""
    v = []
    ts = fix.get("wall_thickness_mm")
    if (not isinstance(ts, list) or len(ts) != case.n_bands
            or not all(isinstance(t, (int, float)) and not isinstance(t, bool) for t in ts)):
        return [{"rule": "format", "detail": f"need a list of {case.n_bands} numbers, wall thicknesses in mm (one per 1 mm band above {case.z_cut} mm)"}]
    for i, t in enumerate(ts):
        if not (T_MIN <= t <= T_MAX):
            v.append({"rule": "thickness_range", "detail": f"band {i + 1}: {t} mm, allowed {T_MIN} to {T_MAX} mm"})
    below = [case.top_wall_t] + ts[:-1]
    for i, (tb, t) in enumerate(zip(below, ts)):
        if t - tb > MAX_STEP_UP + 1e-9:
            v.append({"rule": "overhang", "detail": f"band {i + 1}: {t} mm sits on {tb} mm walls, may grow at most {MAX_STEP_UP} mm"})
    used = material_used(case, fix)
    budget = case.budget[BUDGET_MODE]
    if used > budget * (1 + BUDGET_TOL):
        v.append({"rule": "material_budget", "detail": f"uses {used:.0f} mm3, budget {budget:.0f} mm3 (+{BUDGET_TOL:.0%})"})
    return v


def material_used(case, fix):
    return sum(case.band_full_area(t) * BAND_H for t in fix["wall_thickness_mm"])


def layer_area_ratios(case, fix):
    """Lattice area of every 0.2 mm layer (printed, then proposed) relative to a healthy layer."""
    per_band = round(BAND_H / case.s["layer_height_mm"])
    ratios = [a / case.a0 for a in case.prefix_layer_areas]
    for t in fix["wall_thickness_mm"]:
        ratios += [case.band_lattice_area(t) / case.a0] * per_band
    return ratios


def score(case, fix):
    """Stiffness along Y as a fraction of the defect-free part (1.0 = fully recovered); the main measure.
    Also reports a peak-force estimate (same layers-in-parallel idea, strength exponent), which the
    agent's tool does not report, so it is a check the agent cannot aim at (D10)."""
    ratios = layer_area_ratios(case, fix)
    stiffness = sum(r ** case.n for r in ratios) / len(ratios)
    peak = sum(r ** STRENGTH_EXPONENT[case.s["shape"]] for r in ratios) / len(ratios)
    return {"stiffness_ratio": round(stiffness, 4), "error": round(abs(stiffness - 1), 4),
            "peak_force_ratio": round(peak, 4), "peak_error": round(abs(peak - 1), 4),
            "material_mm3": round(material_used(case, fix), 1)}


def load_cases(path=os.path.join(ROOT, "out", "scenarios", "scenarios.json")):
    return [Case(s) for s in json.load(open(path))]
