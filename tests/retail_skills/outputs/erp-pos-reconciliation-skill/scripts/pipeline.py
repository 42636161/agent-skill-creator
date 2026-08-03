#!/usr/bin/env python3
import argparse, csv, json, sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--erp", required=True); p.add_argument("--pos", required=True)
    p.add_argument("--output", required=True)
    return p.parse_args()

def sf(v, d=0.0):
    try: return float(v)
    except: return d

def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def main():
    args = parse_args(); out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    erp = load(args.erp); pos = load(args.pos)

    # Match by transaction ID
    erp_ids = {r.get("单据编号", "").strip(): r for r in erp}
    pos_ids = {r.get("交易号", "").strip(): r for r in pos}

    matched = []; erp_only = []; pos_only = []; amount_diff = []

    for eid, er in erp_ids.items():
        if eid in pos_ids:
            pr = pos_ids[eid]
            erp_amt = sf(er.get("销售金额", 0))
            pos_amt = sf(pr.get("实收金额", 0))
            if abs(erp_amt - pos_amt) > max(erp_amt * 0.02, 1.0):
                amount_diff.append({"id": eid, "erp": erp_amt, "pos": pos_amt, "diff": round(erp_amt - pos_amt, 2)})
            else:
                matched.append(eid)
        else:
            erp_only.append(eid)

    for pid in pos_ids:
        if pid not in erp_ids:
            pos_only.append(pid)

    summary = "Reconciliation: {} matched, {} ERP-only, {} POS-only, {} amount diffs".format(
        len(matched), len(erp_only), len(pos_only), len(amount_diff))

    report = [
        "# ERP-POS Reconciliation Report",
        "", "Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M"), "",
        "## Summary", "", summary, "",
        "## Discrepancies",
    ]
    for d in amount_diff[:20]:
        report.append("- {} ERP: {:.2f} POS: {:.2f} Diff: {:.2f}".format(d["id"], d["erp"], d["pos"], d["diff"]))

    (out / "report.md").write_text("\n".join(report), encoding="utf-8")
    (out / "report.json").write_text(json.dumps({
        "matched": len(matched), "erp_only": len(erp_only), "pos_only": len(pos_only),
        "amount_diffs": len(amount_diff), "details": amount_diff[:50],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(summary)
    print("   Output: " + str(out))

if __name__ == "__main__":
    sys.exit(main())
