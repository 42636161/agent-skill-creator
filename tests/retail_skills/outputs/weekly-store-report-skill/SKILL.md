---
name: weekly-store-report-skill
description: >-
  A retail analytics pipeline that generates weekly store performance reports
  from three data sources. Activates when users need multi-audience weekly
  reports, store KPI dashboards, or executive briefs from CSV exports.
  Triggers on: 门店周报, 每周报告, weekly store report, 多格式报表, 经营周报.
license: MIT
activation: /weekly-store-report
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
  provenance:
    maintainer: agent-skill-creator
    source_references: []
---
# /weekly-store-report — 多格式门店周报

从三份 CSV 导出文件生成三种受众专属的周报：店长运营版、区域经理对比表、总部一页摘要。

## Quick Profile

- **Category**: Data Analysis / Retail / Reporting
- **Input**: Three CSV files — store_sales.csv (sales KPI), customer_feedback.csv (satisfaction), inventory_snapshot.csv (stock health)
- **Output**: Three differentiated reports — store manager (detailed), region manager (tabular comparison), executive brief (one-page summary)
- **When to use**: Weekly store performance review, multi-level reporting chain, data-driven retail operations meeting
- **When not**: When data is real-time streaming, or when only one audience needs the report

## How to run it

```bash
python3 scripts/pipeline.py \
  --sales store_sales.csv \
  --feedback customer_feedback.csv \
  --inventory inventory_snapshot.csv \
  --output ./reports/ \
  --week 2026-07-24
```

## Runtime Contract

- **正常使用**: 只运行上述命令。`scripts/` 是实现细节，默认不读 (do not read by default).
- 输出位于 `--output` 目录：`report_store_manager.md`、`report_region_manager.md`、`report_executive.md`、`report.json`
- `report_executive.md` 以「本周结论」开头，为规则生成可复现摘要，不依赖 LLM。
- stdout 打印人读摘要，非 JSON 原始数据。
- Output: report_store_manager.md + report_region_manager.md + report_executive.md + report.json in --output directory
- Primary anchor: report_executive.md — one-page executive summary for headquarters
- stdout: Human-readable summary with week period, total sales, and key metrics

### Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion based on: weekly period and total revenue.

2. Show the primary breakdown. Render a table of top 5 stores by sales performance.

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one follow-up that reveals an unrequested capability. Choose a question connected to the data that hints at another analysis this skill can do but the user has not asked for yet.

## Output Example

```
📊 门店周报已生成
   周期: 2026-07-24 ~ 2026-07-24
   总销售额: ¥287,450.30
   顾客满意度: 4.1/5
   库存预警: 12 低库存, 3 过期
   输出:
     店长版:  ./reports/report_store_manager.md
     区域经理: ./reports/report_region_manager.md
     总部摘要: ./reports/report_executive.md
     机器数据: ./reports/report.json
```

**report_executive.md** starts with executive summary:

```
# 本周结论 — 总部摘要

报告周期：2026-07-24 ~ 2026-07-24

## 核心指标

本周 6 家门店总销售额 ¥287,450.30。

- 🏆 销售冠军：朝阳大悦城店（¥58,230.00）
- ⚠️ 销售垫底：通州万达店（¥32,100.00）
- ⭐ 顾客满意度：平均 4.1/5
```

## Tuning

This skill has no configurable parameters — it works with default behavior out of the box.
