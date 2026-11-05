# Paper draft

`main.tex` is a living draft of the research paper. It is updated after each experiment, so details don't get lost.

**To view it as a PDF:** LaTeX isn't installed on this computer. The easiest route is Overleaf (overleaf.com): create a project, then upload `main.tex`, `references.bib` and the `tables` folder.

**To update the result tables:**

```
python agent/results_table.py out/runs/e6_v0_nemotron.jsonl out/runs/e6_v1_nemotron.jsonl out/results/e6_table.md
```

This writes the files in `tables/` from the run logs, so numbers in tables are never typed by hand.

In the PDF, red text marks work still to do, and blue text marks how settled a section is.
