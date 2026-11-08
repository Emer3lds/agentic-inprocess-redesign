"""Hook (runs before Bash/PowerShell/Write): block deleting or emptying files.
Amber's rule: never delete files; ask her instead. Exit code 2 = block, and the message goes to the agent."""
import json, re, sys

d = json.load(sys.stdin)
tool, inp = d.get("tool_name", ""), d.get("tool_input", {})
msg = None
if tool in ("Bash", "PowerShell"):
    cmd = inp.get("command", "")
    pattern = (r"(^|[\s;&|(])(rm|rmdir|del|erase|rd|unlink|shred)\s|Remove-Item|Clear-Content|"
               r"git\s+rm\s|git\s+clean|os\.remove|os\.unlink|shutil\.rmtree|\.unlink\(|"
               r"(^|[;&|])\s*>\s*[\w./\-]+\s*$|Set-Content\s+\S+\s+(-Value\s+)?(''|\"\")")
    if re.search(pattern, cmd, re.I):
        msg = "Blocked: this command looks like it deletes or empties a file."
elif tool == "Write" and not inp.get("content", "").strip():
    msg = "Blocked: writing an empty file would erase its contents."
if msg:
    print(msg + " Amber's rule: never delete files. Tell Amber what should be deleted and why; she will do it.", file=sys.stderr)
    sys.exit(2)
