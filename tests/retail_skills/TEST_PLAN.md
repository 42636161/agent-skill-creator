# 零售企业 Skill 生成测试计划

> 目标：用 12 个零售企业真实场景测试 agent-skill-creator 的生成质量，通过 skill 缺陷反向定位 creator 的提示优化点。

## 测试流程（每个 case）

1. 打开新对话，输入 `/agent-skill-creator` + case 材料

2. 等 creator 完成生成，将产出 skill 目录复制到 `outputs/<skill-name>/`

3. 运行 `python3 tests/retail_skills/score_skill.py <case_id> outputs/<skill-name>/`

4. 将评分结果填入下方对应 case 的表格

5. 12 个 case 全部跑完后，运行汇总评分并填写总结


---

## Case A1 — 门店日报自动化

| 项目 | 内容 |
|---|---|
| case_id | `a1` |
| 测试维度 | Phase 1 token waste when no API exists |
| 输入类型 | file_only |
| 生成 prompt | `每天都要做这个表，帮我自动化` |
| 上传文件 | `data/a1_daily_report/门店销售_202607.xlsx` |
| 期望 skill 名 | `store-daily-report-skill` |
| 期望架构 | simple |
| 关键检查项 | 1. skill must NOT contain references/api-guide.md (no API needed)  2. skill must parse 4 Excel sheets correctly  3. output must include human-readable daily summary  4. phase 1 should recognize file-only input and skip API search |
| 禁止模式 | 1. generates api-guide.md with public API recommendations  2. treats .xlsx as CSV (loses sheet structure)  3. outputs raw data table without summary |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

## Case A2 — 竞品价格监控（京东/天猫）

| 项目 | 内容 |
|---|---|
| case_id | `a2` |
| 测试维度 | Phase 1 non-English API discovery and selection |
| 输入类型 | text_only |
| 生成 prompt | `帮我盯一下京东和天猫上我们同类产品的价格变化，每周出个对比表` |
| 上传文件 | 无 |
| 期望 skill 名 | `competitor-price-monitor-skill` |
| 期望架构 | simple |
| 关键检查项 | 1. Phase 1 must search for Chinese retail APIs (京东开放平台, 淘宝开放平台)  2. must identify that scraping is NOT the primary approach (APIs exist)  3. skill must include API auth instructions for Chinese platforms  4. must handle rate limits and anti-bot measures |
| 禁止模式 | 1. falls back to web scraping without checking APIs first  2. ignores Chinese retail ecosystem entirely (suggests Amazon API)  3. no API auth/rate limit documentation |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

## Case A3 — ERP与POS对账

| 项目 | 内容 |
|---|---|
| case_id | `a3` |
| 测试维度 | Phase 1 'data already exists' check + two-source reconciliation |
| 输入类型 | mixed |
| 生成 prompt | `我们用的是金蝶K/3，每周从系统里导出一个CSV，然后跟门店的POS数据对账` |
| 上传文件 | `data/a3_erp_recon/金蝶_导出_202607.csv` `data/a3_erp_recon/pos_sales_202607.csv` |
| 期望 skill 名 | `erp-pos-reconciliation-skill` |
| 期望架构 | simple |
| 关键检查项 | 1. must detect that data is in local CSVs (no API needed)  2. must NOT search for Kingdee/JinDie API  3. must match records across two sources with fuzzy matching  4. must report mismatches clearly (missing in ERP, missing in POS, amount diff) |
| 禁止模式 | 1. searches for '金蝶 API' or 'Kingdee API'  2. generates api-guide.md  3. only does exact match (fails on date/time format differences) |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

## Case B4 — 促销ROI分析

| 项目 | 内容 |
|---|---|
| case_id | `b4` |
| 测试维度 | Phase 2 analysis design precision for domain-specific math |
| 输入类型 | mixed |
| 生成 prompt | `每次做完大促，老板都要看三个数：促销投入多少钱、带来多少增量销售、有没有吃掉正常销售。但我们现在是手工算的，经常算错` |
| 上传文件 | `data/b4_promo_roi/promo_events.csv` |
| 期望 skill 名 | `promo-roi-analyzer-skill` |
| 期望架构 | simple |
| 关键检查项 | 1. must compute baseline sales (pre-promo average) correctly  2. must compute lift = (promo_sales - baseline) / baseline  3. must estimate cannibalization from post-promo dip  4. must compute ROI = (incremental_profit - marketing_cost) / marketing_cost  5. eval golden cases must include: zero lift, negative ROI, missing baseline period |
| 禁止模式 | 1. simplifies ROI to (promo_sales / marketing_cost) without baseline subtraction  2. ignores post-promo cannibalization effect  3. no baseline logic (just compares two raw numbers)  4. eval cases only test happy path |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

## Case B5 — 商品汰换决策

| 项目 | 内容 |
|---|---|
| case_id | `b5` |
| 测试维度 | Phase 2 handling of mixed quantitative/qualitative analysis |
| 输入类型 | mixed |
| 生成 prompt | `每个季度要决定哪些商品下架、哪些补货，现在凭感觉做，想做数据化一点` |
| 上传文件 | `data/b5_assortment/product_performance.csv` |
| 期望 skill 名 | `assortment-optimizer-skill` |
| 期望架构 | simple |
| 关键检查项 | 1. must produce a four-quadrant classification (high margin × high turnover etc.)  2. must NOT just output a sorted CSV — must include decision recommendations  3. must account for seasonality flag  4. must flag products with high returns rate for review |
| 禁止模式 | 1. sorts by sales volume and calls it 'optimization'  2. ignores margin/turnover trade-off  3. no actionable recommendations (just data dump)  4. treats seasonal products the same as non-seasonal |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

## Case B6 — 会员RFM分层

| 项目 | 内容 |
|---|---|
| case_id | `b6` |
| 测试维度 | Phase 2 correct parameterization of standard methods |
| 输入类型 | mixed |
| 生成 prompt | `我想把会员分成几类，比如高价值的、快流失的、沉睡的，然后针对每类做不同的营销` |
| 上传文件 | `data/b6_rfm/transactions.csv` |
| 期望 skill 名 | `member-rfm-segmenter-skill` |
| 期望架构 | simple |
| 关键检查项 | 1. must compute Recency (days since last purchase), Frequency, Monetary correctly  2. must provide configurable scoring method (quantile vs fixed thresholds)  3. must produce segment profiles with actionable marketing recommendations  4. must handle members with zero/few transactions gracefully |
| 禁止模式 | 1. hardcodes bin thresholds (should be configurable or auto-computed)  2. uses arbitrary percentile cutoffs without explanation  3. no segment-specific recommendations  4. crashes on members with single transaction |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

## Case C7 — 月度经营分析（多维度suite）

| 项目 | 内容 |
|---|---|
| case_id | `c7` |
| 测试维度 | Phase 3 correct classification as complex suite vs single skill |
| 输入类型 | mixed |
| 生成 prompt | `每个月要给区域经理做一套分析：销售达标率、库存健康度、人员效率、费用控制，四个维度，每个维度下面又有好几个子项` |
| 上传文件 | `data/c7_monthly/sales_target.csv` `data/c7_monthly/inventory_health.csv` `data/c7_monthly/staff_efficiency.csv` `data/c7_monthly/cost_control.csv` |
| 期望 skill 名 | `monthly-ops-analysis-suite` |
| 期望架构 | complex_suite |
| 关键检查项 | 1. must be structured as a SUITE with 4+ component skills, not one giant SKILL.md  2. each component must have its own SKILL.md under suite root  3. must include a master orchestrator that runs all 4 and produces combined report  4. each sub-analysis must be independently usable |
| 禁止模式 | 1. crams all 4 dimensions into single SKILL.md > 500 lines  2. sub-analyses are not independently invocable  3. no combined executive summary across all dimensions |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

## Case C8 — 单店排班优化

| 项目 | 内容 |
|---|---|
| case_id | `c8` |
| 测试维度 | Phase 3 correctly keeping simple task as simple skill |
| 输入类型 | mixed |
| 生成 prompt | `我家店长每周要排班，根据客流高峰低谷来安排人，帮我把这个做成一个工具` |
| 上传文件 | `data/c8_scheduling/foot_traffic.csv` |
| 期望 skill 名 | `shift-scheduler-skill` |
| 期望架构 | simple |
| 关键检查项 | 1. must stay as simple skill (not suite) — it's one pipeline  2. must generate weekly shift table from traffic data  3. must respect peak/off-peak staffing ratios  4. output must be a readable schedule table |
| 禁止模式 | 1. over-engineers into suite with separate traffic-analyzer, shift-generator, validator skills  2. SKILL.md exceeds 500 lines for a ~300 line problem  3. generates complex optimization algorithms when simple rule-based suffices |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

## Case D9 — 动销率分析（中文行业术语）

| 项目 | 内容 |
|---|---|
| case_id | `d9` |
| 测试维度 | Phase 4 keyword/description accuracy for Chinese domain terms |
| 输入类型 | mixed |
| 生成 prompt | `给我做一个动销率分析的工具` |
| 上传文件 | `data/d9_sell_through/sku_sales.csv` |
| 期望 skill 名 | `sell-through-analyzer-skill` |
| 期望架构 | simple |
| 关键检查项 | 1. description must include Chinese retail terms: 动销率, 滞销, SKU  2. keywords must cover both Chinese and English variants  3. must correctly compute sell-through = sold / (begin + end) / 2  4. must flag slow/dead SKUs with actionable thresholds |
| 禁止模式 | 1. description uses only English terms (misses 动销率 entirely)  2. computes sell-through incorrectly as sold/beginning  3. hardcodes English-only trigger keywords |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

## Case D10 — 退换货（极简输入）

| 项目 | 内容 |
|---|---|
| case_id | `d10` |
| 测试维度 | Phase 0 harvest→filter→shape for single-word input |
| 输入类型 | text_only_minimal |
| 生成 prompt | `退换货` |
| 上传文件 | 无 |
| 期望 skill 名 | `returns-analyzer-skill` |
| 期望架构 | simple |
| 关键检查项 | 1. must activate Phase 0 spec ideation (single word is too vague for Phase 1)  2. must present hypothesis: 'You need returns rate analysis, reason classification, refund tracking, and product quality alerts. Right?'  3. must NOT guess one narrow direction and build immediately |
| 禁止模式 | 1. jumps directly to Phase 1 without confirming interpretation  2. builds a skill for only one aspect (e.g., only refund tracking)  3. doesn't present hypothesis for user confirmation |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

## Case E11 — 薪资核算（安全敏感）

| 项目 | 内容 |
|---|---|
| case_id | `e11` |
| 测试维度 | Phase 5 security scan + complex business rules + edge cases |
| 输入类型 | mixed |
| 生成 prompt | `我们门店员工的工资是按基本工资+提成+全勤+加班算的，提成规则每个品类不一样。帮我做一个核算工具` |
| 上传文件 | `data/e11_payroll/employees.csv` `data/e11_payroll/commission_rules.md` |
| 期望 skill 名 | `payroll-calculator-skill` |
| 期望架构 | simple |
| 关键检查项 | 1. security_scan must pass with zero high-severity findings  2. output files must NOT contain plaintext salary data without permission warnings  3. must parse commission_rules.md and implement tiered rules correctly  4. must handle: overtime across midnight, partial attendance, holiday pay multipliers  5. must compute social insurance deductions correctly |
| 禁止模式 | 1. hardcodes commission rules instead of reading from rules file  2. outputs .xlsx with salaries without any data protection note  3. logs salary values to stdout  4. eval cases don't cover boundary: zero sales, negative returns, max overtime |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

## Case E12 — 多格式门店周报

| 项目 | 内容 |
|---|---|
| case_id | `e12` |
| 测试维度 | Phase 5 output quality: human-readable summary vs raw data dump |
| 输入类型 | mixed |
| 生成 prompt | `每周要生成一份门店周报，给店长发PDF、给区域经理发表格、给总部发一页摘要。数据来自三个不同的导出文件` |
| 上传文件 | `data/e12_multi_format/store_sales.csv` `data/e12_multi_format/customer_feedback.csv` `data/e12_multi_format/inventory_snapshot.csv` |
| 期望 skill 名 | `weekly-store-report-skill` |
| 期望架构 | simple |
| 关键检查项 | 1. report.md MUST start with executive summary (本周结论), not a data table  2. must produce 3 differentiated outputs for 3 audiences (店长/区域经理/总部)  3. must merge data from 3 CSV sources correctly  4. summary text must be rule-generated (not LLM-dependent) for reproducibility  5. stdout after --report must print human-readable summary, not JSON dump |
| 禁止模式 | 1. report starts with KPI data table (CRM issue #2 pattern)  2. all three audience outputs are the same content with different file extension  3. summary requires LLM call (not reproducible)  4. pipeline stdout prints raw JSON |
| 生成日期 | |
| 评分 | |
| 缺陷记录 | |

---

## 汇总模板

全部 12 个 case 跑完后填写。

| case | grade | validate | security | files | arch | output | anti-pat | 关键发现 |
|---|---|---|---|---|---|---|---|---|
| A1 | | | | | | | | |
| A2 | | | | | | | | |
| A3 | | | | | | | | |
| B4 | | | | | | | | |
| B5 | | | | | | | | |
| B6 | | | | | | | | |
| C7 | | | | | | | | |
| C8 | | | | | | | | |
| D9 | | | | | | | | |
| D10 | | | | | | | | |
| E11 | | | | | | | | |
| E12 | | | | | | | | |

### 按 creator pipeline 阶段归因

| 阶段 | 涉及 case | 通过率 | 典型缺陷 | 优化建议 |
|---|---|---|---|---|
| Phase 0 | D10 | | | |
| Phase 1 | A1, A2, A3 | | | |
| Phase 2 | B4, B5, B6 | | | |
| Phase 3 | C7, C8 | | | |
| Phase 4 | D9 | | | |
| Phase 5 | E11, E12 | | | |

### creator 优化清单

1. [ ] 
2. [ ] 
3. [ ] 
4. [ ] 
5. [ ] 
6. [ ] 
7. [ ] 
8. [ ] 

### 全局统计

- 总 case 数：12
- A 级：___  B 级：___  C 级：___  D-F 级：___
- 综合通过率：___%
- 平均每 skill 缺陷数：___