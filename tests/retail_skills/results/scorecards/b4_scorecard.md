# [B4] 促销ROI分析 — 评分卡

## 生成信息

- case_id: `b4`
- 生成日期: __
- skill 路径: `outputs/promo-roi-analyzer-skill/`
- 期望架构: simple
- 测试维度: Phase 2 analysis design precision for domain-specific math

## 自动评分结果

| 维度 | 结果 | 详情 |
|---|---|---|
| validate.py | PASS / FAIL | 错误数:__, 警告数:__ |
| security_scan.py | PASS / FAIL | 发现数:__, 高危:__ |
| 文件结构 | PASS / FAIL | 问题: __ |
| 架构决策 | PASS / FAIL | 期望/实际: __ |
| 输出质量 | PASS / FAIL | 问题: __ |
| 反模式检查 | PASS / FAIL | 发现: __ |
| **综合等级** | **__** | **__/6** |

## 关键检查项（逐项核验）

- [ ] 1. must compute baseline sales (pre-promo average) correctly
- [ ] 2. must compute lift = (promo_sales - baseline) / baseline
- [ ] 3. must estimate cannibalization from post-promo dip
- [ ] 4. must compute ROI = (incremental_profit - marketing_cost) / marketing_cost
- [ ] 5. eval golden cases must include: zero lift, negative ROI, missing baseline period

## 禁止模式（是否出现）

- [ ] 1. simplifies ROI to (promo_sales / marketing_cost) without baseline subtraction
- [ ] 2. ignores post-promo cannibalization effect
- [ ] 3. no baseline logic (just compares two raw numbers)
- [ ] 4. eval cases only test happy path

## 人工审查笔记

- SKILL.md 线条数: __
- 有无 Runtime Contract: __
- description 含中文术语: __
- 输出格式是否可读: __
- 其他发现: 

## creator 缺陷定位

   （此 case 暴露的 creator 提示问题，映射到具体文件/行）

- 文件: __
- 行/段: __
- 问题描述: __
- 建议修改: __
