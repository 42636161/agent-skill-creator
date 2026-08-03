---
name: competitor-price-monitor-skill
description: >-
  A competitor price monitoring tool for Chinese e-commerce platforms. Tracks
  competitor pricing on JD.com and Tmall, generates weekly comparison reports.
  Activates on: competitor price, price monitor, price tracking, price comparison.
  Triggers on: price change, competitor analysis, price alert, weekly comparison.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
---
# /competitor-price-monitor — Competitor Price Monitor

Track competitor prices on JD.com and Tmall, generate weekly comparison tables.

## Quick Profile

- **Category**: E-commerce / Competitive Intelligence
- **Input**: Product list CSV (SKU, our price, competitor URLs)
- **Output**: Weekly price comparison report with change alerts
- **When to use**: Weekly competitive pricing review, price strategy adjustment
- **When not**: When no competitor data exists or real-time monitoring is needed

## How to run it

```bash
python3 scripts/pipeline.py --products products.csv --output ./reports/
```

## Runtime Contract

- Only run: `python3 scripts/pipeline.py --products <csv> --output <dir>`
- scripts/ are implementation details.
- Note: Chinese e-commerce APIs (JD Open Platform, Taobao Open Platform) require OAuth app keys.
  See references/platform-auth.md for setup.
