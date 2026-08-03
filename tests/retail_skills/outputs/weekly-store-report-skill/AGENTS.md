# weekly-store-report-skill — Dispatch Card

Generate weekly store reports for 3 audiences from 3 CSV sources.

**Run**: `python3 scripts/pipeline.py --sales <csv> --feedback <csv> --inventory <csv> --output <dir> [--week YYYY-MM-DD]`

**Output**: `report_store_manager.md` (detailed), `report_region_manager.md` (tabular comparison), `report_executive.md` (executive summary, starts with "本周结论"), `report.json`

Do not read `scripts/*.py` unless troubleshooting. See [SKILL.md](SKILL.md) for full workflow.
