"""
Experiment E10: cross-check our beam model (fea/beam.py) against OpenSeesPy. Plain code, no AI.

Our beam model is our own numpy code. OpenSeesPy is a widely used structural-engineering package.
Both solve exactly the same beams (same points, walls, thicknesses and held points), so any
difference beyond rounding would mean a bug in our code. This checks the solver, not whether
beams are the right model of the part (that is E8 and E9).

Needs Python 3.12 (OpenSeesPy's Windows build), so run it with the separate environment:
    C:/Users/amber/anaconda3/envs/opensees/python.exe fea/opensees_check.py
Writes out/results/e10_opensees_check.json.
"""
import json, math, os, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import beam
import openseespy.opensees as ops


def opensees_layer(g, thickness, depth, delta=0.01):
    """Same beams and supports as beam.layer_response (plates='clamped'), solved by OpenSeesPy."""
    segs, y0, y1 = beam._wall_segments(g, thickness)
    nodes, index = [], {}
    def nid(p):                                   # same point merging as beam.layer_response
        key = (round(p[0], 5), round(p[1], 5))
        if key not in index:
            index[key] = len(nodes); nodes.append(key)
        return index[key]
    elems = [(nid(a), nid(b), t) for a, b, t in segs]
    on_plate = lambda k: abs(nodes[k][1] - y0) < beam.TOL or abs(nodes[k][1] - y1) < beam.TOL
    # wall pieces not connected to either plate carry no load; our numpy code handles them with a
    # tiny extra stiffness, OpenSees would stop on them, so they are left out here
    nbr = defaultdict(set)
    for i, j, _ in elems:
        nbr[i].add(j); nbr[j].add(i)
    keep, stack = set(), [k for k in range(len(nodes)) if on_plate(k)]
    while stack:
        k = stack.pop()
        if k not in keep:
            keep.add(k); stack.extend(nbr[k])
    ops.wipe(); ops.model("basic", "-ndm", 2, "-ndf", 3)
    for k in keep:
        ops.node(k + 1, *nodes[k])
    ops.geomTransf("Linear", 1)
    n_el = 0
    for i, j, t in elems:
        if i in keep and j in keep:
            n_el += 1
            ops.element("elasticBeamColumn", n_el, i + 1, j + 1, depth * t, beam.E_PLA, depth * t ** 3 / 12.0, 1)
    top = [k for k in keep if abs(nodes[k][1] - y1) < beam.TOL]
    for k in keep:
        if abs(nodes[k][1] - y0) < beam.TOL:
            ops.fix(k + 1, 1, 1, 1)
        elif k in top:
            ops.fix(k + 1, 1, 0, 1)               # top plate: no sliding or turning, Y is pushed
    ops.timeSeries("Constant", 1); ops.pattern("Plain", 1, 1)
    for k in top:
        ops.sp(k + 1, 2, -delta)
    ops.constraints("Transformation"); ops.numberer("RCM"); ops.system("UmfPack")
    ops.test("NormDispIncr", 1e-12, 10); ops.algorithm("Linear"); ops.integrator("LoadControl", 1.0)
    ops.analysis("Static")
    assert ops.analyze(1) == 0, "OpenSees analysis failed"
    ops.reactions()
    force = -sum(ops.nodeReaction(k + 1, 2) for k in top)
    return force / delta, n_el


if __name__ == "__main__":
    rows = []
    for shape in ["hexagon", "reentrant", "triangle"]:
        g = beam.load_graph(os.path.join(ROOT, "out", "base", f"{shape}_graph.json"))
        depth = g["specimen_mm"][2] if len(g["specimen_mm"]) > 2 else 10.0
        mixed = {e["id"]: (0.96 if e["id"] % 2 == 0 else 1.44) for e in g["edges"]}
        for label, t in [("healthy, 1.2 mm walls", g["wall_thickness_mm"]),
                         ("mixed walls, 0.96 / 1.44 mm", mixed)]:
            ours, _ = beam.layer_response(g, t, depth=depth)
            theirs, n_el = opensees_layer(g, t, depth)
            rows.append({"shape": shape, "walls": label, "beam_py_N_per_mm": round(ours, 3),
                         "opensees_N_per_mm": round(theirs, 3), "elements": n_el,
                         "diff_pct": round(100 * (ours - theirs) / theirs, 4)})
            print(f"{shape:10s} {label:28s} ours {ours:9.2f}  OpenSees {theirs:9.2f}  diff {rows[-1]['diff_pct']:+.4f}%")
    os.makedirs(os.path.join(ROOT, "out", "results"), exist_ok=True)
    json.dump({"rows": rows, "max_abs_diff_pct": max(abs(r["diff_pct"]) for r in rows)},
              open(os.path.join(ROOT, "out", "results", "e10_opensees_check.json"), "w"), indent=1)
    print("largest difference:", max(abs(r["diff_pct"]) for r in rows), "%")
