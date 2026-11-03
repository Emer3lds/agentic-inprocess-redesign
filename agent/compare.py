"""
Compare the AI agent's runs with the two baselines, case by case.

Run: python agent/compare.py out/runs/<experiment>.jsonl    (plain Python, no AI, instant)
Needs out/results/baselines.json (from python agent/baselines.py). If out/results/search.json exists
(python agent/search.py), the non-AI search at the agent's tool budget is shown too.
Works for agent v0 logs ("attempts") and v1 logs ("submissions", plus tool calls).
A "tie" is within TIE of the simple rule's error. Error = distance from 100% stiffness.
"""
import json, os, statistics, sys
from collections import Counter, defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIE = 0.005

runs = [json.loads(l) for l in open(sys.argv[1])]
base = {(b["case"], b["fixer"]): b for b in json.load(open(os.path.join(ROOT, "out", "results", "baselines.json")))}
by_case, seen, dupes = defaultdict(list), set(), 0
for r in runs:
    if (r["case"], r["run"]) in seen:      # the same run logged twice (two processes wrote at once): keep the first
        dupes += 1
        continue
    seen.add((r["case"], r["run"]))
    by_case[r["case"]].append(r)
if dupes:
    print(f"note: ignored {dupes} duplicate run(s), kept the first copy of each")

# No silent holes: every case needs the same number of runs, and every case must be there.
all_cases = {c for c, _ in base}
n_runs = max(r["run"] for r in runs)
missing = {c: n_runs - len(by_case.get(c, [])) for c in sorted(all_cases) if len(by_case.get(c, [])) < n_runs}
if missing:
    print(f"INCOMPLETE: {sum(missing.values())} of {n_runs * len(all_cases)} runs missing "
          f"({len(missing)} cases). Rerun the agent command to fill them in.")
    if "--partial" not in sys.argv:
        sys.exit("Not reporting on incomplete data. Add --partial to look anyway.")
    print("Showing partial results (--partial); do not use these as final numbers.\n")

search_path = os.path.join(ROOT, "out", "results", "search.json")
search = {}
if os.path.exists(search_path):
    sr = json.load(open(search_path))
    b = min(r["budget"] for r in sr)   # the matched budget (the agent's)
    search = {r["case"]: r for r in sr if r["budget"] == b}

tally, tally_search, attempts_used, fail_rules, tool_calls = Counter(), Counter(), Counter(), Counter(), []
print(f"{'case':38s} {'do nothing':>10s} {'rule':>7s}" + (f" {'search':>7s}" if search else "")
      + f" {'agent runs':>24s}  spread  vs rule" + ("  vs search" if search else ""))
for case, rs in by_case.items():
    dn, rule = base[(case, "do_nothing")], base[(case, "simple_rule")]
    errs = [r["error"] for r in rs]
    mean_err = statistics.mean(errs)
    verdict = "tie" if abs(mean_err - rule["error"]) <= TIE else ("WIN" if mean_err < rule["error"] else "loss")
    tally[verdict] += 1
    vs_search = ""
    if case in search:
        se = search[case]["error"]
        vs_search = "tie" if abs(mean_err - se) <= TIE else ("WIN" if mean_err < se else "loss")
        tally_search[vs_search] += 1
    for r in rs:
        attempts_used["fallback" if r["fallback_used"] else f"ok on attempt {r['n_attempts']}"] += 1
        if "n_tool_calls" in r:
            tool_calls.append(r["n_tool_calls"])
        for a in r.get("attempts", r.get("submissions", [])):
            for v in a["violations"]:
                fail_rules[v["rule"]] += 1
    agent = " ".join(f"{r['stiffness_ratio']:.1%}" + ("*" if r["fallback_used"] else "") for r in rs)
    spread = max(r["stiffness_ratio"] for r in rs) - min(r["stiffness_ratio"] for r in rs)
    same = len({tuple(r["final_fix"]["wall_thickness_mm"]) for r in rs}) == 1
    print(f"{case.replace('reentrant_', ''):38s} {dn['stiffness_ratio']:10.1%} {rule['stiffness_ratio']:7.1%}"
          + (f" {search[case]['stiffness_ratio']:7.1%}" if case in search else "")
          + f" {agent:>24s}  {spread:5.1%}{' same' if same else '     '}  {verdict:7s} {vs_search}")

print(f"\nagent vs simple rule (mean of runs, tie = within {TIE:.1%}): {dict(tally)}")
if search:
    print(f"agent vs non-AI search at the same budget: {dict(tally_search)}")
print(f"runs: {dict(attempts_used)}   (* = fell back to do nothing)")
if tool_calls:
    print(f"tool calls per run: mean {statistics.mean(tool_calls):.1f}, max {max(tool_calls)}")
print(f"rejected attempts by rule: {dict(fail_rules)}")
models = Counter(a.get("model_version") for r in runs for a in r.get("attempts", r.get("turns", [])))
print(f"model versions reported: {dict(models)}")
