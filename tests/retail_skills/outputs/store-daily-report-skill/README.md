# store-daily-report-skill

Generate daily retail store reports from multi-sheet Excel files.

## Install

```bash
skillctl install store-daily-report-skill
```

## Usage

```bash
python3 scripts/pipeline.py --input 门店销售.xlsx --output ./reports/
python3 scripts/pipeline.py --input 门店销售.xlsx --output ./reports/ --date 2026-07-15
```

Output: `report.md` (summary-first), `report.json`, `report.csv`
