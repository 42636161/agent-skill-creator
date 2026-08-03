---
name: competitor-price-monitor-skill
description: >-
  A competitor price monitoring tool for Chinese e-commerce platforms. Tracks
  competitor pricing on JD.com and Tmall, generates weekly comparison reports.
  Activates on: competitor price, price monitor, price tracking, price comparison.
  Triggers on: price change, competitor analysis, price alert, weekly comparison.
license: MIT
activation: /competitor-price-monitor
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

- Activation signal: when activating, agent declares "正在运行 competitor-price-monitor-skill" to the user
- Only run: `python3 scripts/pipeline.py --products <csv> --output <dir>`
- scripts/ are implementation details, do not read by default.
- Note: Chinese e-commerce APIs (JD Open Platform, Taobao Open Platform) require OAuth app keys.
  See references/platform-auth.md for setup.
- Output: report.md (comparison table + alerts) + report.json (structured data) in --output directory
- Primary anchor: report.md — start with the price change summary section
- stdout: One-line summary with product count tracked

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: number of price changes and direction (up/down).

2. Show the primary breakdown. Render a table of products sorted by price change magnitude.

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Tuning

This skill has no configurable parameters — it works with default behavior out of the box.
