"""Hook (runs after an edit to a .py file): quick check that the project still works.
Loads the 12 repair cases and scores 'do nothing' on each with the current scorer. Takes a few seconds.
If it fails, the error goes back to the agent so it fixes the code right away."""
import json, os, subprocess, sys

d = json.load(sys.stdin)
p = (d.get("tool_input", {}).get("file_path") or "").replace("\\", "/")
if not p.endswith(".py"):
    sys.exit(0)
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
r = subprocess.run([sys.executable, os.path.join(root, "agent", "quick_check.py")],
                   capture_output=True, text=True, timeout=120)
if r.returncode != 0:
    print("Quick check failed after this edit:\n" + (r.stdout + r.stderr)[-1500:], file=sys.stderr)
    sys.exit(2)
