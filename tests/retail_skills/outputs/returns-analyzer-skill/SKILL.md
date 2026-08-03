---
name: returns-analyzer-skill
description: >-
  A retail returns analysis tool that identifies return patterns and product
  quality issues. Activates on: retur, refund, quality analysis, product returns.
  Triggers on: return rate, return reason, product quality, refund tracking.
license: MIT
activation: /returns-analyzer
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

- Activation signal: when activating, agent declares "正在运行 returns-analyzer-skill" to the user
- Only run: `python3 scripts/pipeline.py --input <csv> --output <dir>`
- scripts/ are implementation details, do not read by default.
- stdout prints human-readable summary, not JSON.
- Output: report.md (return analysis) + report.json (structured data) in --output directory
- Primary anchor: report.md — start with the returns summary (total returns, rate, top reason)
- stdout: One-line summary with count, total value, and top return reason

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: total returns count and rate.

2. Show the primary breakdown. Render a table of top 5 return reasons sorted by frequency.

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Tuning

This skill has no configurable parameters — it works with default behavior out of the box.
