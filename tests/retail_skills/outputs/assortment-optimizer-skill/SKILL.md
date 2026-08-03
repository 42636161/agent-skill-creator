---
name: assortment-optimizer-skill
description: >-
  A product assortment optimizer using four-quadrant classification to guide
  keep/drop/replace decisions. Activates on: assortment, product optimization,
  SKU rationalization, category management. Triggers on: which products to drop,
  product performance, category review, assortment planning.
license: MIT
activation: /assortment-optimizer
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

- Activation signal: when activating, agent declares "正在运行 assortment-optimizer-skill" to the user
- Only run the command above. scripts/ are implementation details, do not read by default.
- Recommendations are rule-based, not LLM-dependent.
- Output: report.md (executive summary) + report.json (structured data) in --output directory
- Primary anchor: report.md — start with the executive summary section for quadrant classification results
- stdout: One-line summary with SKU count, star performers, and drop candidates

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: business status summary from the quadrant analysis.

2. Show the primary breakdown. Render a table of products by quadrant (Stars, Cash Cows, Question Marks, Dogs).

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Tuning

The following parameters can be adjusted.

| Parameter | Default | What it controls | When to adjust |
|-----------|---------|------------------|---------------|
| 重新订货阈值 | median_t=30 | Median turnover days for replenishment flag | When your product lifecycle is faster/slower than typical retail (e.g., fashion vs home goods) |
