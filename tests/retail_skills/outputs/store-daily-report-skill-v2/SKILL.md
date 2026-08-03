---
name: store-daily-report-skill
description: >-
  A retail report generator that creates daily store reports from multi-sheet
  Excel files. Activates when users need to automate daily sales, returns,
  member, and promotion reporting from spreadsheet data. Triggers on: 门店日报,
  销售日报, 每日报表, daily store report, 自动化报表.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-08-03
  last_reviewed: 2026-08-03
  review_interval_days: 90
  activation: /store-daily-report
---
# /store-daily-report — Store Daily Report Generator

Generate daily retail reports from multi-sheet Excel files (销售明细, 退货, 会员, 促销).

## Quick Profile

- **Category**: Retail Operations / Reporting
- **Input**: Multi-sheet .xlsx (4 sheets: sales, returns, members, promotions)
- **Output**: report.md (summary-first), report.json, report.csv
- **When to use**: Daily store performance reporting, multi-dimension sales analysis
- **When not**: When data is not in the expected 4-sheet format, or real-time dashboard is needed

## How to run it

```bash
python3 scripts/pipeline.py --input 门店销售.xlsx --output ./reports/
python3 scripts/pipeline.py --input 门店销售.xlsx --output ./reports/ --date 2026-07-15
```

## Runtime Contract

- Only run: `python3 scripts/pipeline.py --input <file.xlsx> --output <dir> [--date YYYY-MM-DD]`
- scripts/ are implementation details, do not read by default.
- stdout prints human-readable summary (not JSON).
- report.md starts with "本周结论" executive summary.
