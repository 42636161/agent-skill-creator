---
name: assortment-optimizer-skill
description: >-
  A product assortment optimizer using four-quadrant classification to guide
  keep/drop/replace decisions. Activates on: assortment, product optimization,
  SKU rationalization, category management. Triggers on: which products to drop,
  product performance, category review, assortment planning.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
---
# /assortment-optimizer — Product Assortment Optimizer

Four-quadrant classification (margin x turnover) with seasonal awareness and actionable recommendations.

## Quick Profile

- **Category**: Retail / Category Management
- **Input**: CSV with product performance (margin, turnover, returns rate, seasonality)
- **Output**: Four-quadrant classification + keep/drop/review recommendations
- **When to use**: Quarterly assortment review, SKU rationalization
- **When not**: When seasonality patterns are unknown or data is incomplete

## Methodology

- High Margin + High Turnover = Stars (Keep & Promote)
- High Margin + Low Turnover = Cash Cows (Review Pricing)
- Low Margin + High Turnover = Traffic Drivers (Optimize Cost)
- Low Margin + Low Turnover = Candidates (Consider Dropping)
- Seasonal products are evaluated only within their active season

## How to run it

```bash
python3 scripts/pipeline.py --products products.csv --output ./reports/
```

## Runtime Contract

- Only run the command above. scripts/ are implementation details.
- Recommendations are rule-based, not LLM-dependent.
