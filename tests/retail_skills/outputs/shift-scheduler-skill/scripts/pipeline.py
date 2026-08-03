#!/usr/bin/env python3
import argparse, csv, sys
from collections import defaultdict
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--traffic", required=True); p.add_argument("--staff", type=int, default=8)
    p.add_argument("--output", required=True)
    return p.parse_args()

def si(v, d=0):
    try: return int(v)
    except: return d

def main():
    args = parse_args(); out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    with open(args.traffic, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # Aggregate traffic by hour across days
    hour_traffic = defaultdict(int)
    for r in rows:
        hour = r.get("时间段", "").split(":")[0] if ":" in r.get("时间段", "") else ""
        hour_traffic[hour] += si(r.get("客流量", 0))

    total = sum(hour_traffic.values()) or 1
    lines = ["# Weekly Shift Schedule", "", "## Staff Allocation ({} staff)".format(args.staff), "", "| Hour | Traffic Share | Staff |", "|---|---|---|"]
    for h in sorted(hour_traffic.keys()):
        share = hour_traffic[h] / total
        staff = max(1, round(share * args.staff))
        lines.append("| {}:00 | {:.1%} | {} |".format(h, share, staff))

    (out / "schedule.md").write_text("\n".join(lines), encoding="utf-8")
    print("Schedule generated for {} hours, {} staff".format(len(hour_traffic), args.staff))
    print("   Output: " + str(out / "schedule.md"))

if __name__ == "__main__":
    sys.exit(main())
