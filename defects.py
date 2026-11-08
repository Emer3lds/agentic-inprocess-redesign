"""
Inject printing defects into a lattice and export the result as one watertight STL.

The part is built as stacked Z bands (Z = print direction, 0 = print bed):
  normal walls outside the defect band, changed geometry inside it.
Bands are merged with manifold3d.

Defect types (see docs/week2_defects.md for where the numbers come from):
  under_extrusion : walls and end plates thinner inside the band
  over_extrusion  : walls and end plates thicker inside the band
  layer_shift     : everything above the shift height moved along X
  warpage         : corners of the bottom layers lifted off the bed
"""
import copy, os, sys
import numpy as np
import trimesh
import manifold3d
sys.path.insert(0, os.path.dirname(__file__))
from lattice import *

BAND_H = 1.0          # mm, height of an under/over-extrusion band (about 5 layers of 0.2 mm)
WARP_RADIUS = 15.0    # mm, how far from each corner the lift reaches

SEVERITY = {
    "under_extrusion": {"small": 1.08, "medium": 0.96, "severe": 0.84},   # wall thickness, mm
    "over_extrusion":  {"small": 1.32, "medium": 1.44, "severe": 1.56},   # wall thickness, mm
    "layer_shift":     {"small": 0.4,  "medium": 0.8,  "severe": 1.0},    # shift along X, mm (1.2 = wall thickness would leave walls touching edge to edge)
    "warpage":         {"small": 0.3,  "medium": 0.6,  "severe": 1.0},    # corner lift, mm
}


# ---------------------------------------------------------------- mesh helpers
def to_manifold(m):
    return manifold3d.Manifold(manifold3d.Mesh(
        vert_properties=np.asarray(m.vertices, dtype=np.float32),
        tri_verts=np.asarray(m.faces, dtype=np.uint32)))


def to_trimesh(man):
    # keep manifold3d's own vertex list: snapping nearly equal points together can turn tiny
    # slivers into false "not watertight" results
    mm = man.to_mesh()
    return trimesh.Trimesh(vertices=mm.vert_properties[:, :3], faces=mm.tri_verts, process=False)


def band(poly, z0, z1, dx=0.0):
    # close gaps thinner than 2 microns and drop extra points on straight edges, so bands
    # that meet at a plate corner do not leave pinch points in the merged solid
    poly = poly.buffer(1e-3, join_style="mitre").buffer(-1e-3, join_style="mitre").simplify(1e-4)
    m = polygon_to_mesh(poly, z0, z1)
    if dx: m.apply_translation([dx, 0, 0])
    return m


def union(meshes):
    out = to_manifold(meshes[0])
    for m in meshes[1:]:
        out = out + to_manifold(m)
    return to_trimesh(out)


# ---------------------------------------------------------------- defects
def inject(g, dtype, severity, z0=None):
    """Return (mesh, defect_record). z0 = bottom of the defect band in mm (not used for warpage)."""
    value = SEVERITY[dtype][severity]
    normal = graph_to_polygon(g)
    rec = {"type": dtype, "severity": severity, "xy_region": "whole layer"}

    if dtype in ("under_extrusion", "over_extrusion"):
        z1 = z0 + BAND_H
        # walls and end plates both change by the same flow ratio; grown plates stick out past y = 0 and 50
        ratio = value / g["wall_thickness_mm"]
        changed = graph_to_polygon(g, thickness_override=lambda e: value, plate_scale=ratio)
        parts = [band(changed, z0, z1)]
        if z0 > 0: parts.insert(0, band(normal, 0, z0))
        if z1 < SIZE_Z: parts.append(band(normal, z1, SIZE_Z))
        pb = g["plates"]["bottom"]
        rec.update(z_range_mm=[z0, z1], wall_thickness_mm=value, normal_wall_thickness_mm=g["wall_thickness_mm"],
                   plate_thickness_mm=round((pb[1] - pb[0]) * ratio, 3), normal_plate_thickness_mm=pb[1] - pb[0])
        return union(parts), rec

    if dtype == "layer_shift":
        parts = [band(normal, 0, z0), band(normal, z0, SIZE_Z, dx=value)]
        rec.update(z_range_mm=[z0, SIZE_Z], shift_mm=[value, 0.0], shift_height_mm=z0)
        return union(parts), rec

    if dtype == "warpage":
        # The bottom corners curl up off the bed. For straight-walled parts this is the same as
        # cutting away everything below a curved surface: lift = value at each corner, fading
        # to 0 at WARP_RADIUS. Layers above stay where the printer put them.
        corners = np.array([[0, 0], [SIZE_X, 0], [0, SIZE_Y], [SIZE_X, SIZE_Y]])
        def lift_surface(v):
            if v[2] < -0.5: return v                       # bottom of the cutter stays flat
            d = np.min(np.linalg.norm(corners - v[:2], axis=1))
            fade = max(0.0, 1 - d / WARP_RADIUS) ** 2
            return [v[0], v[1], value * fade - 1e-4]       # just under the bed where there is no lift
        cutter = manifold3d.Manifold.cube([SIZE_X + 2, SIZE_Y + 2, 1.0]).translate([-1, -1, -1.0])
        cutter = cutter.refine_to_length(0.5).warp(lift_surface)
        part = to_manifold(band(normal, 0, SIZE_Z)) - cutter
        rec.update(z_range_mm=[0.0, value], corner_lift_mm=value, lift_radius_mm=WARP_RADIUS)
        return to_trimesh(part), rec

    raise ValueError(dtype)


# ---------------------------------------------------------------- checks
def check_defect(mesh, rec, base_volume):
    info = check_mesh(mesh)
    z0, z1 = rec["z_range_mm"]
    region = trimesh.creation.box(bounds=[[-5, -5, z0], [SIZE_X + 5, SIZE_Y + 5, z1]])
    overlap = (to_manifold(mesh) ^ to_manifold(region)).volume()
    (x0, y0, zz0), (x1, y1, zz1) = info["bounds_mm"]
    # intended overhangs: a layer shift along X, and grown plates along Y for over-extrusion
    allowed_dx = rec.get("shift_mm", [0, 0])[0]
    allowed_dy = max(0.0, (rec.get("plate_thickness_mm", 0) - rec.get("normal_plate_thickness_mm", 0)) / 2)
    tol = 1e-3
    in_box = (x0 >= -tol and y0 >= -allowed_dy - tol and zz0 >= -tol and
              x1 <= SIZE_X + allowed_dx + tol and y1 <= SIZE_Y + allowed_dy + tol and zz1 <= SIZE_Z + tol)
    return {
        "one_piece": info["pieces"] == 1,
        "watertight": info["watertight"],
        "defect_on_structure": overlap > 0,
        "inside_box": in_box,
        "volume_change_pct": round(100 * (info["volume_mm3"] - base_volume) / base_volume, 2),
        "bounds_mm": info["bounds_mm"],
    }
