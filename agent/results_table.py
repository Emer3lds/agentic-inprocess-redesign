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


# LaTeX versions for the paper, written to paper/tables/ so the paper's numbers always come from the logs.
def pct(x, d=1):
    return f"{100 * x:.{d}f}" + r"\%"


TEX = os.path.join(os.path.dirname(ROOT), "paper", "tables")   # the paper has its own repo, next to this one
os.makedirs(TEX, exist_ok=True)
rows = [r"\begin{tabular}{lrrrrr}", r"\toprule", r"Case & Do nothing & Simple rule & Search (10) & Agent, no calc. & Agent, calc. \\", r"\midrule"]
for c in cases:
    name = c.replace("reentrant_", "").replace("_medium_z", " ").replace("_", " ") + r"\%"
    rows.append(f"{name} & {pct(base[(c, 'do_nothing')]['stiffness_ratio'])} & {pct(base[(c, 'simple_rule')]['stiffness_ratio'])} & "
                f"{pct(search[(c, 10)]['stiffness_ratio'])} & {pct(mean(a0, c, 'stiffness_ratio'))} & {pct(mean(a1, c, 'stiffness_ratio'))} \\\\")
rows += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(TEX, "e6_per_case.tex"), "w", encoding="utf8").write("\n".join(rows) + "\n")

six = [c for c in cases if "extrusion" in c]


def avg(f, key, group):
    return st.mean(f(c, key) for c in group)


methods = [(n, lambda c, k, f=f: f(c)[k]) for n, f in fixed.items()] + [
    ("Agent, no calculator", lambda c, k: mean(a0, c, k)), ("Agent, calculator", lambda c, k: mean(a1, c, k))]
rows = [r"\begin{tabular}{lrrrr}", r"\toprule", r"& \multicolumn{2}{c}{All 12 cases} & \multicolumn{2}{c}{6 extrusion cases} \\",
        r"Method & Stiffness & Peak force & Stiffness & Peak force \\", r"\midrule"]
for n, f in methods:
    rows.append(f"{n} & {pct(avg(f, 'error', cases), 2)} & {pct(avg(f, 'peak_error', cases), 2)} & {pct(avg(f, 'error', six), 2)} & {pct(avg(f, 'peak_error', six), 2)} \\\\")
rows += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(TEX, "e6_summary.tex"), "w", encoding="utf8").write("\n".join(rows) + "\n")

# Which prompt produced which results, plus the exact prompts, for the paper.
e5 = load_runs(os.path.join(ROOT, "out", "runs", "e5_v1_full.jsonl"))
rows = [r"\begin{tabular}{llllrr}", r"\toprule",
        r"Prompt & Agent & Model & Long reasoning & All 12 cases & 6 extrusion cases \\", r"\midrule"]
for prompt, agent, model, reasoning, runs in (("v1", "No calculator", "Gemini 3.6 Flash", "On", e5),
                                              ("v1", "No calculator", "Nemotron 3 Ultra", "Off", a0),
                                              (r"v2\_tools", "Calculator", "Nemotron 3 Ultra", "Off", a1)):
    rows.append(f"{prompt} & {agent} & {model} & {reasoning} & {pct(st.mean(mean(runs, c, 'error') for c in cases), 2)} & {pct(st.mean(mean(runs, c, 'error') for c in six), 2)} \\\\")
rows += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(TEX, "prompts.tex"), "w", encoding="utf8").write("\n".join(rows) + "\n")
PROMPTS = os.path.join(os.path.dirname(ROOT), "paper", "prompts")
os.makedirs(PROMPTS, exist_ok=True)
for name in ("v1.md", "v1_retry.md", "v2_tools.md"):
    text = open(os.path.join(HERE_PROMPTS := os.path.join(ROOT, "agent", "prompts"), name), encoding="utf8").read()
    open(os.path.join(PROMPTS, name.replace(".md", ".txt")), "w", encoding="utf8").write(text)
