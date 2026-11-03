"""
Agent version 0: one AI model in a propose -> check -> retry loop (proposal sections 7.3 and 8.1).

  1. Fill the prompt template with the case's facts and ask the model for a fix.
  2. The checker (evaluate.check) judges it. The agent never sees the score (decision A).
  3. If rejected, send the checker's reasons back and ask again, up to MAX_ATTEMPTS in total.
  4. If no attempt is allowed, use the fallback (do nothing). The failure still counts.
Every attempt is logged: prompt version, model, full text sent, raw reply, parsed fix, checker result.

Run: python agent/agent_v0.py --cases z10 --runs 1    (uses the AI; needs GEMINI_API_KEY)
Writes one line per run to out/runs/<experiment>.jsonl and prints one line per run.
"""
import argparse, datetime, json, os, re, sys, time, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from evaluate import *
from baselines import do_nothing
import llm

MAX_ATTEMPTS = 3   # proposal 7.3: fixed attempt limit, then a predefined fallback (decision C)
MAX_SKIPS_IN_A_ROW = 2   # one failed run may be a hiccup; two in a row means the service is down, so stop


def load_prompt(version):
    d = os.path.join(HERE, "prompts")
    return open(os.path.join(d, f"{version}.md")).read(), open(os.path.join(d, f"{version}_retry.md")).read()


def fill(template, slots):
    """Replace {name} for known slots only, so the JSON braces in the prompt stay as written."""
    return re.sub(r"\{(\w+)\}", lambda m: str(slots[m.group(1)]) if m.group(1) in slots else m.group(0), template)


def slots_for(case):
    s = case.s
    return {"shape": s["shape"].replace("reentrant", "re-entrant"), "total_height_mm": s["specimen_mm"][2],
            "nominal_t": case.g["wall_thickness_mm"], "defect_type": s["defect"]["type"].replace("_", " "),
            "defect_start_mm": s["defect"]["z_range_mm"][0], "z_cut_mm": case.z_cut,
            "top_wall_t": case.top_wall_t, "remaining_height_mm": s["remaining_height_mm"], "n_bands": case.n_bands}


def parse(text):
    try:
        d = json.loads(text)
        return {"wall_thickness_mm": d.get("wall_thickness_mm")}, d.get("reasoning"), None
    except (json.JSONDecodeError, AttributeError) as e:
        return None, None, f"could not read the answer as JSON: {e}"


def run_agent(case, prompt_version="v1", model=llm.DEFAULT_MODEL):
    template, retry_template = load_prompt(prompt_version)
    messages = [{"role": "user", "text": fill(template, slots_for(case))}]
    attempts, t0 = [], time.time()
    for k in range(1, MAX_ATTEMPTS + 1):
        reply, meta = llm.chat(messages, model=model)
        fix, reasoning, parse_error = parse(reply)
        violations = check(case, fix) if fix else [{"rule": "format", "detail": parse_error}]
        attempts.append({"attempt": k, "sent": messages[-1]["text"], "reply": reply, "reasoning": reasoning,
                         "fix": fix, "violations": violations, **meta})
        if not violations:
            break
        messages += [{"role": "model", "text": reply},
                     {"role": "user", "text": fill(retry_template, {"violations": "; ".join(f"{v['rule']}: {v['detail']}" for v in violations)})}]
    accepted = not attempts[-1]["violations"]
    final = attempts[-1]["fix"] if accepted else do_nothing(case)
    return {"case": case.s["id"], "prompt_version": prompt_version, "model": model,
            "accepted": accepted, "n_attempts": len(attempts), "fallback_used": not accepted,
            "final_fix": final, "final_violations": check(case, final), **score(case, final),
            "decision_seconds": round(time.time() - t0, 1), "attempts": attempts}


def main(run_fn=None, default_prompt="v1"):
    """Command line shared by every agent version: run_fn(case, prompt_version, model) -> result dict."""
    run_fn = run_fn or run_agent
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="", help="only cases whose id contains this text")
    ap.add_argument("--runs", type=int, default=1, help="repeat each case this many times (answers vary)")
    ap.add_argument("--prompt", default=default_prompt)
    ap.add_argument("--model", default=llm.DEFAULT_MODEL)
    ap.add_argument("--experiment", default=None, help="log name; default is a timestamp")
    a = ap.parse_args()
    cases = [c for c in load_cases() if a.cases in c.s["id"]]
    name = a.experiment or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(ROOT, "out", "runs")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.jsonl")
    done = {(d["case"], d["run"]) for d in map(json.loads, open(path))} if os.path.exists(path) else set()
    print(f"{len(cases)} cases x {a.runs} runs, prompt {a.prompt}, model {a.model} -> out/runs/{name}.jsonl"
          + (f" (resuming: {len(done)} runs already logged)" if done else ""))
    skips_in_a_row = 0
    with open(path, "a") as f:
        for case in cases:
            for r in range(1, a.runs + 1):
                if (case.s["id"], r) in done:
                    continue
                try:
                    res = {"experiment": name, "run": r, "time": datetime.datetime.now().isoformat(timespec="seconds"),
                           **run_fn(case, a.prompt, a.model)}
                except urllib.error.HTTPError as e:   # service down: skip; rerunning the same command fills the gap
                    print(f"{case.s['id']:38s} run {r}  SKIPPED (model service error {e.code}); rerun to fill in")
                    skips_in_a_row += 1
                    if skips_in_a_row >= MAX_SKIPS_IN_A_ROW:
                        sys.exit(f"Stopping: {skips_in_a_row} runs in a row failed, the model service looks down. "
                                 "Rerun the same command later to resume.")
                    continue
                skips_in_a_row = 0
                f.write(json.dumps(res) + "\n"); f.flush()
                print(f"{case.s['id']:38s} run {r}  {res['stiffness_ratio']:7.1%}  attempts {res['n_attempts']}"
                      + (f"  tool calls {res['n_tool_calls']}" if "n_tool_calls" in res else "") + "  "
                      + ("allowed" if res["accepted"] else "FALLBACK (do nothing)"))


if __name__ == "__main__":
    main()
