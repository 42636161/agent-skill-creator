---
name: monthly-ops-analysis-suite
description: >-
  A retail operations analysis suite for monthly store performance across four
  dimensions. Activates on: monthly ops, store analysis, multi-dimension report,
  region manager review. Triggers on: monthly report, store KPI, operations review.
license: MIT
activation: /monthly-ops-analysis
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
  provenance:
    maintainer: agent-skill-creator
    source_references: []
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

- Only run the commands above. scripts/ and components/*/scripts/ are implementation details, do not read by default.
- Four components are independently usable.
- Master orchestrator integrates results across all dimensions.
- Output: Combined report.md (executive summary) + per-dimension reports in --output directory
- Primary anchor: report.md — start with the combined executive summary across all four dimensions
- stdout: One-line summary with store count, total revenue, and achievement rate

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: overall store performance across all 4 dimensions.

2. Show the primary breakdown. Render a table of top 5 stores by sales achievement rate.

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Tuning

This skill has no configurable parameters — it works with default behavior out of the box.
