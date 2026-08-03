---
name: store-daily-report-skill
description: >-
  A retail report generator that creates daily store reports from multi-sheet Excel files. Activates
  when users need to automate daily sales, returns, member, and promotion
  reporting from spreadsheet data. Triggers on: 门店日报, 销售日报, 每日报表,
  daily store report, 自动化报表, 卖场日报.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-31
  last_reviewed: 2026-07-31
  review_interval_days: 90
---
# /store-daily-report — 门店日报自动生成

从多 sheet 的零售 Excel 文件中提取销售、退货、会员、促销数据，生成人读摘要 + 结构化报表。

## Quick Profile
- **Category**: Data Analysis / Retail
- **Input**: Multi-sheet .xlsx file with sheets 销售明细, 退货, 会员, 促销
- **Output**: report.md (executive summary), report.json (structured data), report.csv (tabular data)
- **When to use**: Daily/weekly retail store performance reporting, multi-dimension sales analysis
- **When not**: When data is not in the expected 4-sheet Excel format, or when real-time dashboard is needed
 含「销售明细」「退货」「会员」「促销」四个 sheet 的 .xlsx 文件
- **输出**: `report.md`（含执行摘要）、`report.json`（机器可读）、`report.csv`（表格数据）
- **语言**: 中文输出，代码英文

## How to run it

```bash
python3 scripts/pipeline.py --input 门店销售_202607.xlsx --output ./reports/
python3 scripts/pipeline.py --input 门店销售_202607.xlsx --output ./reports/ --date 2026-07-15
```

## Runtime Contract

- **正常使用**: 只运行 `python3 scripts/pipeline.py --input <file> --output <dir> [--date YYYY-MM-DD]`
- **scripts/ 是实现细节，默认不读**。仅在排障或扩展功能时才需要阅读 `scripts/pipeline.py`
- 输出位于 `--output` 指定的目录下：`report.md` / `report.json` / `report.csv`

## Workflow

1. 加载 Excel，自动识别四个 sheet
2. 聚合销售数据（按门店、品类、支付方式）
3. 分析退货（退货率、原因分布、高退货商品）
4. 统计会员（等级分布、人均消费）
5. 检查促销活动（进行中/即将开始）
6. 生成人读摘要（`report.md` 以"本周结论"开头）和机器可读数据

## Output Example

`report.md` 以执行摘要开头：

```
## 本周结论

报告日期：2026-07-15  |  生成时间：2026-07-31 16:30

### 销售总览
当日共 58 笔交易，销售额 ¥23,450.80，客单价 ¥404.32。
销售冠军门店：朝阳大悦城店（¥5,230.50），销售冠军品类：生鲜（¥8,120.30）。
会员消费占比 62.3%。

### 退货分析
🟡 退货 5 件，金额 ¥680.00（退货率 2.9%）。主要原因：质量问题（3次）。

### 会员动态
会员总数 200 人。等级分布：普通 80人（人均消费 ¥150），银卡 70人（人均消费 ¥380），金卡 40人（人均消费 ¥820），钻石 10人（人均消费 ¥2,100）。

### 进行中促销
• 暑期清凉节（满减，饮料/冷冻食品，折扣 15%）
```

## Eval

```bash
python3 scripts/run_evals.py --rollout     # 跑所有 golden cases
python3 scripts/run_evals.py --promote     # 标记首次通过的 baseline
python3 scripts/evolve.py                  # 依赖检查 + rollout
```
