---
name: payroll-calculator-skill
description: >-
  A retail payroll calculator handling base pay, tiered commission, attendance
  bonus, overtime, deductions, and social insurance. Activates on: payroll,
  salary calculator, commission calculator. Triggers on: calculate salary,
  compute payroll, process payroll, wage calculation.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
---
# /payroll-calculator — Retail Payroll Calculator

Compute monthly salaries with tiered commission rules, attendance tracking, overtime, and social insurance deductions.

## Quick Profile

- **Category**: HR / Payroll / Retail Operations
- **Input**: employees.csv, commission_rules.md, attendance.csv
- **Output**: report.md, report.json, report.csv (per-employee breakdown)
- **When to use**: Monthly payroll for retail staff with tiered commission
- **When not**: For non-retail payroll or ERP-integrated systems

## How to run it

```bash
python3 scripts/pipeline.py --employees employees.csv --rules commission_rules.md --attendance attendance.csv --output ./payroll/
```

## Runtime Contract

- Only run the command above. scripts/ are implementation details.
- Commission rules are parsed from commission_rules.md, not hardcoded.
- stdout prints aggregate summary only (no individual salary details).
- Output files contain salary data — store securely.

## Security

- No individual salary data in stdout
- security_scan.py must pass before use
- Output directory should be access-restricted
