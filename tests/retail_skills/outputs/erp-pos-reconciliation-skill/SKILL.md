---
name: erp-pos-reconciliation-skill
description: >-
  A reconciliation tool that matches ERP export data with POS transaction data
  and identifies discrepancies. Activates on: reconciliation, ERP POS matching,
  data reconciliation, transaction matching. Triggers on: reconcile ERP POS,
  match transactions, find discrepancies, audit sales data.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
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

- Only run: `python3 scripts/pipeline.py --erp <csv> --pos <csv> --output <dir>`
- Works with local CSV files — no API or database connection needed.
- Performs fuzzy matching on transaction IDs, amounts within 2% tolerance.
