---
name: shift-scheduler-skill
description: >-
  A simple shift scheduler that generates weekly staff schedules from foot
  traffic data. Activates on: shift scheduler, staff scheduling, employee
  schedule, roster planner. Triggers on: create schedule, generate shifts,
  staff roster, weekly schedule.
license: MIT
activation: /shift-scheduler
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
# /shift-scheduler — Store Shift Scheduler

Generate weekly staff schedules based on foot traffic patterns.

## Quick Profile

- **Category**: Retail Operations / HR
- **Input**: CSV with foot traffic by hour (date, time_slot, traffic, is_holiday)
- **Output**: Weekly shift schedule table
- **When to use**: Weekly shift planning for stores with variable traffic
- **When not**: When complex constraints (union rules, skill matching) are needed

## How to run it

```bash
python3 scripts/pipeline.py --traffic foot_traffic.csv --staff 8 --output ./schedule/
```

## Runtime Contract

- Activation signal: when activating, agent declares "正在运行 shift-scheduler-skill" to the user
- Only run the command above. scripts/ are implementation details, do not read by default.
- This is a simple rule-based scheduler (not a suite of tools).
- Output: Schedule in --output directory (formatted schedule table)
- Primary anchor: Generated schedule file — read the daily shift table
- stdout: One-line summary with hours and staff count

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: week period and staff count scheduled.

2. Show the primary breakdown. Render a table of daily staff distribution (peak vs off-peak coverage).

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Tuning

The following parameters can be adjusted.

| Parameter | Default | What it controls | When to adjust |
|-----------|---------|------------------|---------------|
| 最小排班时长 | --traffic (default: 8) | Minimum staff hours per shift slot | When store hours or peak patterns change |
