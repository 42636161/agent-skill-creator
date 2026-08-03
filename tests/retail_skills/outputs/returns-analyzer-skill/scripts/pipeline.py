#!/usr/bin/env python3
import argparse, csv, json, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True); p.add_argument("--output", required=True)
    return p.parse_args()

def sf(v, d=0.0):
    try: return float(v)
    except: return d

def main():
    args = parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)

    with open(args.input, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    rows = [r for r in rows if any(v.strip() for v in r.values())]

    reason_count = defaultdict(int); product_amt = defaultdict(float)
    store_count = defaultdict(int); total_amt = 0.0

    for r in rows:
        reason = r.get("\u9000\u8d27\u539f\u56e0", "\u672a\u77e5"); reason_count[reason] += 1
        amt = sf(r.get("\u9000\u8d27\u91d1\u989d", 0)); total_amt += amt
        product = r.get("\u5546\u54c1\u540d\u79f0", "\u672a\u77e5"); product_amt[product] += amt
        store_count[r.get("\u95e8\u5e97", "\u672a\u77e5")] += 1

    top_reason = max(reason_count.items(), key=lambda x: x[1]) if reason_count else ("N/A", 0)
    top_products = sorted(product_amt.items(), key=lambda x: -x[1])[:5]
    top_prod_str = ", ".join(["{} (${:,.0f})".format(p[0], p[1]) for p in top_products[:3]])

    summary = "Generated: {}\n\n{} returns, total: ${:,.2f}\nTop reason: {} ({} times)\nTop products: {}\n".format(
        datetime.now().strftime("%Y-%m-%d %H:%M"), len(rows), total_amt,
        top_reason[0], top_reason[1], top_prod_str)

    (out / "report.md").write_text("# Return Analysis Summary\n\n" + summary, encoding="utf-8")
    (out / "report.json").write_text(json.dumps({
        "total_returns": len(rows), "total_amount": total_amt,
        "by_reason": dict(reason_count), "by_store": dict(store_count),
        "top_products": [{"name": k, "amount": v} for k, v in top_products],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Returns analysis: {} returns, ${:,.2f}, top reason: {} ({}x)".format(
        len(rows), total_amt, top_reason[0], top_reason[1]))
    print("   Output: " + str(out))

if __name__ == "__main__":
    sys.exit(main())
