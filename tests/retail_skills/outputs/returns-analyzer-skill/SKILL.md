---
name: returns-analyzer-skill
description: >-
  A retail returns analysis tool that identifies return patterns and product
  quality issues. Activates on: retur, refund, quality analysis, product returns.
  Triggers on: return rate, return reason, product quality, refund tracking.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
---
# /returns-analyzer — Returns Analysis

Analyze retail returns data: return rate, reason classification, top returned products.

## Quick Profile

- **Category**: Retail Operations / Quality Analysis
- **Input**: CSV with returns data (return date, store, SKU, product name, qty, amount, reason)
- **Output**: report.md (summary-first), report.json
- **When to use**: Weekly/monthly returns review, product quality investigation
- **When not**: When no structured returns data exists

> Phase 0 note: Derived from single-word input. Creator expanded to 4 analysis dimensions:
> return rate, reason classification, product quality alert, refund timeline.

## How to run it

```bash
python3 scripts/pipeline.py --input returns.csv --output ./reports/
```

## Runtime Contract

- Only run: `python3 scripts/pipeline.py --input <csv> --output <dir>`
- scripts/ are implementation details, do not read by default.
- stdout prints human-readable summary, not JSON.
