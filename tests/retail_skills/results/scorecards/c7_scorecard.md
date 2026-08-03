# [C7] 月度经营分析（多维度suite） — 评分卡

## 生成信息

- case_id: `c7`
- 生成日期: __
- skill 路径: `outputs/monthly-ops-analysis-suite/`
- 期望架构: complex_suite
- 测试维度: Phase 3 correct classification as complex suite vs single skill

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

- [ ] 1. must be structured as a SUITE with 4+ component skills, not one giant SKILL.md
- [ ] 2. each component must have its own SKILL.md under suite root
- [ ] 3. must include a master orchestrator that runs all 4 and produces combined report
- [ ] 4. each sub-analysis must be independently usable

## 禁止模式（是否出现）

- [ ] 1. crams all 4 dimensions into single SKILL.md > 500 lines
- [ ] 2. sub-analyses are not independently invocable
- [ ] 3. no combined executive summary across all dimensions

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
