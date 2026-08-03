---
name: shift-scheduler-skill
description: >-
  A simple shift scheduler that generates weekly staff schedules from foot
  traffic data. Activates on: shift scheduler, staff scheduling, employee
  schedule, roster planner. Triggers on: create schedule, generate shifts,
  staff roster, weekly schedule.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
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

- Only run the command above. scripts/ are implementation details.
- This is a simple rule-based scheduler (not a suite of tools).
