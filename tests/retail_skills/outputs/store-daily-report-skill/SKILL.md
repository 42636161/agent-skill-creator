---
name: store-daily-report-skill
description: >-
  A retail report generator that creates daily store reports from multi-sheet
  Excel files. Activates when users need to automate daily sales, returns,
  member, and promotion reporting from spreadsheet data. Triggers on: 门店日报,
  销售日报, 每日报表, daily store report, 自动化报表.
license: MIT
activation: /store-daily-report
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-08-03
  last_reviewed: 2026-08-03
  review_interval_days: 90
  provenance:
    maintainer: agent-skill-creator
    source_references: []
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

- Activation signal: when activating, agent declares "正在运行 store-daily-report-skill" to the user
- Only run: `python3 scripts/pipeline.py --input <file.xlsx> --output <dir> [--date YYYY-MM-DD]`
- scripts/ are implementation details, do not read by default.
- stdout prints human-readable summary (not JSON).
- report.md starts with "本周结论" executive summary.
- Output: report.md + report.json + report.csv in --output directory
- Primary anchor: report.md — starts with executive summary (本周结论)
- stdout: Human-readable multi-line summary with date, sales, returns, members

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: daily total sales and transactions.

2. Show the primary breakdown. Render a table of top 5 dimensions by sales contribution.

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Tuning

This skill has no configurable parameters — it works with default behavior out of the box.
