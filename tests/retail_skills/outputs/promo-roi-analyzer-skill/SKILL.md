---
name: promo-roi-analyzer-skill
description: >-
  A promotion ROI analyzer that computes baseline sales, incremental lift,
  cannibalization effects, and true ROI for retail promotions. Activates on:
  promotion ROI, promo analysis, campaign effectiveness. Triggers on: calculate
  promo ROI, measure promotion, campaign analysis, 促销ROI.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-08-03
  last_reviewed: 2026-08-03
  review_interval_days: 90
  provenance:
    maintainer: agent-skill-creator
    source_references: []
activation: /promo-roi-analyzer
---
# /promo-roi-analyzer - Promotion ROI Analyzer

Compute lift, cannibalization, and true ROI from promotion event CSV.

## Quick Profile

- **Category**: Retail / Marketing Analytics
- **Input**: CSV with promotion events (pre/during/post daily sales, marketing cost)
- **Output**: report.md (summary-first), report.json
- **When to use**: Post-promotion review, campaign effectiveness analysis
- **When not**: Real-time tracking or when baseline data is unavailable

## How to run it

```bash
python3 scripts/pipeline.py --events promo_events.csv --output ./reports/
python3 scripts/pipeline.py --events promo_events.csv --margin 0.30 --output ./reports/
```

## Runtime Contract

- Activation signal: when activating, agent declares "正在运行 promo-roi-analyzer-skill" to the user
- Only run: `python3 scripts/pipeline.py --events <csv> [--margin <rate>] --output <dir>`
- scripts/ are implementation details, do not read by default.
- stdout prints human-readable summary, not JSON.
- report.md starts with executive summary.
- Output: report.md (ROI analysis) + report.json (structured data) in --output directory
- Primary anchor: report.md — start with the executive ROI summary per promotion event
- stdout: One-line ROI summary per promotion

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: promotion name, ROI value, and whether it was profitable.

2. Show the primary breakdown. Render a table of top 5 promotions sorted by ROI.

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Tuning

The following parameters can be adjusted.

| Parameter | Default | What it controls | When to adjust |
|-----------|---------|------------------|---------------|
| 利润率 | --margin (default: 0.0) | Gross margin rate used for profit calculation | When your actual margin differs from default; adjust for accurate ROI |
