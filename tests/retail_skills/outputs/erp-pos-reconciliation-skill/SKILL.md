---
name: erp-pos-reconciliation-skill
description: >-
  A reconciliation tool that matches ERP export data with POS transaction data
  and identifies discrepancies. Activates on: reconciliation, ERP POS matching,
  data reconciliation, transaction matching. Triggers on: reconcile ERP POS,
  match transactions, find discrepancies, audit sales data.
license: MIT
activation: /erp-pos-reconciliation
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
# /erp-pos-reconciliation — ERP-POS Reconciliation

Match ERP export records with POS transaction data, identify mismatches.

## Quick Profile

- **Category**: Finance / Retail Operations
- **Input**: Two CSV files (ERP export, POS data)
- **Output**: Reconciliation report showing matches, ERP-only, POS-only, amount discrepancies
- **When to use**: Weekly/monthly sales reconciliation, audit preparation
- **When not**: When data is already in a unified system

> Note: This skill works with local CSV files only. No ERP API integration needed.
> The input is exported CSV data, not a live system connection.

## How to run it

```bash
python3 scripts/pipeline.py --erp 金蝶_导出.csv --pos pos_sales.csv --output ./reports/
```

## Runtime Contract

- Activation signal: when activating, agent declares "正在运行 erp-pos-reconciliation-skill" to the user
- Only run: `python3 scripts/pipeline.py --erp <csv> --pos <csv> --output <dir>`
- scripts/ are implementation details, do not read by default.
- Works with local CSV files — no API or database connection needed.
- Performs fuzzy matching on transaction IDs, amounts within 2% tolerance.
- Output: report.md (mismatch summary) + report.json (structured data) in --output directory
- Primary anchor: report.md — start with the reconciliation summary (matched/mismatched counts)
- stdout: One-line reconciliation summary with match rate

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: match rate and total discrepancies found.

2. Show the primary breakdown. Render a table of mismatches by type (missing in ERP, missing in POS, amount difference).

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Tuning

This skill has no configurable parameters — it works with default behavior out of the box.
