#!/usr/bin/env python3
import argparse, csv, sys
from pathlib import Path
from datetime import datetime

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--sales", required=True)
    p.add_argument("--inventory", required=True)
    p.add_argument("--staff", required=True)
    p.add_argument("--cost", required=True)
    p.add_argument("--output", required=True)
    return p.parse_args()

def sf(v, d=0.0):
    try: return float(v)
    except: return d

def load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def main():
    args = parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)

    sales = load_csv(args.sales); cost_rows = load_csv(args.cost)
    stores = []; sales_data = {}
    for r in sales:
        s = r.get("门店", r.get("store", ""))
        if s not in stores: stores.append(s)
        actual = sf(r.get("实际销售额", r.get("actual_sales", 0)))
        target = sf(r.get("目标销售额", r.get("target", 1)))
        sales_data[s] = {"actual": actual, "target": target, "rate": actual/target if target else 0}

    cost_data = {}
    for r in cost_rows:
        s = r.get("门店", r.get("store", ""))
        cost_data[s] = {"total": sf(r.get("总费用", 0)), "rate": sf(r.get("费用率", 0))}

    t_actual = sum(v["actual"] for v in sales_data.values())
    t_target = sum(v["target"] for v in sales_data.values())
    best = max(sales_data.items(), key=lambda x: x[1]["rate"]) if sales_data else ("N/A", {"rate": 0})
    worst = min(sales_data.items(), key=lambda x: x[1]["rate"]) if sales_data else ("N/A", {"rate": 0})
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Monthly Operations Analysis - Executive Summary",
        "", "Generated: " + now, "",
        "## Key Findings",
        "", "{} stores. Target: {:.0f}, Actual: {:.0f}, Rate: {:.1%}".format(
            len(stores), t_target, t_actual, t_actual/t_target if t_target else 0),
        "", "- Best: {} ({:.1%})".format(best[0], best[1]["rate"]),
        "- Worst: {} ({:.1%})".format(worst[0], worst[1]["rate"]),
    ]
    (out / "executive_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("Suite complete: {} stores, total {:.0f}, rate {:.1%}".format(
        len(stores), t_actual, t_actual/t_target if t_target else 0))
    print("   Output: " + str(out / "executive_summary.md"))

if __name__ == "__main__":
    sys.exit(main())
