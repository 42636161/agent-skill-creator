#!/usr/bin/env python3
"""Store Daily Report Pipeline — reads multi-sheet retail Excel, produces summary report.

Invoke: python3 scripts/pipeline.py --input <excel> --output <dir>
"""

import argparse, csv, json, sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
import openpyxl

def parse_args():
    p = argparse.ArgumentParser(description="Generate daily store report from Excel.")
    p.add_argument("--input", required=True, help="Path to multi-sheet Excel file")
    p.add_argument("--output", required=True, help="Output directory for reports")
    p.add_argument("--date", help="Filter to specific date (YYYY-MM-DD), default: all dates")
    return p.parse_args()

def load_excel(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    sheets = {}
    for name in wb.sheetnames:
        ws = wb[name]
        rows = list(ws.iter_rows(min_row=2, values_only=True))  # skip header
        sheets[name] = {"headers": [c.value for c in ws[1]], "rows": rows}
    return sheets

def safe_float(v, default=0.0):
    try: return float(v)
    except (TypeError, ValueError): return default

def safe_int(v, default=0):
    try: return int(v)
    except (TypeError, ValueError): return default

# ── Analysis functions ──────────────────────────────────────────────────────

def analyze_sales(rows, filter_date=None):
    """Aggregate sales by store, category, and payment method."""
    by_store = defaultdict(lambda: {"txns": 0, "qty": 0, "revenue": 0.0})
    by_category = defaultdict(lambda: {"txns": 0, "revenue": 0.0})
    payment = defaultdict(float)
    member_sales, non_member_sales = 0.0, 0.0
    total_txns, total_revenue = 0, 0.0

    for row in rows:
        d_str, store, sku, name, cat, subcat, qty, price, amt, method, member = row
        if filter_date and str(d_str) != filter_date:
            continue
        rev = safe_float(amt)
        q = safe_int(qty)
        total_txns += 1
        total_revenue += rev
        by_store[store]["txns"] += 1
        by_store[store]["qty"] += q
        by_store[store]["revenue"] += rev
        by_category[str(cat)]["txns"] += 1
        by_category[str(cat)]["revenue"] += rev
        payment[str(method)] += rev
        if member:
            member_sales += rev
        else:
            non_member_sales += rev

    return {
        "total_transactions": total_txns,
        "total_revenue": round(total_revenue, 2),
        "avg_basket": round(total_revenue / total_txns, 2) if total_txns else 0,
        "by_store": {k: {"txns": v["txns"], "revenue": round(v["revenue"], 2)} for k, v in sorted(by_store.items())},
        "by_category": {k: {"txns": v["txns"], "revenue": round(v["revenue"], 2)} for k, v in sorted(by_category.items(), key=lambda x: -x[1]["revenue"])},
        "payment_methods": {k: round(v, 2) for k, v in sorted(payment.items(), key=lambda x: -x[1])},
        "member_ratio": round(member_sales / total_revenue, 3) if total_revenue else 0,
    }

def analyze_returns(rows, filter_date=None):
    """Summarize returns — rate, reasons, top returned products."""
    total_qty, total_amt = 0, 0.0
    reasons = defaultdict(lambda: {"count": 0, "amount": 0.0})
    by_product = defaultdict(lambda: {"qty": 0, "amount": 0.0})

    for row in rows:
        d_str, store, sku, name, qty, amt, reason, orig_date = row
        if filter_date and str(d_str) != filter_date:
            continue
        q = safe_int(qty)
        a = safe_float(amt)
        total_qty += q
        total_amt += a
        reasons[str(reason)]["count"] += 1
        reasons[str(reason)]["amount"] += a
        by_product[str(name)]["qty"] += q
        by_product[str(name)]["amount"] += a

    return {
        "total_returns": total_qty,
        "total_return_amount": round(total_amt, 2),
        "by_reason": {k: {"count": v["count"], "amount": round(v["amount"], 2)} for k, v in sorted(reasons.items(), key=lambda x: -x[1]["count"])},
        "top_returned_products": [{"name": k, "qty": v["qty"], "amount": round(v["amount"], 2)} for k, v in sorted(by_product.items(), key=lambda x: -x[1]["amount"])[:5]],
    }

def analyze_members(rows):
    """Member tier distribution and spending."""
    tiers = defaultdict(lambda: {"count": 0, "total_points": 0, "total_spending": 0.0})
    total_members = 0

    for row in rows:
        mid, name, gender, phone, reg_date, tier, points, spending = row
        total_members += 1
        t = str(tier)
        tiers[t]["count"] += 1
        tiers[t]["total_points"] += safe_int(points)
        tiers[t]["total_spending"] += safe_float(spending)

    return {
        "total_members": total_members,
        "by_tier": {k: {"count": v["count"], "avg_spending": round(v["total_spending"] / v["count"], 2) if v["count"] else 0} for k, v in sorted(tiers.items())},
    }

def analyze_promotions(rows, filter_date=None):
    """Active promotions for the target date."""
    active = []
    upcoming = []
    target = datetime.strptime(filter_date, "%Y-%m-%d").date() if filter_date else date.today()

    for row in rows:
        name, start_s, end_s, ptype, scope, discount, sku_count, budget = row
        start_d = datetime.strptime(str(start_s)[:10], "%Y-%m-%d").date()
        end_d = datetime.strptime(str(end_s)[:10], "%Y-%m-%d").date()
        info = {"name": str(name), "type": str(ptype), "scope": str(scope), "discount": safe_float(discount), "budget": safe_float(budget)}
        if start_d <= target <= end_d:
            active.append(info)
        elif start_d > target:
            upcoming.append(info)

    return {"active_promotions": active, "upcoming_promotions": upcoming}

# ── Report generation ───────────────────────────────────────────────────────

def generate_summary(sales, returns, members, promos, filter_date):
    """Generate human-readable executive summary text."""
    lines = []
    display_date = filter_date or "全部日期"

    # Top-line
    lines.append(f"## 本周结论")
    lines.append(f"")
    lines.append(f"报告日期：{display_date}  |  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"")

    # Sales summary
    top_store = list(sales["by_store"].items())[0] if sales["by_store"] else ("N/A", {"revenue": 0})
    top_cat = list(sales["by_category"].items())[0] if sales["by_category"] else ("N/A", {"revenue": 0})
    lines.append(f"### 销售总览")
    lines.append(f"当日共 {sales['total_transactions']} 笔交易，销售额 ¥{sales['total_revenue']:,.2f}，")
    lines.append(f"客单价 ¥{sales['avg_basket']:.2f}。")
    lines.append(f"销售冠军门店：{top_store[0]}（¥{top_store[1]['revenue']:,.2f}），")
    lines.append(f"销售冠军品类：{top_cat[0]}（¥{top_cat[1]['revenue']:,.2f}）。")
    lines.append(f"会员消费占比 {sales['member_ratio']:.1%}。")
    lines.append(f"")

    # Returns
    if returns["total_returns"] > 0:
        top_reason = list(returns["by_reason"].items())[0] if returns["by_reason"] else ("N/A", {"count": 0})
        ret_rate = returns["total_return_amount"] / sales["total_revenue"] if sales["total_revenue"] else 0
        color = "🔴" if ret_rate > 0.05 else "🟡" if ret_rate > 0.02 else "🟢"
        lines.append(f"### 退货分析")
        lines.append(f"{color} 退货 {returns['total_returns']} 件，金额 ¥{returns['total_return_amount']:,.2f}（退货率 {ret_rate:.1%}）。")
        lines.append(f"主要原因：{top_reason[0]}（{top_reason[1]['count']} 次）。")
        if ret_rate > 0.05:
            lines.append(f"⚠️ 退货率超过 5%，建议核查 {', '.join([p['name'] for p in returns['top_returned_products'][:3]])}。")
        lines.append(f"")

    # Members
    lines.append(f"### 会员动态")
    lines.append(f"会员总数 {members['total_members']} 人。")
    tier_lines = [f"{t} {v['count']}人（人均消费 ¥{v['avg_spending']:.0f}）" for t, v in members["by_tier"].items()]
    lines.append(f"等级分布：{'，'.join(tier_lines)}。")
    lines.append(f"")

    # Promotions
    if promos["active_promotions"]:
        lines.append(f"### 进行中促销")
        for p in promos["active_promotions"]:
            lines.append(f"• {p['name']}（{p['type']}，{p['scope']}，折扣 {p['discount']:.0%}）")
    else:
        lines.append(f"### 促销")
        lines.append(f"当日无进行中促销活动。")
    lines.append(f"")

    return "\n".join(lines)

def generate_report_md(summary_text, sales, returns, members, promos):
    """Full markdown report body after the summary."""
    lines = [summary_text]
    lines.append("---")
    lines.append("")

    # Sales detail table
    lines.append("## 门店销售明细")
    lines.append("| 门店 | 交易笔数 | 销售额 |")
    lines.append("|---|---|---|")
    for store, v in sales["by_store"].items():
        lines.append(f"| {store} | {v['txns']} | ¥{v['revenue']:,.2f} |")
    lines.append("")

    # Category detail
    lines.append("## 品类销售排名")
    lines.append("| 品类 | 交易笔数 | 销售额 |")
    lines.append("|---|---|---|")
    for cat, v in sales["by_category"].items():
        lines.append(f"| {cat} | {v['txns']} | ¥{v['revenue']:,.2f} |")
    lines.append("")

    # Returns detail
    if returns["total_returns"] > 0:
        lines.append("## 退货原因分布")
        lines.append("| 原因 | 次数 | 金额 |")
        lines.append("|---|---|---|")
        for reason, v in returns["by_reason"].items():
            lines.append(f"| {reason} | {v['count']} | ¥{v['amount']:,.2f} |")
        lines.append("")

    return "\n".join(lines)

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    sheets = load_excel(args.input)

    # Validate expected sheets
    expected = ["销售明细", "退货", "会员", "促销"]
    missing = [s for s in expected if s not in sheets]
    if missing:
        print(f"⚠️ 缺少 sheet: {missing}（将跳过缺失维度）", file=sys.stderr)

    sales_rows = sheets.get("销售明细", {}).get("rows", [])
    returns_rows = sheets.get("退货", {}).get("rows", [])
    members_rows = sheets.get("会员", {}).get("rows", [])
    promos_rows = sheets.get("促销", {}).get("rows", [])

    filter_date = args.date

    sales = analyze_sales(sales_rows, filter_date)
    returns = analyze_returns(returns_rows, filter_date)
    members = analyze_members(members_rows)
    promos = analyze_promotions(promos_rows, filter_date)

    # Generate summary (human-readable)
    summary_text = generate_summary(sales, returns, members, promos, filter_date)

    # Write report.md
    report_md = generate_report_md(summary_text, sales, returns, members, promos)
    (out_dir / "report.md").write_text(report_md, encoding="utf-8")

    # Write report.json (machine-readable)
    report_json = {
        "date": filter_date or "all",
        "generated_at": datetime.now().isoformat(),
        "summary_text": summary_text,
        "sales": sales,
        "returns": returns,
        "members": members,
        "promotions": promos,
        "highlights": [],
        "alerts": [],
    }
    # Add highlights and alerts
    if sales["total_revenue"] > 0:
        top_store = list(sales["by_store"].items())[0]
        report_json["highlights"].append(f"销售冠军: {top_store[0]} ¥{top_store[1]['revenue']:,.2f}")
    ret_rate = returns["total_return_amount"] / sales["total_revenue"] if sales["total_revenue"] else 0
    if ret_rate > 0.05:
        report_json["alerts"].append(f"退货率 {ret_rate:.1%} 超过 5% 警戒线")
    (out_dir / "report.json").write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write report.csv
    csv_path = out_dir / "report.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["维度", "指标", "数值"])
        w.writerow(["销售", "总交易数", sales["total_transactions"]])
        w.writerow(["销售", "总销售额", sales["total_revenue"]])
        w.writerow(["销售", "客单价", sales["avg_basket"]])
        for store, v in sales["by_store"].items():
            w.writerow(["门店销售", store, v["revenue"]])
        w.writerow(["退货", "退货件数", returns["total_returns"]])
        w.writerow(["退货", "退货金额", returns["total_return_amount"]])
        w.writerow(["会员", "总人数", members["total_members"]])

    # Print human-readable summary to stdout
    print(f"📊 门店日报已生成")
    print(f"   日期: {filter_date or '全部'}")
    print(f"   销售额: ¥{sales['total_revenue']:,.2f} ({sales['total_transactions']} 笔)")
    print(f"   退货: {returns['total_returns']} 件 ¥{returns['total_return_amount']:,.2f}")
    print(f"   会员: {members['total_members']} 人")
    print(f"   输出: {out_dir}/report.md  {out_dir}/report.json  {out_dir}/report.csv")
    if report_json["alerts"]:
        for alert in report_json["alerts"]:
            print(f"   ⚠️  {alert}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
