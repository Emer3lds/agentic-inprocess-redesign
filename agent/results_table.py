"""
Build the results table for an experiment from the logs, so no number is typed by hand.

Run: python agent/results_table.py out/runs/<agent v0 log>.jsonl out/runs/<agent v1 log>.jsonl out/results/<name>.md
(plain Python, no AI, instant). Agent values are the mean of their runs. Error = distance from 100%, in percentage points.
A tie means the two mean errors are within TIE of each other, as in compare.py.
"""
import json, os, statistics as st, sys
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIE = 0.005


def load_runs(path):
    runs, seen = defaultdict(list), set()
    for line in open(path):
        r = json.loads(line)
        if (r["case"], r["run"]) not in seen:
            seen.add((r["case"], r["run"]))
            runs[r["case"]].append(r)
    return runs


a0, a1 = load_runs(sys.argv[1]), load_runs(sys.argv[2])
base = {(b["case"], b["fixer"]): b for b in json.load(open(os.path.join(ROOT, "out", "results", "baselines.json")))}
search = {(r["case"], r["budget"]): r for r in json.load(open(os.path.join(ROOT, "out", "results", "search.json")))}
cases = list(a0)
fixed = {"Do nothing": lambda c: base[(c, "do_nothing")], "Simple rule": lambda c: base[(c, "simple_rule")],
         "Search, 10 uses": lambda c: search[(c, 10)], "Search, 200 uses": lambda c: search[(c, 200)]}


def mean(runs, c, key):
    return st.mean(r[key] for r in runs[c])


def vs(a_err, b_err):
    tally = {"wins": 0, "ties": 0, "losses": 0}
    for c in cases:
        d = a_err(c) - b_err(c)
        tally["ties" if abs(d) <= TIE else "wins" if d < 0 else "losses"] += 1
    return tally


out = ["| Case | Do nothing | Simple rule | Search, 10 uses | Agent, no calculator | Agent, calculator |", "|---|---|---|---|---|---|"]
for c in cases:
    out.append(f"| {c.replace('reentrant_', '').replace('_medium', '').replace('_', ' ')} | "
               f"{base[(c, 'do_nothing')]['stiffness_ratio']:.1%} | {base[(c, 'simple_rule')]['stiffness_ratio']:.1%} | "
               f"{search[(c, 10)]['stiffness_ratio']:.1%} | {mean(a0, c, 'stiffness_ratio'):.1%} | {mean(a1, c, 'stiffness_ratio'):.1%} |")
out += ["", "| Method | Average stiffness error | Average peak-force error |", "|---|---|---|"]
for name, f in fixed.items():
    out.append(f"| {name} | {st.mean(f(c)['error'] for c in cases):.2%} | {st.mean(f(c)['peak_error'] for c in cases):.2%} |")
for name, runs in (("Agent, no calculator", a0), ("Agent, calculator", a1)):
    out.append(f"| {name} | {st.mean(mean(runs, c, 'error') for c in cases):.2%} | {st.mean(mean(runs, c, 'peak_error') for c in cases):.2%} |")
err1 = lambda c: mean(a1, c, "error")
out += ["", "Agent with calculator, case by case (tie = within 0.5 points):",
        f"- vs simple rule: {vs(err1, lambda c: base[(c, 'simple_rule')]['error'])}",
        f"- vs search, 10 uses: {vs(err1, lambda c: search[(c, 10)]['error'])}",
        f"- vs agent without calculator: {vs(err1, lambda c: mean(a0, c, 'error'))}"]
damaged = [r["n_tool_calls"] for c in cases if "extrusion" in c for r in a1[c]]
other = [r["n_tool_calls"] for c in cases if "extrusion" not in c for r in a1[c]]
out.append(f"- calculator uses per run: {st.mean(damaged + other):.1f} overall, {st.mean(damaged):.1f} on under/over-extrusion, {st.mean(other):.1f} on layer shift/warpage")
open(sys.argv[3], "w", encoding="utf8").write("\n".join(out) + "\n")
print("\n".join(out))
