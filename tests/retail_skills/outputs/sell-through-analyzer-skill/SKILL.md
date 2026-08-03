---
name: sell-through-analyzer-skill
description: >-
  A sell-through rate analyzer for retail SKU performance. Computes sell-through
  rates, identifies dead stock, and provides category velocity rankings.
  Activates on: sell through, SKU velocity, inventory turnover, product
  performance. Triggers on: calculate sell through, find dead stock, analyze
  product velocity, inventory performance. Supports Chinese retail terminology
  including 动销率 (sell-through rate) and 滞销 (dead stock).
license: MIT
activation: /sell-through-analyzer
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
# /sell-through-analyzer — Sell-Through Rate Analyzer (动销率分析)

Compute sell-through rates, flag dead stock, and rank category velocity.

## Quick Profile

- **Category**: Retail / Inventory Analytics
- **Input**: CSV with SKU sales (beginning inventory, ending inventory, units sold)
- **Output**: Sell-through rate report, dead stock alerts, category rankings
- **When to use**: Monthly inventory review, slow-moving stock identification
- **When not**: When real-time inventory data is needed

## Methodology

- Sell-Through Rate = Units Sold / (Beginning Inventory + Ending Inventory) / 2
- Dead Stock: ST Rate < 5% and days on shelf > 90
- Negative inventory values flagged as data errors

## How to run it

```bash
python3 scripts/pipeline.py --skus sku_sales.csv --output ./reports/
```

## Runtime Contract

- Activation signal: when activating, agent declares "正在运行 sell-through-analyzer-skill" to the user
- Only run the command above. scripts/ are implementation details, do not read by default.
- Handles edge cases: zero movement, negative stock (data error).
- Output: report.md (sell-through analysis) + report.json (structured data) in --output directory
- Primary anchor: report.md — start with the sell-through summary and dead stock alerts
- stdout: One-line summary with SKU count and dead stock count

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: overall sell-through rate and dead stock count.

2. Show the primary breakdown. Render a table of top 5 slowest-moving SKUs by sell-through rate.

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Tuning

This skill has no configurable parameters — it works with default behavior out of the box.
