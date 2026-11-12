"""
Experiment E8: checks of the 3D solid model (fea/solid3d.py) on healthy parts. Plain code, no AI.
Design: docs/pipeline_diagrams.md section 9.

  1. Tool check: a solid 10 x 10 x 10 mm block.
     a. Faces free to slide sideways: exact answer E*A/L = 3500 * 100 / 10 = 35,000 N/mm.
     b. Faces glued (held in X and Z, as for the lattices): somewhat higher than 35,000, because
        the glued faces stop the block from bulging sideways.
  2. Piece-size check on the healthy re-entrant part: use the largest piece size whose stiffness
     is within 2% of the next smaller size, and stays within 2% at every smaller size tried. Run as a half model (z 0..5 with the z = 5 mirror plane
     held in Z; exact for a straight extrusion, about half the memory). This laptop has about 6 GB
     of memory, and the full model at 0.6 mm would need most of it. The full model is also run at
     the sizes given by --full-sizes, to show half and full give close answers.
  3. Healthy hexagon, re-entrant, triangle at the chosen size, against the beam model and the
     formula (numbers from out/results/e7_beam_checks.json). No pass mark.
  Extra: the hexagon, the one STL the mesher accepts, built both from its STL and from its design
     graph, to show the two ways of building the solid give the same answer.

Run: python fea/e8_solid_checks.py [--sizes 1.2 0.8 0.6] [--size 0.8] [--rerun]
Finished runs are reused from out/fea3d/<run>/result.json unless --rerun is given.
Writes out/results/e8_solid_checks.json.
"""
import argparse, json, os, sys
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import solid3d as s3

BASE = os.path.join(ROOT, "out", "base")
SHAPES = ["hexagon", "reentrant", "triangle"]
EXACT_BLOCK = s3.E_PLA * 10 * 10 / 10   # E * A / L, N/mm
SETTLED = 2.0                            # % change between piece sizes that counts as settled


def pct(a, b):
    return round(100.0 * (a - b) / b, 1)


def keep(r):
    return {k: r[k] for k in ("stiffness_N_per_mm", "n_elements", "n_nodes", "seconds")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=float, nargs="+", default=[1.2, 0.8, 0.6])
    ap.add_argument("--size", type=float, default=None, help="piece size for check 3 if check 2 is not settled")
    ap.add_argument("--full-sizes", type=float, nargs="*", default=[1.2, 0.8])
    ap.add_argument("--rerun", action="store_true")
    a = ap.parse_args()
    reuse = not a.rerun
    out = {"material": {"E_MPa": s3.E_PLA, "poisson": s3.NU_PLA}, "push_mm": s3.PUSH,
           "route": "graph (lattice.graph_to_polygon extruded in Z); see fea/solid3d.py mesh_part"}

    # 1. Tool check
    block = os.path.join(s3.OUT_DIR, "block", "block.stl")
    if not os.path.exists(block):
        os.makedirs(os.path.dirname(block), exist_ok=True)
        trimesh.creation.box(extents=[10, 10, 10]).apply_translation([5, 5, 5]).export(block)
    free = s3.stiffness(block, 1.0, name="block_free", y_top=10, z_top=10, hold_sides=False, reuse=reuse)
    glued = s3.stiffness(block, 1.0, name="block_glued", y_top=10, z_top=10, reuse=reuse)
    out["check1_block"] = {"exact_free_N_per_mm": EXACT_BLOCK,
                           "free": {**keep(free), "diff_pct": pct(free["stiffness_N_per_mm"], EXACT_BLOCK)},
                           "glued": {**keep(glued), "diff_pct": pct(glued["stiffness_N_per_mm"], EXACT_BLOCK)}}
    print(f"1. Block: free {free['stiffness_N_per_mm']:.0f} N/mm ({out['check1_block']['free']['diff_pct']:+}% vs 35,000), "
          f"glued {glued['stiffness_N_per_mm']:.0f} N/mm ({out['check1_block']['glued']['diff_pct']:+}%)")

    # 2. Piece-size check
    g = lambda sh: os.path.join(BASE, f"{sh}_graph.json")
    sizes = sorted(a.sizes, reverse=True)
    runs = [s3.stiffness(g("reentrant"), h, reuse=reuse, half_z=True) for h in sizes]
    rows, chosen = [], None
    for i, (h, r) in enumerate(zip(sizes, runs)):
        row = {"size_mm": h, **keep(r)}
        if i + 1 < len(runs):
            row["change_to_next_smaller_pct"] = pct(r["stiffness_N_per_mm"], runs[i + 1]["stiffness_N_per_mm"])
        rows.append(row)
    # chosen: the largest size from which every further step to a smaller size changes the answer by
    # at most 2% (so a small change followed by a bigger one does not count as settled)
    for i in range(len(rows) - 1):
        if all(abs(x["change_to_next_smaller_pct"]) <= SETTLED for x in rows[i:-1]):
            chosen = rows[i]["size_mm"]; break
    for row in rows:
        h = row["size_mm"]; r = row
        print(f"2. Re-entrant (half model), size {h} mm: {r['stiffness_N_per_mm']:.1f} N/mm, {r['n_elements']} elements, "
              f"{r['seconds']} s" + (f", change to next smaller {row['change_to_next_smaller_pct']:+}%"
                                     if "change_to_next_smaller_pct" in row else ""))
    full = []
    for h in a.full_sizes:
        r = s3.stiffness(g("reentrant"), h, reuse=reuse)
        full.append({"size_mm": h, **keep(r)})
        print(f"   Re-entrant (full model), size {h} mm: {r['stiffness_N_per_mm']:.1f} N/mm, "
              f"{r['n_elements']} elements, {r['seconds']} s")
    out["check2_piece_size"] = {"model": "half (z 0..5, mirror plane held in Z, force doubled)",
                                "rows": rows, "full_model_rows": full, "settled_within_pct": SETTLED,
                                "chosen_size_mm": chosen}
    size3 = chosen if chosen is not None else a.size
    print(f"   chosen size: {chosen if chosen is not None else 'none settled yet'}"
          + ("" if chosen is not None else f"; check 3 uses {size3} mm (provisional)"))

    # 3. Healthy parts against the beam model and the formula
    if size3 is not None:
        e7 = {r["shape"]: r for r in json.load(open(os.path.join(ROOT, "out", "results", "e7_beam_checks.json")))
              ["check2_healthy_vs_formula"]}
        rows = []
        for sh in SHAPES:
            r = s3.stiffness(g(sh), size3, reuse=reuse, half_z=True)
            k, b, f = r["stiffness_N_per_mm"], e7[sh]["beam_N_per_mm"], e7[sh]["formula_N_per_mm"]
            rows.append({"shape": sh, **keep(r), "beam_N_per_mm": b, "formula_N_per_mm": f,
                         "beam_vs_3d_pct": pct(b, k), "formula_vs_3d_pct": pct(f, k)})
            print(f"3. {sh}: 3D {k:.0f} N/mm ({r['n_elements']} elements, {r['seconds']} s); "
                  f"beam {b} ({pct(b, k):+}% vs 3D); formula {f} ({pct(f, k):+}% vs 3D)")
        out["check3_healthy"] = {"size_mm": size3, "provisional": chosen is None, "rows": rows}

    # Extra: STL route vs graph route on the hexagon
    h = 1.2
    via_stl = s3.stiffness(os.path.join(BASE, "hexagon.stl"), h, name="hexagon_stl_h1p2", reuse=reuse)
    via_graph = s3.stiffness(g("hexagon"), h, reuse=reuse)
    out["extra_hexagon_routes"] = {"size_mm": h, "stl": keep(via_stl), "graph": keep(via_graph),
                                   "diff_pct": pct(via_stl["stiffness_N_per_mm"], via_graph["stiffness_N_per_mm"])}
    print(f"Extra: hexagon at {h} mm, from STL {via_stl['stiffness_N_per_mm']:.1f}, from graph "
          f"{via_graph['stiffness_N_per_mm']:.1f} N/mm ({out['extra_hexagon_routes']['diff_pct']:+}%)")

    path = os.path.join(ROOT, "out", "results", "e8_solid_checks.json")
    json.dump(out, open(path, "w"), indent=1)
    print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
