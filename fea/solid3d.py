"""
3D solid model of a part: the planned judge (pipeline_diagrams.md section 9). Plain code, no AI.

What it does, in plain words:
  - gmsh turns the part into a solid volume and fills it with small 10-node tetrahedra
    (4-cornered pieces with a middle point on each edge). The solid comes from the STL (a closed
    triangle surface) or, for healthy parts, from the design graph (see mesh_part).
  - CalculiX solves how every piece moves when the bottom face (y = 0) is held still and the top
    face (y = 50) is pushed 0.01 mm toward y = 0. Both faces are also held in X and Z, as if glued
    to the test machine's plates.
  - Stiffness = total Y force on the top face / push, in N/mm.

Units: mm, N, MPa. Material values are placeholders (E from fea/beam.py, Poisson's ratio 0.35).
Axes: Z = print direction, Y = loading direction.
"""
import json, os, re, subprocess, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from beam import E_PLA

NU_PLA = 0.35          # placeholder Poisson's ratio for PLA
PUSH = 0.01            # mm, push of the top face along -Y
Y_TOP = 50.0           # mm, top face; bottom face is y = 0
Z_TOP = 10.0           # mm, part depth in Z
FACE_TOL = 1e-3        # mm, tolerance for picking nodes on the y = 0 and y = 50 faces
CCX = "C:/Users/amber/anaconda3/envs/fea/Library/bin/ccx.exe"
CCX_PATHS = ["C:/Users/amber/anaconda3/envs/fea/Library/bin",
             "C:/Users/amber/anaconda3/envs/fea/Library/mingw-w64/bin",
             "C:/Users/amber/anaconda3/envs/fea"]
OUT_DIR = os.path.join(ROOT, "out", "fea3d")


def _stl_solid(gmsh, stl_path):
    """STL route: split the triangle surface into flat patches at sharp edges, make them real
    surfaces, close them into a volume. Works for the hexagon; fails for the triangle and
    re-entrant STLs (see the note at mesh_part)."""
    gmsh.merge(stl_path)
    gmsh.model.mesh.classifySurfaces(40 * np.pi / 180, True, False, np.pi)
    gmsh.model.mesh.createGeometry()
    surfs = [s[1] for s in gmsh.model.getEntities(2)]
    gmsh.model.geo.addVolume([gmsh.model.geo.addSurfaceLoop(surfs)])
    gmsh.model.geo.synchronize()
    return None


def _graph_solid(gmsh, graph_path, depth=Z_TOP):
    """Graph route: the same 2D cross-section that built the STL (lattice.graph_to_polygon),
    as an exact flat face with the holes cut out, extruded 10 mm in Z. Returns its volume."""
    sys.path.insert(0, ROOT)
    import lattice
    poly = lattice.graph_to_polygon(json.load(open(graph_path)))
    occ = gmsh.model.occ
    def face(ring):
        c = np.array(ring.coords)[:-1]
        p = [occ.addPoint(x, y, 0) for x, y in c[:, :2]]
        return occ.addPlaneSurface([occ.addCurveLoop(
            [occ.addLine(p[i], p[(i + 1) % len(p)]) for i in range(len(p))])])
    outer = [(2, face(poly.exterior))]
    holes = [(2, face(r)) for r in poly.interiors]
    if holes:
        outer, _ = occ.cut(outer, holes)
    vols = [e for e in occ.extrude(outer, 0, 0, depth) if e[0] == 3]
    occ.synchronize()
    vol = sum(occ.getMass(3, v[1]) for v in vols)
    if abs(vol - poly.area * depth) > 1e-3 * poly.area * depth:
        raise RuntimeError(f"solid volume {vol:.1f} does not match the cross-section {poly.area * depth:.1f}")
    return vol


def mesh_part(path, size, half_z=False):
    """Part -> solid -> 10-node tetrahedra with largest piece size `size` mm.
    path: an STL (STL route) or a design graph <shape>_graph.json (graph route).
    Note: STLs made before 2026-11-12 had zero-thickness internal faces for the triangle and
    re-entrant, which the mesher rejects; fixed in lattice.polygon_to_mesh (E8 follow-up). The graph
    route builds the same solid from the design graph, for healthy parts only.
    Returns dict: tags (node ids), xyz (n x 3), conn (elements x 10, gmsh order), bounds, volume."""
    import gmsh
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        if half_z and not path.endswith(".json"):
            raise ValueError("half_z only for the graph route (healthy parts)")
        vol = (_graph_solid(gmsh, path, Z_TOP / 2 if half_z else Z_TOP) if path.endswith(".json")
               else _stl_solid(gmsh, path))
        gmsh.option.setNumber("Mesh.MeshSizeMax", size)
        gmsh.option.setNumber("Mesh.MeshSizeMin", 0.0)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)  # middle points stay on straight edges
        gmsh.model.mesh.generate(3)
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        et, _, enodes = gmsh.model.mesh.getElements(3)
        if 11 not in list(et):
            raise RuntimeError("gmsh made no 10-node tetrahedra")
        conn = enodes[list(et).index(11)].reshape(-1, 10).astype(np.int64)
    finally:
        gmsh.finalize()
    xyz = xyz.reshape(-1, 3)
    return {"tags": tags.astype(np.int64), "xyz": xyz, "conn": conn, "volume_mm3": vol,
            "bounds": [xyz.min(0).tolist(), xyz.max(0).tolist()]}


def write_inp(mesh, E, nu, push, path, y_top=Y_TOP, z_top=Z_TOP, hold_sides=True, sym_z=None):
    """CalculiX input: bottom face (y = 0) held in X, Y, Z; top face (y = y_top) moved -push in Y
    and held in X, Z (both faces glued to the machine's plates). hold_sides=False holds the faces
    only in Y (free to slide sideways; used for the tool check, where the exact answer is E*A/L).
    Asks only for the total reaction force on the top face."""
    tags, xyz, conn = mesh["tags"], mesh["xyz"], mesh["conn"]
    lo, hi = mesh["bounds"]
    if abs(lo[1]) > FACE_TOL or abs(hi[1] - y_top) > FACE_TOL or abs(lo[2]) > FACE_TOL \
            or abs(hi[2] - z_top) > FACE_TOL:
        raise ValueError(f"part does not span y 0..{y_top} and z 0..{z_top}: {lo} {hi}")
    used = np.unique(conn)
    keep = np.isin(tags, used)  # write only nodes that belong to a tetrahedron
    tags, xyz = tags[keep], xyz[keep]
    bot = tags[np.abs(xyz[:, 1]) < FACE_TOL]
    top = tags[np.abs(xyz[:, 1] - y_top) < FACE_TOL]
    ccx_conn = np.hstack([conn[:, :8], conn[:, 9:10], conn[:, 8:9]])  # gmsh -> CalculiX order
    with open(path, "w") as f:
        f.write("*NODE\n")
        np.savetxt(f, np.column_stack([tags, xyz]), fmt="%d,%.9g,%.9g,%.9g")
        f.write("*ELEMENT,TYPE=C3D10,ELSET=ALL\n")
        np.savetxt(f, np.column_stack([np.arange(1, len(conn) + 1), ccx_conn]), fmt="%d", delimiter=",")
        sets = [("BOT", bot), ("TOP", top)]
        if sym_z is not None:  # mirror plane of a half model: nodes there cannot move in Z
            sets.append(("SYM", tags[np.abs(xyz[:, 2] - sym_z) < FACE_TOL]))
        for name, ids in sets:
            f.write(f"*NSET,NSET={name}\n")
            np.savetxt(f, ids.reshape(-1, 1), fmt="%d")
        f.write(f"*MATERIAL,NAME=PLA\n*ELASTIC\n{E},{nu}\n*SOLID SECTION,ELSET=ALL,MATERIAL=PLA\n")
        if hold_sides:
            f.write("*BOUNDARY\nBOT,1,3,0\nTOP,1,1,0\nTOP,3,3,0\n")
        else:  # Y only, plus two bottom corner nodes to stop the part sliding or spinning
            on_bot = np.abs(xyz[:, 1]) < FACE_TOL
            c0 = tags[on_bot][np.argmin(np.linalg.norm(xyz[on_bot] - [lo[0], 0, lo[2]], axis=1))]
            c1 = tags[on_bot][np.argmin(np.linalg.norm(xyz[on_bot] - [hi[0], 0, lo[2]], axis=1))]
            f.write(f"*BOUNDARY\nBOT,2,2,0\n{c0},1,3,0\n{c1},3,3,0\n")
        if sym_z is not None:
            f.write("*BOUNDARY\nSYM,3,3,0\n")
        f.write(f"*STEP\n*STATIC\n*BOUNDARY\nTOP,2,2,{-push}\n"
                "*NODE PRINT,NSET=TOP,TOTALS=ONLY\nRF\n*END STEP\n")
    return {"n_bottom_nodes": int(len(bot)), "n_top_nodes": int(len(top))}


def run_ccx(job_dir, name):
    """Runs CalculiX on <job_dir>/<name>.inp. Returns the path of <name>.dat."""
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([p.replace("/", os.sep) for p in CCX_PATHS] + [env.get("PATH", "")])
    n = str(os.cpu_count() or 1)
    env["OMP_NUM_THREADS"] = n
    env["CCX_NPROC_EQUATION_SOLVER"] = n
    with open(os.path.join(job_dir, name + "_ccx.log"), "w") as log:
        r = subprocess.run([CCX, name], cwd=job_dir, env=env, stdout=log, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise RuntimeError(f"CalculiX failed (code {r.returncode}); see {name}_ccx.log")
    return os.path.join(job_dir, name + ".dat")


def read_force(dat_path):
    """Total reaction force (fx, fy, fz) on the top face, from the .dat file."""
    txt = open(dat_path).read()
    m = re.search(r"total force.*?\n\s*\n?\s*([-\d.Ee+]+)\s+([-\d.Ee+]+)\s+([-\d.Ee+]+)", txt)
    if not m:
        raise RuntimeError(f"no 'total force' in {dat_path}")
    return tuple(float(v) for v in m.groups())


def stiffness(path, size, name=None, E=E_PLA, nu=NU_PLA, y_top=Y_TOP, z_top=Z_TOP, hold_sides=True,
              reuse=False, half_z=False):
    """Whole chain: mesh, write input, run CalculiX, read force. Stiffness in N/mm.
    Files go to out/fea3d/<name>/. A short result.json is saved there; reuse=True returns it
    instead of running again.
    half_z=True (healthy parts from the graph only): models z 0..5 and holds the z = 5 mirror plane in
    Z, then doubles the force. Exact for a straight extrusion with these supports; about half the
    memory and time. Not for defect parts, which are not mirror-symmetric in Z."""
    base = os.path.splitext(os.path.basename(path))[0].replace("_graph", "")
    name = name or (f"{base}_h{size:g}" + ("_half" if half_z else "")).replace(".", "p")
    job_dir = os.path.join(OUT_DIR, name)
    res_path = os.path.join(job_dir, "result.json")
    if reuse and os.path.exists(res_path):
        return json.load(open(res_path))
    os.makedirs(job_dir, exist_ok=True)
    t0 = time.time()
    mesh = mesh_part(path, size, half_z)
    t_mesh = time.time() - t0
    faces = write_inp(mesh, E, nu, PUSH, os.path.join(job_dir, name + ".inp"), y_top,
                      z_top / 2 if half_z else z_top, hold_sides, z_top / 2 if half_z else None)
    mult = 2 if half_z else 1
    t1 = time.time()
    fx, fy, fz = read_force(run_ccx(job_dir, name))
    t_solve = time.time() - t1
    r = {"source": os.path.relpath(path, ROOT).replace(os.sep, "/"), "size_mm": size,
         "stiffness_N_per_mm": round(mult * abs(fy) / PUSH, 1), "half_z": half_z, "n_nodes": int(len(np.unique(mesh["conn"]))),
         "n_elements": int(len(mesh["conn"])), "seconds": round(time.time() - t0, 1),
         "mesh_seconds": round(t_mesh, 1), "solve_seconds": round(t_solve, 1),
         "force_N": [fx, fy, fz], "volume_mm3": mesh["volume_mm3"], "hold_sides": hold_sides,
         "job_dir": os.path.relpath(job_dir, ROOT).replace(os.sep, "/"), **faces}
    json.dump(r, open(res_path, "w"), indent=1)
    return r
