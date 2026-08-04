#!/usr/bin/env python3
"""Promotion ROI Analyzer - computes lift, cannibalization, and true ROI."""
import argparse, csv, json, sys
from pathlib import Path
from datetime import datetime

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--events", required=True)
    p.add_argument("--margin", type=float, default=0.30)
    p.add_argument("--output", required=True)
    return p.parse_args()

def sf(v, d=0.0):
    try: return float(v)
    except: return d

def main():
    args = parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    with open(args.events, encoding="utf-8-sig") as f:
        events = list(csv.DictReader(f))

    results = []
    for e in events:
        name = e.get("活动名称", "")
        pre = sf(e.get("活动前日均销售额"))
        during = sf(e.get("活动中日均销售额"))
        post = sf(e.get("活动后一周日均销售额"))
        cost = sf(e.get("营销费用"))

        if pre <= 0:
            lift = 0.0; cannib = 0.0
        else:
            lift = (during - pre) / pre
            cannib = max(0, pre - post) / during if during > 0 else 0

        incremental = (during - pre) * args.margin if during > pre else 0
        roi = (incremental - cost) / cost if cost > 0 else 0

        results.append({
            "name": name, "lift": round(lift, 4),
            "cannibalization": round(cannib, 4),
            "roi": round(roi, 4),
            "incremental_profit": round(incremental, 2),
        })

    results.sort(key=lambda x: -x["roi"])
    top3 = results[:3]
    bot3 = [r for r in results if r["roi"] < 0][:3]

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 本周结论 - 促销ROI分析", "",
        "生成时间: " + now_str, "",
        "## 核心发现", "",
        str(len(results)) + " 场促销活动。",
    ]
    if results:
        lines.append("最佳ROI: " + top3[0]["name"] + " (" + "{:.1%}".format(top3[0]["roi"]) + "), 增量利润 " + "${:,.0f}".format(top3[0]["incremental_profit"]))
    if bot3:
        names = ", ".join([r["name"] for r in bot3])
        lines.append(str(len(bot3)) + " 场ROI为负，建议复盘: " + names)
    lines.append("")
    lines.append("## 详细排名")
    lines.append("| 活动 | Lift | Cannib | ROI | 增量利润 |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        lines.append("| " + r["name"] + " | {:.1%} | {:.1%} | {:.1%} | ${:,.0f} |".format(r["lift"], r["cannibalization"], r["roi"], r["incremental_profit"]))

    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "report.json").write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8")

    profitable = len([r for r in results if r["roi"] > 0])
    print("Promo ROI: " + str(len(results)) + " events, " + str(profitable) + " profitable")
    if results:
        print("  Best: " + results[0]["name"] + " (ROI " + "{:.1%}".format(results[0]["roi"]) + ")")
    if bot3:
        print("  " + str(len(bot3)) + " negative ROI events need review")
    print("  Output: " + str(out))

if __name__ == "__main__":
    sys.exit(main())
