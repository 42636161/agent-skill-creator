#!/usr/bin/env python3
import argparse, csv, json, sys
from pathlib import Path
from datetime import datetime

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--products", required=True); p.add_argument("--output", required=True)
    return p.parse_args()

def sf(v, d=0.0):
    try: return float(v)
    except: return d

def classify(margin, turnover):
    median_m = 0.25; median_t = 30  # reasonable defaults
    if margin >= median_m and turnover <= median_t: return "Cash Cow"
    if margin >= median_m and turnover > median_t: return "Star"
    if margin < median_m and turnover > median_t: return "Traffic Driver"
    return "Candidate for Drop"

def main():
    args = parse_args(); out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    with open(args.products, encoding="utf-8-sig") as f:
        products = list(csv.DictReader(f))

    # Compute medians
    margins = [sf(p.get("毛利率", 0)) for p in products]
    turnovers = [sf(p.get("库存周转天数", 999)) for p in products]
    median_m = sorted(margins)[len(margins)//2] if margins else 0.25
    median_t = sorted(turnovers)[len(turnovers)//2] if turnovers else 30

    results = []; stars = []; drops = []
    for p in products:
        m = sf(p.get("毛利率", 0)); t = sf(p.get("库存周转天数", 999))
        is_seasonal = p.get("是否季节性商品", "否") == "是"
        ret_rate = sf(p.get("退货率", 0))
        quad = classify(m, t)
        rec = "Keep & Promote" if quad == "Star" else "Review Pricing" if quad == "Cash Cow" else "Optimize Cost" if quad == "Traffic Driver" else "Consider Drop"
        if ret_rate > 0.5: rec = "HIGH RETURNS - Investigate"
        if is_seasonal: rec += " (seasonal)"

        results.append({"name": p.get("商品名称", ""), "quadrant": quad, "recommendation": rec,
                       "margin": m, "turnover_days": t, "return_rate": ret_rate})
        if quad == "Star": stars.append(p.get("商品名称", ""))
        if quad == "Candidate for Drop": drops.append(p.get("商品名称", ""))

    lines = ["# Product Assortment Analysis", "", "## Summary",
             "Stars (Keep): {} SKUs".format(len(stars)),
             "Drop Candidates: {} SKUs".format(len(drops)),
             "", "## Recommendations", ""]
    for r in sorted(results, key=lambda x: x["margin"], reverse=True)[:20]:
        lines.append("- **{}** | {} | Margin: {:.1%} | {}".format(
            r["name"], r["quadrant"], r["margin"], r["recommendation"]))

    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "report.json").write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Assortment analysis: {} SKUs, {} stars, {} drop candidates".format(len(results), len(stars), len(drops)))
    print("   Output: " + str(out))

if __name__ == "__main__":
    sys.exit(main())
