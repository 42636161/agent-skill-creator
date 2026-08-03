#!/usr/bin/env python3
import argparse, csv, json, sys
from pathlib import Path
from datetime import datetime

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--events", required=True); p.add_argument("--margin", type=float, default=0.30)
    p.add_argument("--output", required=True)
    return p.parse_args()

def sf(v, d=0.0):
    try: return float(v)
    except: return d

def main():
    args = parse_args(); out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    with open(args.events, encoding="utf-8-sig") as f:
        events = list(csv.DictReader(f))

    results = []
    for e in events:
        name = e.get("活动名称", ""); pre = sf(e.get("活动前日均销售额")); during = sf(e.get("活动中日均销售额"))
        post = sf(e.get("活动后一周日均销售额")); cost = sf(e.get("营销费用"))

        if pre <= 0: lift = 0.0; cannib = 0.0
        else:
            lift = (during - pre) / pre
            cannib = max(0, pre - post) / during if during > 0 else 0

        incremental = (during - pre) * args.margin if during > pre else 0
        roi = (incremental - cost) / cost if cost > 0 else 0

        results.append({"name": name, "lift": round(lift, 4), "cannibalization": round(cannib, 4),
                        "roi": round(roi, 4), "incremental_profit": round(incremental, 2)})

    # Sort by ROI
    results.sort(key=lambda x: -x["roi"])

    lines = ["# Promotion ROI Analysis", "", "Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M"),
             "", "## Results", ""]
    lines.append("| Promotion | Lift | Cannibalization | ROI | Inc. Profit |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        lines.append("| {} | {:.1%} | {:.1%} | {:.1%} | {:.0f} |".format(
            r["name"], r["lift"], r["cannibalization"], r["roi"], r["incremental_profit"]))

    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "report.json").write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")

    best = results[0] if results else {"name": "N/A"}
    print("ROI analysis: {} promotions, best: {} (ROI {:.1%})".format(len(results), best["name"], best.get("roi", 0)))
    print("   Output: " + str(out))

if __name__ == "__main__":
    sys.exit(main())
