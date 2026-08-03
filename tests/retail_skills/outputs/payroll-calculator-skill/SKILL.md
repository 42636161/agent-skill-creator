---
name: payroll-calculator-skill
description: >-
  A retail payroll calculator handling base pay, tiered commission, attendance
  bonus, overtime, deductions, and social insurance. Activates on: payroll,
  salary calculator, commission calculator. Triggers on: calculate salary,
  compute payroll, process payroll, wage calculation.
license: MIT
activation: /payroll-calculator
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

- Activation signal: when activating, agent declares "正在运行 payroll-calculator-skill" to the user
- Only run the command above. scripts/ are implementation details, do not read by default.
- Commission rules are parsed from commission_rules.md, not hardcoded.
- stdout prints aggregate summary only (no individual salary details).
- Output files contain salary data — store securely.
- Output: report.md (payslip summary) + report.json + report.csv in --output directory
- Primary anchor: report.md — start with the payroll total and headcount summary
- stdout: One-line summary with employee count, total payroll, and average pay

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: total payroll amount and headcount.

2. Show the primary breakdown. Render a table of top 5 employees by total pay (for audit).

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Security

- No individual salary data in stdout
- security_scan.py must pass before use
- Output directory should be access-restricted

## Tuning

This skill has no configurable parameters — it works with default behavior out of the box.
