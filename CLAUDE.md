# Lattice defect project: handoff notes

## Working rules
- Do only what I ask. No extra checks, backups, or comparisons unless something fails.
- Never delete files. If something should be deleted, tell me and I will do it.
- Only create or edit files inside `C:\Users\amber\Research\AI_Benchmark` (widened by Amber on 2026-10-26).
- Stop after each step: summarize in a few short bullets and wait for me.
- Ask me before generating more than 20 files or running anything expected to take more than 5 minutes.
- Keep script output short: print summaries, not full data.
- Don't install new packages without telling me why.
- Write to me in plain words, short bullets, no jargon. No short catchy phrases that hide the meaning; say exactly what is meant, with an example if needed.
- Teach before you build (agent framework, from 2026-10-26): give me a short lesson on the principle and walk me through applying it to this project, let me make the key choices, then build.
- After every step, explain the whole pipeline: what was added, what exists vs. not yet, and one worked example with real numbers. When you say you "ran" something, name the script and say whether it is plain code or AI.
- The learning log only records what I actually did or was walked through.
- Commit often (after each finished step), one logical change per commit, clear message saying what and why. Briefly tell me what was committed. Never commit secrets (API keys stay in environment variables).
- The proposal `../Agentic_IPQI_AM_Research_Proposal.docx` is the main reference. Cite it for decisions; when my instructions, Ma's directions or the pipeline differ from it, say so in chat (no separate differences file).
- `docs/learning_log.md` is personal and kept off GitHub (in `.gitignore`).
- The living paper draft is `../paper/main.tex`, in its own repo synced with Overleaf. Yichen decides where to submit it. In the 2026-11-05 meeting he said ICML probably isn't mechanical enough and we may look at other journals; no venue is chosen. Update it after each experiment. Result tables come from `agent/results_table.py`; never type result numbers into tables by hand.
- `docs/pipeline_diagrams.md` has a function-level diagram for every stage, agent version and experiment setup (what goes in, which functions run, what comes out). Add one for each new version or experiment before running it, and keep the old ones.
- `docs/progress.md` is a running summary of work per week, written so I can send it to Ma. Each week has a short version (a few lines to paste into a message) and a detailed version; update both after each finished step. Both must include the key decisions (what was chosen, why, alternatives, limits), not only what was built.

## Who and what
- Amber, an undergraduate in industrial engineering at Georgia Tech. Codes in Python at a beginner to intermediate level. New to 3D printing, so explain printing terms.
- Research: a multi-agent framework for AI-driven repair of defects in 3D-printed lattices. Mentor: Ma. Results target end of December 2026.
- Amber's parts: lattice design, defect definition and injection, and agent design. Ma's group does printing and data collection.
- Writing style for Amber: plain words, short bullets, no jargon or shorthand. Ask before guessing.


## Where to find more (open only when the task needs it)
- `docs/reference/project_facts.md`: setup (GitHub, Bambu Studio), fixed design decisions (specimen size, shapes, wall thickness, defect settings), past status.
- `docs/reference/code_notes.md`: what each code file does and how to run it.
- `docs/reference/open_questions.md`: open questions for Ma and Amber.
- `docs/progress.md`, `docs/decisions.md`, `docs/experiments.md`, `docs/pipeline_diagrams.md`: running records.

## How to communicate

These are important. Follow them in every response, summary, and report.

- **Be concise.** Use bullet points instead of paragraphs. Keep each bullet short.
- **Be clear and jargon-free.** Use plain, everyday words. If a technical term is unavoidable, explain it.
- **No shorthand.** Short does not mean cryptic. Each bullet should be a clear, complete thought that Amber can understand without guessing what you meant.
- **No flourish.** No filler, no hype, no decorative language.
- **Ask when unsure.** Ask questions instead of guessing.** Whenever anything is unclear, or there is more than one reasonable way to do a task, stop and ask Amber before acting. Amber would much rather answer a question up front than have you do something slightly wrong that she then has to go back and correct. There is no limit on how many questions you can ask. When in doubt, ask.
