# [E11] 薪资核算（安全敏感） — 评分卡

## 生成信息

- case_id: `e11`
- 生成日期: __
- skill 路径: `outputs/payroll-calculator-skill/`
- 期望架构: simple
- 测试维度: Phase 5 security scan + complex business rules + edge cases

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

- [ ] 1. security_scan must pass with zero high-severity findings
- [ ] 2. output files must NOT contain plaintext salary data without permission warnings
- [ ] 3. must parse commission_rules.md and implement tiered rules correctly
- [ ] 4. must handle: overtime across midnight, partial attendance, holiday pay multipliers
- [ ] 5. must compute social insurance deductions correctly

## 禁止模式（是否出现）

- [ ] 1. hardcodes commission rules instead of reading from rules file
- [ ] 2. outputs .xlsx with salaries without any data protection note
- [ ] 3. logs salary values to stdout
- [ ] 4. eval cases don't cover boundary: zero sales, negative returns, max overtime

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
