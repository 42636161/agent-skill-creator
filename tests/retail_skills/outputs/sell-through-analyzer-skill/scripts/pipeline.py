#!/usr/bin/env python3
import argparse, csv, json, sys
from pathlib import Path
from datetime import datetime

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--skus", required=True); p.add_argument("--output", required=True)
    return p.parse_args()

def sf(v, d=0.0):
    try: return float(v)
    except: return d

def si(v, d=0):
    try: return int(v)
    except: return d

def main():
    args = parse_args(); out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    with open(args.skus, encoding="utf-8-sig") as f:
        skus = list(csv.DictReader(f))

    results = []; dead = []; errors = []
    for s in skus:
        begin = sf(s.get("月初库存", 0)); end = sf(s.get("月末库存", 0))
        sold = sf(s.get("月销量", 0)); days = si(s.get("上架天数", 0))
        avg_inv = (begin + end) / 2
        st_rate = sold / avg_inv if avg_inv > 0 else 0

        if begin < 0 or end < 0:
            errors.append({"sku": s.get("商品名称", ""), "issue": "negative inventory"})

        status = "Normal"
        if st_rate < 0.05 and days > 90:
            status = "Dead Stock (滞销)"
            dead.append(s.get("商品名称", ""))
        elif st_rate < 0.10:
            status = "Slow Moving"

        results.append({"name": s.get("商品名称", ""), "sell_through_rate": round(st_rate, 4),
                       "status": status, "days_on_shelf": days})

    lines = ["# Sell-Through Rate Analysis (动销率分析)", "",
             "## Summary", "",
             "Total SKUs analyzed: {}".format(len(results)),
             "Dead stock (滞销): {} SKUs".format(len(dead)),
             "Data errors: {} records".format(len(errors)),
             "", "## Dead Stock Alerts"]
    for d_name in dead[:10]:
        lines.append("- " + d_name)

    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "report.json").write_text(json.dumps({"results": results, "dead_stock": dead, "errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Sell-through analysis: {} SKUs, {} dead stock".format(len(results), len(dead)))
    print("   Output: " + str(out))

if __name__ == "__main__":
    sys.exit(main())
