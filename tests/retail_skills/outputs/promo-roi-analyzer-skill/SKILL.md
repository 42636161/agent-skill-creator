---
name: promo-roi-analyzer-skill
description: >-
  A promotion ROI analyzer that computes baseline sales, incremental lift,
  cannibalization effects, and true ROI for retail promotions. Activates on:
  promotion ROI, promo analysis, campaign effectiveness, marketing ROI.
  Triggers on: calculate promo ROI, measure promotion, campaign analysis.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
---
# /promo-roi-analyzer — Promotion ROI Analyzer

Compute incremental sales, cannibalization, and true ROI for promotions.

## Quick Profile

- **Category**: Retail / Marketing Analytics
- **Input**: CSV with promo events (pre/during/post daily sales, marketing cost)
- **Output**: ROI report with lift, cannibalization, and ranking
- **When to use**: Post-promotion review, promo budget planning
- **When not**: For real-time during-promotion tracking

## Methodology

- Baseline = average daily sales in pre-promo period
- Lift = (promo_sales - baseline) / baseline
- Cannibalization = max(0, baseline - post_promo_sales) / promo_sales
- ROI = (incremental_gross_profit - marketing_cost) / marketing_cost

## How to run it

```bash
python3 scripts/pipeline.py --events promo_events.csv --margin 0.30 --output ./reports/
```

## Runtime Contract

- Only run the command above. scripts/ are implementation details.
- Handles edge cases: zero lift, negative ROI, missing baseline data.
