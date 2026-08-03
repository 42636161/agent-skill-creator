# [B6] 会员RFM分层 — 评分卡

## 生成信息

- case_id: `b6`
- 生成日期: __
- skill 路径: `outputs/member-rfm-segmenter-skill/`
- 期望架构: simple
- 测试维度: Phase 2 correct parameterization of standard methods

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

- [ ] 1. must compute Recency (days since last purchase), Frequency, Monetary correctly
- [ ] 2. must provide configurable scoring method (quantile vs fixed thresholds)
- [ ] 3. must produce segment profiles with actionable marketing recommendations
- [ ] 4. must handle members with zero/few transactions gracefully

## 禁止模式（是否出现）

- [ ] 1. hardcodes bin thresholds (should be configurable or auto-computed)
- [ ] 2. uses arbitrary percentile cutoffs without explanation
- [ ] 3. no segment-specific recommendations
- [ ] 4. crashes on members with single transaction

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
