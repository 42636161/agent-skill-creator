---
name: member-rfm-segmenter-skill
description: >-
  A customer RFM segmentation tool that classifies members by recency, frequency,
  and monetary value with configurable scoring. Activates on: RFM, customer
  segmentation, member analysis, loyalty analysis. Triggers on: segment customers,
  classify members, RFM analysis, customer value.
license: MIT
activation: /member-rfm-segmenter
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

- Activation signal: when activating, agent declares "正在运行 member-rfm-segmenter-skill" to the user
- Only run the command above. scripts/ are implementation details, do not read by default.
- Scoring method is configurable via --bins parameter.
- Output: report.md (segment profiles + recommendations) + report.json (structured data) in --output directory
- Primary anchor: report.md — start with the segment distribution summary
- stdout: One-line summary with member count and segment count

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: segment distribution (e.g., "High Value: 120 members").

2. Show the primary breakdown. Render a table of member segments sorted by member count (High Value, Active, At Risk, Dormant).

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Tuning

The following parameters can be adjusted.

| Parameter | Default | What it controls | When to adjust |
|-----------|---------|------------------|---------------|
| 评分分档数 | --bins (default: 5) | Number of scoring tiers for R, F, M dimensions | When you need finer segmentation (more bins) or simpler tiers (fewer bins) for executive reports |
