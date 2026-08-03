# [A2] 竞品价格监控（京东/天猫） — 评分卡

## 生成信息

- case_id: `a2`
- 生成日期: __
- skill 路径: `outputs/competitor-price-monitor-skill/`
- 期望架构: simple
- 测试维度: Phase 1 non-English API discovery and selection

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

- [ ] 1. Phase 1 must search for Chinese retail APIs (京东开放平台, 淘宝开放平台)
- [ ] 2. must identify that scraping is NOT the primary approach (APIs exist)
- [ ] 3. skill must include API auth instructions for Chinese platforms
- [ ] 4. must handle rate limits and anti-bot measures

## 禁止模式（是否出现）

- [ ] 1. falls back to web scraping without checking APIs first
- [ ] 2. ignores Chinese retail ecosystem entirely (suggests Amazon API)
- [ ] 3. no API auth/rate limit documentation

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
