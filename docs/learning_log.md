# Learning log

After each session: the principle, what we did, and 2 to 3 sentences I could say in an interview.

---

## Session 1 (2026-10-26): define the task as test cases
- **Status:** Claude built this before teaching it; lesson and exercise done afterwards (2026-10-27).
- **Principle:** before building an agent, write down exactly what one problem looks like (inputs, limits, what counts as success).
- **What I did (exercise answers, with feedback):**
  - Why 10/50/80% instead of 10/20%: defects can happen at any height, and we need to see how the agent behaves on later defects. ✔ Also: the later the defect, the less height is left to fix it, so this tests whether timing matters.
  - Why a material budget: without it the agent could build the sturdiest structure possible, which is not realistic or helpful. ✔ Also: "more plastic = stronger" is trivially true, so success would mean nothing and comparisons would be unfair.
  - How to judge a fix without crushing: a crush simulation, or a calculation of how forces move through the redesigned part. ✔ Becomes the session 2 decision (formula vs. beam model vs. full simulation). Also needed: validity checks (nothing floating, sits on the printed part, within budget).
- **Interview version:** _(after the exercise, in my own words)_
