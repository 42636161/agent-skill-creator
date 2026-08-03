---
name: monthly-ops-analysis-suite
description: >-
  A retail operations analysis suite for monthly store performance across four
  dimensions. Activates on: monthly ops, store analysis, multi-dimension report,
  region manager review. Triggers on: monthly report, store KPI, operations review.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
---
# /monthly-ops-analysis — Monthly Store Operations Suite

Four-dimension analysis suite: sales achievement, inventory health, staff efficiency, cost control.

## Quick Profile

- **Category**: Retail Operations / Multi-Dimension Analysis
- **Input**: Four CSV files (sales_target, inventory_health, staff_efficiency, cost_control)
- **Output**: Executive summary + per-dimension reports
- **When to use**: Monthly regional manager reviews, multi-dimension KPI analysis
- **When not**: Single-dimension analysis (use individual component skill)

## How to run it

```bash
# Full suite
python3 scripts/pipeline.py --sales <csv> --inventory <csv> --staff <csv> --cost <csv> --output <dir>

# Individual component
python3 components/sales-achievement/scripts/pipeline.py --input <csv> --output <dir>
```

## Runtime Contract

- Only run the commands above. scripts/ and components/*/scripts/ are implementation details.
- Four components are independently usable.
- Master orchestrator integrates results across all dimensions.
