"""Quick check that the pipeline still works (plain code, no AI, a few seconds).
Loads every repair case and scores 'do nothing' on each. Run it after code changes to confirm nothing broke.
Run: python agent/quick_check.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from evaluate import load_cases, check, score
from baselines import do_nothing

cases = load_cases()
assert len(cases) == 12, f"expected 12 cases, found {len(cases)}"
for c in cases:
    fix = do_nothing(c)
    assert check(c, fix) == [], f"{c.s['id']}: do-nothing fix rejected"
    s = score(c, fix)
    assert 0.5 < s["stiffness_ratio"] < 1.5, f"{c.s['id']}: odd stiffness {s['stiffness_ratio']}"
print(f"quick check ok: {len(cases)} cases load and score")
