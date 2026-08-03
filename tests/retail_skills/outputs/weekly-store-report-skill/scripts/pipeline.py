#!/usr/bin/env python3
"""Weekly Store Report Pipeline — 3 inputs, 3 audience-specific outputs.

Usage:
    python3 scripts/pipeline.py --sales <csv> --feedback <csv> --inventory <csv> --output <dir> [--week YYYY-MM-DD]
"""
import argparse, csv, json, sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--sales", required=True)
    p.add_argument("--feedback", required=True)
    p.add_argument("--inventory", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--week", help="Start date of the week (YYYY-MM-DD)")
    return p.parse_args()

def load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [row for row in reader if any(v.strip() for v in row.values())]  # skip blank rows

def sf(v, default=0.0):
    try: return float(v)
    except: return default

def si(v, default=0):
    try: return int(v)
    except: return default

def week_range(start_str):
    d = datetime.strptime(start_str, "%Y-%m-%d").date()
    return [str(d + timedelta(days=i)) for i in range(7)]

# ── Analysis ─────────────────────────────────────────────────────────────────

def analyze_sales(rows, week_dates=None):
    by_store = defaultdict(lambda: {"revenue": 0.0, "txns": 0, "traffic": 0, "margin": 0.0})
    total = 0.0
    for r in rows:
        d = r.get("日期", "").strip()
        if week_dates and d not in week_dates:
            continue
        store = r.get("门店", "")
        rev = sf(r.get("销售额"))
        txns = si(r.get("交易笔数"))
        traffic = si(r.get("客流量"))
        margin = sf(r.get("毛利率"))
        total += rev
        by_store[store]["revenue"] += rev
        by_store[store]["txns"] += txns
        by_store[store]["traffic"] += traffic
        by_store[store]["margin"] = max(by_store[store]["margin"], margin)
    return {"total_revenue": round(total, 2), "by_store": dict(by_store)}

def analyze_feedback(rows, week_dates=None):
    by_dim = defaultdict(list)
    by_store = defaultdict(list)
    for r in rows:
        d = r.get("日期", "").strip()
        if week_dates and d not in week_dates:
            continue
        by_dim[r.get("评价维度", "")].append(si(r.get("评分")))
        by_store[r.get("门店", "")].append(si(r.get("评分")))
    dim_avg = {k: round(sum(v)/len(v), 2) for k, v in by_dim.items()}
    store_avg = {k: round(sum(v)/len(v), 2) for k, v in by_store.items()}
    return {"by_dimension": dim_avg, "by_store": store_avg}

def analyze_inventory(rows):
    alerts = []
    by_store = defaultdict(lambda: {"low_stock": 0, "expiry_warn": 0, "total_sku": 0})
    for r in rows:
        store = r.get("门店", "")
        low = si(r.get("低库存SKU数"))
        exp = si(r.get("过期预警SKU数"))
        sku = si(r.get("SKU数"))
        by_store[store]["low_stock"] += low
        by_store[store]["expiry_warn"] += exp
        by_store[store]["total_sku"] += sku
        if low > 5:
            alerts.append(f"{store} {r.get('品类','')} 低库存SKU {low} 个")
        if exp > 0:
            alerts.append(f"{store} {r.get('品类','')} 过期预警 {exp} 个")
    return {"by_store": dict(by_store), "alerts": alerts[:10]}

# ── Output generators (3 audiences) ──────────────────────────────────────────

def gen_store_manager_report(sales, feedback, inv, week_label):
    """Detailed operational view for store manager."""
    lines = [f"# 门店运营周报 — 店长版", f"", f"报告周期：{week_label}  |  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", f""]
    lines.append("## 本周销售明细")
    lines.append("| 门店 | 销售额 | 交易数 | 客流 | 毛利率 |")
    lines.append("|---|---|---|---|---|")
    for store, v in sorted(sales["by_store"].items()):
        lines.append(f"| {store} | ¥{v['revenue']:,.2f} | {v['txns']} | {v['traffic']} | {v['margin']:.1%} |")
    lines.append("")

    lines.append("## 顾客满意度")
    lines.append("| 门店 | 平均评分 |")
    lines.append("|---|---|")
    for store, score in sorted(feedback["by_store"].items()):
        lines.append(f"| {store} | {score} ⭐ |")
    lines.append("")

    if inv["alerts"]:
        lines.append("## ⚠️ 库存预警")
        for a in inv["alerts"]:
            lines.append(f"- {a}")
        lines.append("")
    return "\n".join(lines)

def gen_region_manager_report(sales, feedback, inv, week_label):
    """Tabular comparison for regional manager."""
    lines = [f"# 区域经理周报对比表 — {week_label}", f""]
    # Per store KPI table
    lines.append("## 门店KPI对比")
    lines.append("| 门店 | 销售额 | 交易数 | 客单价 | 顾客评分 | 低库存SKU | 过期预警 |")
    lines.append("|---|---|---|---|---|---|---|")
    for store, v in sorted(sales["by_store"].items()):
        asp = round(v["revenue"] / v["txns"], 2) if v["txns"] else 0
        score = feedback["by_store"].get(store, "-")
        inv_s = inv["by_store"].get(store, {})
        lines.append(f"| {store} | ¥{v['revenue']:,.2f} | {v['txns']} | ¥{asp:.2f} | {score} | {inv_s.get('low_stock',0)} | {inv_s.get('expiry_warn',0)} |")
    lines.append("")

    # Category-level inventory
    lines.append("## 库存健康度总览")
    lines.append("| 门店 | 总SKU数 | 低库存SKU | 过期预警SKU |")
    lines.append("|---|---|---|---|")
    for store, v in sorted(inv["by_store"].items()):
        lines.append(f"| {store} | {v['total_sku']} | {v['low_stock']} | {v['expiry_warn']} |")
    lines.append("")
    return "\n".join(lines)

def gen_executive_brief(sales, feedback, inv, week_label):
    """One-page executive summary for HQ."""
    total = sales["total_revenue"]
    n_stores = len(sales["by_store"])
    top_store = max(sales["by_store"].items(), key=lambda x: x[1]["revenue"])
    worst_store = min(sales["by_store"].items(), key=lambda x: x[1]["revenue"])
    avg_score = sum(feedback["by_store"].values()) / len(feedback["by_store"]) if feedback["by_store"] else 0
    total_low = sum(v["low_stock"] for v in inv["by_store"].values())
    total_exp = sum(v["expiry_warn"] for v in inv["by_store"].values())
    top_score_store = max(feedback["by_store"].items(), key=lambda x: x[1])

    lines = [
        f"# 本周结论 — 总部摘要",
        f"",
        f"报告周期：{week_label}  |  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## 核心指标",
        f"",
        f"本周 {n_stores} 家门店总销售额 **¥{total:,.2f}**。",
        f"",
        f"- 🏆 销售冠军：{top_store[0]}（¥{top_store[1]['revenue']:,.2f}）",
        f"- ⚠️ 销售垫底：{worst_store[0]}（¥{worst_store[1]['revenue']:,.2f}）",
        f"- ⭐ 顾客满意度：平均 {avg_score:.1f}/5，最高为 {top_score_store[0]}（{top_score_store[1]}分）",
        f"",
        f"## 库存风险",
        f"",
    ]
    if total_low > 0:
        lines.append(f"- 🔴 低库存预警：共 {total_low} 个 SKU 需要补货")
    if total_exp > 0:
        lines.append(f"- 🟡 过期预警：共 {total_exp} 个 SKU 临近过期")
    if total_low == 0 and total_exp == 0:
        lines.append(f"- 🟢 库存健康，无异常预警")
    lines.append("")

    if inv["alerts"]:
        lines.append(f"## 待处理事项")
        for a in inv["alerts"][:5]:
            lines.append(f"- {a}")
        lines.append("")

    return "\n".join(lines)

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    week_dates = set(week_range(args.week)) if args.week else None
    week_label = f"{args.week} ~ {args.week}" if args.week else "全量数据"

    sales = analyze_sales(load_csv(args.sales), week_dates)
    feedback = analyze_feedback(load_csv(args.feedback), week_dates)
    inv = analyze_inventory(load_csv(args.inventory))

    # 3 audience-specific outputs
    (out / "report_store_manager.md").write_text(
        gen_store_manager_report(sales, feedback, inv, week_label), encoding="utf-8")
    (out / "report_region_manager.md").write_text(
        gen_region_manager_report(sales, feedback, inv, week_label), encoding="utf-8")
    brief = gen_executive_brief(sales, feedback, inv, week_label)
    (out / "report_executive.md").write_text(brief, encoding="utf-8")

    # JSON machine-readable
    (out / "report.json").write_text(json.dumps({
        "week": week_label,
        "generated_at": datetime.now().isoformat(),
        "summary": brief,
        "sales": sales,
        "feedback": feedback,
        "inventory": inv,
        "alerts": inv["alerts"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print human-readable summary
    total = sales["total_revenue"]
    avg_score = sum(feedback["by_store"].values()) / len(feedback["by_store"]) if feedback["by_store"] else 0
    print(f"📊 门店周报已生成")
    print(f"   周期: {week_label}")
    print(f"   总销售额: ¥{total:,.2f}")
    print(f"   顾客满意度: {avg_score:.1f}/5")
    print(f"   库存预警: {sum(v['low_stock'] for v in inv['by_store'].values())} 低库存, {sum(v['expiry_warn'] for v in inv['by_store'].values())} 过期")
    print(f"   输出:")
    print(f"     店长版:  {out}/report_store_manager.md")
    print(f"     区域经理: {out}/report_region_manager.md")
    print(f"     总部摘要: {out}/report_executive.md")
    print(f"     机器数据: {out}/report.json")

if __name__ == "__main__":
    sys.exit(main())
