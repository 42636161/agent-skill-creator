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

- Only run: `python3 scripts/pipeline.py --events <csv> [--margin <rate>] --output <dir>`
- scripts/ are implementation details, do not read by default.
- stdout prints human-readable summary, not JSON.
- report.md starts with executive summary.
