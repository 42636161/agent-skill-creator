#!/usr/bin/env python3
import argparse, csv, json, sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime, date

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--transactions", required=True); p.add_argument("--output", required=True)
    p.add_argument("--bins", type=int, default=5)
    return p.parse_args()

def sf(v, d=0.0):
    try: return float(v)
    except: return d

def si(v, d=0):
    try: return int(v)
    except: return d

def quantile_score(values, bins, reverse=False):
    sorted_v = sorted(values)
    n = len(sorted_v)
    def score(v):
        for i in range(bins):
            thresh = sorted_v[int(n * (i + 1) / bins) - 1] if i < bins - 1 else float('inf')
            if v <= thresh:
                return bins - i if reverse else i + 1
        return 1
    return [score(v) for v in values]

def main():
    args = parse_args(); out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    with open(args.transactions, encoding="utf-8-sig") as f:
        txns = list(csv.DictReader(f))

    # Aggregate per member
    mem = defaultdict(lambda: {"recency": 999, "frequency": 0, "monetary": 0.0})
    today = date.today()
    for t in txns:
        mid = t.get("会员ID", "").strip()
        if not mid: continue
        d_str = t.get("交易日期", "").strip()
        try: t_date = datetime.strptime(d_str[:10], "%Y-%m-%d").date()
        except: continue
        days = (today - t_date).days
        mem[mid]["recency"] = min(mem[mid]["recency"], days)
        mem[mid]["frequency"] += 1
        mem[mid]["monetary"] += sf(t.get("交易金额", 0))

    mids = list(mem.keys())
    r_scores = quantile_score([mem[m]["recency"] for m in mids], args.bins, reverse=True)
    f_scores = quantile_score([mem[m]["frequency"] for m in mids], args.bins)
    m_scores = quantile_score([mem[m]["monetary"] for m in mids], args.bins)

    results = []
    for i, mid in enumerate(mids):
        rfm = r_scores[i] + f_scores[i] + m_scores[i]
        if rfm >= args.bins * 2.5: seg = "High Value"
        elif rfm >= args.bins * 1.5: seg = "Active"
        elif rfm >= args.bins * 0.8: seg = "At Risk"
        else: seg = "Dormant"
        results.append({"member_id": mid, "R": r_scores[i], "F": f_scores[i], "M": m_scores[i],
                       "rfm_total": rfm, "segment": seg, "monetary": round(mem[mid]["monetary"], 2)})

    seg_counts = defaultdict(int)
    for r in results: seg_counts[r["segment"]] += 1

    lines = ["# RFM Segmentation Report", "", "## Summary", ""]
    for seg, cnt in seg_counts.items():
        lines.append("- {}: {} members".format(seg, cnt))

    recs = {"High Value": "VIP treatment, exclusive offers", "Active": "Upsell, cross-sell",
            "At Risk": "Win-back campaign, reactivation offer", "Dormant": "Low-cost re-engagement"}
    lines.append(""); lines.append("## Recommendations")
    for seg, rec in recs.items():
        if seg in seg_counts:
            lines.append("- **{}**: {}".format(seg, rec))

    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "report.json").write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8")

    print("RFM: {} members, {} segments".format(len(results), len(seg_counts)))
    print("   Output: " + str(out))

if __name__ == "__main__":
    sys.exit(main())
