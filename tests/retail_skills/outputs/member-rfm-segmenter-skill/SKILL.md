---
name: member-rfm-segmenter-skill
description: >-
  A customer RFM segmentation tool that classifies members by recency, frequency,
  and monetary value with configurable scoring. Activates on: RFM, customer
  segmentation, member analysis, loyalty analysis. Triggers on: segment customers,
  classify members, RFM analysis, customer value.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
---
# /member-rfm-segmenter — Member RFM Segmentation

Classify members by Recency, Frequency, Monetary value with configurable scoring.

## Quick Profile

- **Category**: Retail / CRM Analytics
- **Input**: CSV of member transactions
- **Output**: RFM scores, segment profiles, marketing recommendations
- **When to use**: Member segmentation, targeted marketing planning
- **When not**: When transaction data is incomplete or member base < 100

## Methodology

- R = days since last purchase (lower = better)
- F = total transaction count
- M = total spending
- Scoring: configurable quantile-based (default) or fixed thresholds

## How to run it

```bash
python3 scripts/pipeline.py --transactions txns.csv --output ./reports/ [--bins 5]
```

## Runtime Contract

- Only run the command above. scripts/ are implementation details.
- Scoring method is configurable via --bins parameter.
