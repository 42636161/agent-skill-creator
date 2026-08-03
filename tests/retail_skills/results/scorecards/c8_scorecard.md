# [C8] 单店排班优化 — 评分卡

## 生成信息

- case_id: `c8`
- 生成日期: __
- skill 路径: `outputs/shift-scheduler-skill/`
- 期望架构: simple
- 测试维度: Phase 3 correctly keeping simple task as simple skill

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

- [ ] 1. must stay as simple skill (not suite) — it's one pipeline
- [ ] 2. must generate weekly shift table from traffic data
- [ ] 3. must respect peak/off-peak staffing ratios
- [ ] 4. output must be a readable schedule table

## 禁止模式（是否出现）

- [ ] 1. over-engineers into suite with separate traffic-analyzer, shift-generator, validator skills
- [ ] 2. SKILL.md exceeds 500 lines for a ~300 line problem
- [ ] 3. generates complex optimization algorithms when simple rule-based suffices

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
