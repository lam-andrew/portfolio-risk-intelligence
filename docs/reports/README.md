# Weekly report exports

The editable Week 3 source is [week3-report.md](../week3-report.md). It contains
acceptance criteria, per-story DoD tasks, 18 test specifications, source links,
and the evidence cutoff. Preserve the original Week 2 submission.

## Build

Run a Python environment with `reportlab` installed:

```sh
python docs/reports/build_week3_pdf.py
```

Output: [Orbit_Week3_Report.pdf](../../output/pdf/Orbit_Week3_Report.pdf).
The renderer uses explicit page boundaries and draws the report's burndown from
its stated September 7-8 observations (0 open-issue points). It does not retrieve
live board data. If updating the reporting period, update source, chart data,
cutoff labels, and evidence together; never extend actuals into future dates.

Arial is embedded when available locally on macOS; otherwise standard PDF fonts
are used. Do not add font binaries to the repository. Render and visually inspect
every page after changes, check hyperlinks and test IDs, and review through a PR.
The exported PDF is the single assessment deliverable; Markdown and renderer are
maintained so the document can be corrected without reconstructing it.
