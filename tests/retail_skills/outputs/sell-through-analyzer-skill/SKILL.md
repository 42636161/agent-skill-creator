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
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
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

- Only run the command above. scripts/ are implementation details.
- Handles edge cases: zero movement, negative stock (data error).
