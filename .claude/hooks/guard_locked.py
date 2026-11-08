"""Hook (runs before Edit/Write/Bash/PowerShell): block changes to locked files.
Locked: the FEA judge (fea/judge/) and the held-back test cases (out/scenarios/heldout/).
These score the agents, so an agent that could change them could improve its score without improving
its designs. Only Amber unlocks them (by editing LOCKED below)."""
import json, re, sys

LOCKED = ["fea/judge/", "out/scenarios/heldout/"]
d = json.load(sys.stdin)
tool, inp = d.get("tool_name", ""), d.get("tool_input", {})
norm = lambda s: s.replace("\\", "/")
hit = None
if tool in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
    p = norm(inp.get("file_path", "") or inp.get("notebook_path", ""))
    hit = next((L for L in LOCKED if L in p), None)
elif tool in ("Bash", "PowerShell"):
    cmd = norm(inp.get("command", ""))
    writes = re.search(r">|\b(mv|cp|move|copy|sed\s+-i|tee|touch|Set-Content|Out-File|Add-Content|Move-Item|Copy-Item|New-Item|git\s+checkout|git\s+restore)\b", cmd, re.I)
    if writes:
        hit = next((L for L in LOCKED if L in cmd), None)
if hit:
    print(f"Blocked: {hit} is locked (it scores the agents). Read it if you need to, but don't change it. "
          "If it really needs a change, write a decision brief for Amber in docs/open_decisions.md.", file=sys.stderr)
    sys.exit(2)
