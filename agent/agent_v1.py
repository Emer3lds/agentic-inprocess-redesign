"""
Agent version 1: the same model and case facts as v0, plus a calculation tool (decision D10).

  The agent works in turns. Each turn it either calls evaluate_design (plastic used, budget, a stiffness
  estimate, rule violations) to check an idea, or calls submit_fix with its final answer.
  - evaluate_design: at most TOOL_BUDGET calls per case (the non-AI search gets the same budget).
  - submit_fix: judged by the checker; rejected answers get the reasons back, at most MAX_ATTEMPTS.
  - If nothing is accepted, fall back to do nothing (the failure still counts), as in v0.
Every turn is logged: what the model said, which tools it called with which inputs, and what came back.

Run: python agent/agent_v1.py --cases z10 --runs 1    (uses the AI; needs GEMINI_API_KEY)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from agent_v0 import *
from tools import Toolbox, TOOL_BUDGET

MAX_TURNS = TOOL_BUDGET + MAX_ATTEMPTS + 3   # a hard stop in case the model never submits
THICKNESSES = {"type": "ARRAY", "items": {"type": "NUMBER"}, "description": "one wall thickness in mm per 1 mm band, bottom band first"}
TOOL_DECLS = [
    {"name": "evaluate_design",
     "description": "Check a design you are considering: plastic used and budget, stiffness estimate along Y (% of healthy), rule violations.",
     "parameters": {"type": "OBJECT", "properties": {"wall_thickness_mm": THICKNESSES}, "required": ["wall_thickness_mm"]}},
    {"name": "submit_fix",
     "description": "Submit your final design. The checker judges it.",
     "parameters": {"type": "OBJECT", "properties": {"wall_thickness_mm": THICKNESSES, "reasoning": {"type": "STRING"}},
                    "required": ["wall_thickness_mm", "reasoning"]}},
]


def run_agent_v1(case, prompt_version="v2_tools", model=llm.DEFAULT_MODEL):
    template = open(os.path.join(HERE, "prompts", f"{prompt_version}.md")).read()
    prompt = fill(template, {**slots_for(case), "tool_budget": TOOL_BUDGET, "max_attempts": MAX_ATTEMPTS})
    contents = [{"role": "user", "parts": [{"text": prompt}]}]
    tb, turns, submissions, accepted, t0 = Toolbox(case), [], [], False, time.time()
    for k in range(1, MAX_TURNS + 1):
        content, meta = llm.step(contents, TOOL_DECLS, model=model)
        contents.append(content)
        calls = [p["functionCall"] for p in content["parts"] if "functionCall" in p]
        text = " ".join(p["text"] for p in content["parts"] if "text" in p and not p.get("thought"))
        responses = []
        for c in calls:
            args = c.get("args", {})
            if c["name"] == "evaluate_design":
                r = tb.evaluate_design(args.get("wall_thickness_mm"))
            elif c["name"] == "submit_fix" and len(submissions) < MAX_ATTEMPTS:
                fix = {"wall_thickness_mm": args.get("wall_thickness_mm")}
                violations = check(case, fix)
                submissions.append({"fix": fix, "reasoning": args.get("reasoning"), "violations": violations})
                accepted = not violations
                r = {"accepted": True} if accepted else {"accepted": False, "violations": violations,
                                                          "submissions_left": MAX_ATTEMPTS - len(submissions)}
            else:
                r = {"error": f"unknown tool {c['name']}" if c["name"] != "submit_fix" else "no submissions left"}
            responses.append({"functionResponse": {"name": c["name"], "response": r}})
            if accepted:
                break
        turns.append({"turn": k, "text": text, "calls": calls, "responses": [x["functionResponse"]["response"] for x in responses], **meta})
        if accepted or len(submissions) >= MAX_ATTEMPTS:
            break
        contents.append({"role": "user", "parts": responses or [{"text": "Please call evaluate_design or submit_fix."}]})
    final = submissions[-1]["fix"] if accepted else do_nothing(case)
    return {"case": case.s["id"], "agent": "v1", "prompt_version": prompt_version, "prompt_text": prompt, "tool_decls": TOOL_DECLS, "model": model,
            "accepted": accepted, "n_attempts": len(submissions), "n_tool_calls": len(tb.calls), "n_turns": len(turns),
            "fallback_used": not accepted, "final_fix": final, "final_reasoning": submissions[-1]["reasoning"] if submissions else None,
            "final_violations": check(case, final), **score(case, final),
            "decision_seconds": round(time.time() - t0, 1), "tool_calls": tb.calls, "submissions": submissions, "turns": turns}


if __name__ == "__main__":
    main(run_agent_v1, default_prompt="v2_tools")
