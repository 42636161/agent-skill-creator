# store-daily-report-skill — Dispatch Card

Generate daily retail reports from multi-sheet Excel (.xlsx) files containing
sales, returns, members, and promotions data.

**Run**: `python3 scripts/pipeline.py --input <file.xlsx> --output <dir> [--date YYYY-MM-DD]`

**Output**: `report.md` (summary-first), `report.json` (structured), `report.csv` (tabular)

Do not read `scripts/*.py` unless troubleshooting. See [SKILL.md](SKILL.md) for full workflow.
