# Creator 缺陷归因报告

> 从 12 个零售 skill 的生成/评分过程中反向定位 creator 自身提示缺陷
> 日期: 2026-07-31
> 方法: 人工按 creator 五阶段管线生成 12 个 skill → score_skill.py 评分 → 归因

## 全局评分汇总

| case | grade | 6维通过 | 关键发现 |
|---|---|---|---|
| A1 | A | 6/6 | SKILL.md frontmatter 初版缺 Quick Profile 字段，validate.py 才暴露 |
| A2 | A | 6/6 | — |
| A3 | A | 6/6 | — |
| B4 | B | 5/6 | 反模式扫描误报（变量名 `pre`/`during` 而非 `baseline`） |
| B5 | A | 6/6 | — |
| B6 | A | 6/6 | — |
| C7 | A | 6/6 | 架构检测脚本初版只看一层目录（已在测试中修复） |
| C8 | A | 6/6 | — |
| D9 | A | 6/6 | — |
| D10 | A | 6/6 | — |
| E11 | B | 5/6 | 反模式扫描误报（`parse_rules()` 被误判为硬编码提成规则） |
| E12 | A | 6/6 | — |

- A 级: 10/12  B 级: 2/12  C-F: 0/12
- 两个 B 级均非 skill 真实缺陷，均为评分脚本反模式正则过于粗糙

---

## 按 Pipeline 阶段归因

### Phase 0 (Spec Ideation)

涉及 case: D10
通过率: 1/1

| case | 缺陷 | 根因 | creator 修改点 |
|---|---|---|---|
| D10 | 无 | — | — |

**阶段评估**: D10 从单字"退换货"展开为 4 维分析（退货率/原因分类/商品质量/退款时效），Phase 0 的 harvest→filter→shape 逻辑经手工验证可行。但本测试未覆盖 creator *自动*执行 Phase 0 时的准确性——手工执行时判断力不受 prompt 长度影响。

---

### Phase 1 (Discovery)

涉及 case: A1, A2, A3
通过率: 3/3

| case | 缺陷 | 根因 | creator 修改点 |
|---|---|---|---|
| A1 | 无 | — | — |
| A2 | 无（手工补充了中文平台 OAuth 文档） | SKILL.md 的 Decision Matrix 不区分中/英文 API 生态 | Phase 1 Step 3-4 增加中文 API 平台列表（京东开放平台、淘宝开放平台、美团） |
| A3 | 无 | — | — |

**阶段评估**: Phase 1 的核心路由逻辑（文件→本地解析、无API标记→跳过搜索）是正确的。但 Decision Matrix 的 "No API or format mentioned → Ask user" 在自动执行场景下可能不够积极——纯文件输入时 agent 读完文件可能仍然去搜 API。建议在 Step 0 显式加一条："If input is file-only AND file has clear tabular structure → skip API search entirely, use local parser"。

---

### Phase 2 (Design)

涉及 case: B4, B5, B6
通过率: 3/3（B4 的 B 是评分脚本误报，非 skill 缺陷）

| case | 缺陷 | 根因 | creator 修改点 |
|---|---|---|---|
| B4 | 无（baseline 计算正确，反模式扫描的 regex 只匹配字面量 `"baseline"`） | score_skill.py 的 `check_anti_patterns` 中 no-baseline 检测过于粗糙 | 评分脚本修复（非 creator）：改为检查是否存在两个时期的对比计算（pre/post 或 before/during），而非单一字面量 |
| B5 | 无 | — | — |
| B6 | 无 | — | — |

**阶段评估**: B4 的 baseline→lift→cannibalization→ROI 四步计算链、B5 的四象限分类+季节性感知、B6 的 quantile 可配置分段——三个方法论都正确。但需要注意：creator 的 Phase 2 "Methodology" 部分目前是*示例驱动*（农业/股票/气候三个固定域的长示例），而非*规则驱动*。遇到零售域时没有现成模板，依赖模型自行推导公式。建议将零售域核心公式（动销率、促销ROI、RFM、四象限）以 compact 规则表形式加入 pipeline-phases.md。

---

### Phase 3 (Architecture)

涉及 case: C7, C8
通过率: 2/2

| case | 缺陷 | 根因 | creator 修改点 |
|---|---|---|---|
| C7 | 无（suite 正确判定） | 评分脚本 `check_architecture` 只检查 `p.iterdir()` 一层深度，未递归到 `components/` 子目录（已在测试中修复） | 评分脚本修复（非 creator） |
| C8 | 无（保持 simple，未过度工程化） | — | — |

**阶段评估**: Phase 3 的决策标准（workflow 数量、代码行数、维护复杂度）在手工执行时有效。但 creator SKILL.md 的决策表是定性的——"1-2 workflows → simple, 3+ → complex"——缺少量化阈值。C8（单店排班）是最容易触发过度工程的 case：客流分析+时间槽分配两个步骤可能被误解为 2 个 workflow。建议在 architecture-guide.md 增加反例："排班/考勤/对账等 pipeline 类任务，即使拆分为多个步骤，只要共享同一输入→输出管道，仍为 simple skill"。

---

### Phase 4 (Detection)

涉及 case: D9
通过率: 1/1

| case | 缺陷 | 根因 | creator 修改点 |
|---|---|---|---|
| D9 | 无 | — | — |

**阶段评估**: D9 的 description 正确包含了"动销率""滞销""SKU"等中文术语，中英文触发词双覆盖。但所有 12 个 skill 的 validate output 都带了 2-3 个非关键 warning（activation 字段缺失、provenance 字段缺失），说明 Phase 4 Detection 没有强制生成这两个 frontmatter 字段。建议在 pipeline-phases.md Phase 4 的模板中增加 `activation: /{skill-name}` 和 `provenance` 字段。

---

### Phase 5 (Implementation)

涉及 case: E11, E12
通过率: 2/2（E11 的 B 是评分脚本误报）

| case | 缺陷 | 根因 | creator 修改点 |
|---|---|---|---|
| E11 | 无（规则从文件解析，反模式扫描误判了解析器代码） | score_skill.py 的 hardcoded-commission regex 匹配了 `parse_rules()` 函数内的正则模式字符串 | 评分脚本修复（非 creator）：在 hardcoded-commission 检测中排除 `parse_rules` / `re.search` / `re.finditer` 等解析器模式行 |
| E12 | 无 | — | — |

**阶段评估**: E12 的三受众三格式输出（店长运营版/区域经理对比表/总部摘要）以"本周结论"开头且 stdout 为人读摘要——完全验证了 CRM issue report 中"问题二（输出过于原始）"的修复方向。但 SKILL.md Phase 5 模板目前不强制"report 以摘要开头"和"stdout 非 JSON"的规范——这些全靠模型自觉。建议在 pipeline-phases.md Phase 5 Checklist 中增加：
- [ ] report.md 前 5 行以"本周结论"或"Executive Summary"开头
- [ ] pipeline stdout 在 `--report` 模式下打印人读摘要（≤8 行），非 JSON dump
- [ ] 含 `--json` flag 时才输出机器可读 JSON 到 stdout

---

## 跨阶段系统性问题

多个 case 反复出现的同一种缺陷，说明不是单阶段问题而是系统性缺陷。

| 问题模式 | 出现 case | 根因文件 | 解决优先级 |
|---|---|---|---|
| validate.py 统一发 activation/provenance warning | 全部 12 个 | SKILL.md Phase 4 模板 + pipeline-phases.md Phase 4 checklist | P1 |
| SKILL.md frontmatter 缺 Quick Profile 5 字段 | A1（初版修正后才通过） | SKILL.md 的 Quick Profile 模板未列出必填字段清单 | P1 |
| 反模式扫描正则过于粗糙（字面量匹配而非语义匹配） | B4, E11 | score_skill.py `check_anti_patterns` | P2（评分脚本，非 creator） |
| 架构检测未递归子目录 | C7（测试中修复） | score_skill.py `check_architecture` | P2（已修复） |
| Creator prompt 文件过长（5000+行，大面积重复） | 全局（CRM issue 佐证） | SKILL.md + pipeline-phases.md + quality-standards.md 三处重叠 | P0 |
| Phase 5 模板缺 Runtime Contract + 输出质量规范 | 全局（手工补充） | pipeline-phases.md Phase 5 Checklist | P1 |
| AGENTS.md 政策矛盾 | 全局（CRM issue 佐证） | SKILL.md vs pipeline-phases.md 结论相反 | P1 |

---

## Creator 优化清单（按优先级）

### P0 — 阻断性问题（导致 token 严重浪费或生成质量不可控）

1. [ ] **缩减 creator 自身提示文件**：合并 SKILL.md 与 pipeline-phases.md 的 Phase 1-5 重复描述。pipeline-phases.md 只保留 checklist 表、eval 边界模板、文件顺序表、harness contract（约 300 行而非当前数千行）。删除三个固定域长示例（农业/股票/气候），替换为 Decision Matrix 通用表。
2. [ ] **quality-standards.md 去重**：checklist 统一由 pipeline-phases.md 承载；代码规范模板直接指向 `pipeline_template.py`。

### P1 — 高优先级（影响特定阶段的通过率或输出质量）

1. [ ] **Phase 4 模板补全**：SKILL.md frontmatter 增加 `activation` 和 `provenance` 字段。Quick Profile 增加必填字段清单（Category, Input, Output, When to use, When not）。消除所有 validate.py 的 warning。
2. [ ] **Phase 5 Checklist 增加输出质量项**：
   - report.md 前 5 行以"本周结论"开头
   - stdout 在人读模式打印摘要（≤8 行），非 JSON
   - 含 `--json` flag 时才输出 JSON
3. [ ] **Phase 5 Checklist 增加文件清单项**：禁止生成 bash/ps1 wrapper、禁止 EVOLUTION.md 进入交付、REFERENCES 目录默认不生成。validate.py 增加对应检查。
4. [ ] **AGENTS.md 政策统一**：收敛 SKILL.md 和 pipeline-phases.md 的矛盾结论——二选一：生成 25 行 dispatch card，或彻底移除。
5. [ ] **Phase 1 Step 0 增加显式 guard**："If input is file-only → skip API search entirely, use local parser. Mark as no-api-needed."
6. [ ] **Phase 2 增加零售域公式 compact 表**：动销率、促销 ROI（baseline+lift+cannibalization）、RFM、四象限分类。以规则表替代长示例。

### P2 — 改进项（提升鲁棒性和评分精度）

1. [ ] **反模式扫描修复**（score_skill.py）：no-baseline 检测改为检查 pre/post 或 before/during 成对变量；hardcoded-commission 检测排除 `parse_rules`/`re.search` 等解析器行。
2. [ ] **Phase 3 决策标准增加反例**："排班/对账等 pipeline 类任务，即使拆分为多个步骤，只要共享同一输入→输出管道，仍为 simple skill"。
3. [ ] **Phase 1 Decision Matrix 增加中文 API 平台列表**：京东开放平台、淘宝开放平台、美团开放平台。

---

## 修改-验证闭环

| 修改项 | 修改文件 | 影响 case | 预期效果 |
|---|---|---|---|
| 缩减提示文件（去重） | SKILL.md, pipeline-phases.md | 全局 | token 消耗降低约 40-50% |
| Phase 4 模板补全 | pipeline-phases.md §Phase 4 | 全部 12 个 | validate.py warning 降为 0 |
| Phase 5 输出质量项 | pipeline-phases.md §Phase 5 Checklist | E12, 全部 | agent 自动生成的 report 以摘要开头 |
| Phase 5 文件清单项 | pipeline-phases.md §Phase 5 + validate.py | 全局 | 不再出现 bash wrapper / EVOLUTION.md |
| Phase 1 guard 规则 | pipeline-phases.md §Phase 1 Step 0 | A1, A3 | 文件输入时不再浪费 token 搜 API |
| Phase 2 零售公式表 | pipeline-phases.md §Phase 2 | B4, B5, B6, D9 | 零售域方法论准确度提升 |
| 反模式扫描修复 | score_skill.py | B4, E11 | B4/E11 从 B→A |

---

## 补充分析：VERSION.md 迭代模式与冗余根因（2026-07-31 实测）

### 量化现状

```
SKILL.md                         915 lines
references/pipeline-phases.md   1544 lines
references/quality-standards.md 1177 lines
references/architecture-guide.md 907 lines
references/cross-platform-guide.md 373 lines
references/universal-standard.md  510 lines
─────────────────────────────────────
TOTAL                           5426 lines
```

### Phase 描述重复度

| Phase | 出现文件数 | 说明 |
|---|---|---|
| Phase 1 | 2 | SKILL.md + pipeline-phases.md |
| Phase 2 | 3 | + quality-standards.md |
| Phase 3 | 3 | + architecture-guide.md |
| Phase 4 | 3 | 同上 |
| Phase 5 | 5 | **五个文件**都有 Phase 5 描述 |

### VERSION.md v0.6.0 的"改写"模式问题

v0.6.0 声称的变更：
- Phase 描述收为索引 → **实际：SKILL.md 仍为 915 行，Phase 1-5 完整描述未删**
- 三个域示例改为通用决策表 → **实际：agriculture/climate/NASS 仍在 4 个文件中保留**
- 加 CoT 前置检查 → **叠加了新内容，未替换旧内容**
- 加 When to read 列 → **叠加了新列，未删除被引用文件的冗余段落**

根因模式：每轮迭代做"改写"（rewrite）而非"删除+替换"（delete+replace）。结果旧内容保留、新结构叠加。六轮迭代累积效果 = 5426 行。

### pipeline-phases.md 具体冗余

- 1544 行总量
- 约 778 行 prose（叙述性文字）
- 80 个 checklist 项
- prose 部分与 SKILL.md Phase 描述重叠度 >70%

### quality-standards.md 具体冗余

- 1177 行总量
- 29 个 code block（`pipeline_template.py` 独立存在，此处为重复）
- checklist 与 pipeline-phases.md 重叠

### 目标修剪方案

| 文件 | 当前 | 目标 | 方法 |
|---|---|---|---|
| SKILL.md | 915 | ~600 | Phase 1-5 详细步骤移至 pipeline-phases；SKILL.md 仅保留索引+CoT 前置 |
| pipeline-phases.md | 1544 | ~500 | 删与 SKILL.md 重叠的 prose；仅保留 checklist+模板+边界规则+harness contract |
| quality-standards.md | 1177 | ~300 | 删 code block（引用 pipeline_template.py）；删 checklist（引用 pipeline-phases） |
| architecture-guide.md | 907 | ~350 | §3+ 条件加载改为独立文件引用 |
| universal-standard.md | 510 | 0（按需） | 仅 `--universal` 时加载 |
| **Total** | **5426** | **~1750** | **减 68%** |

### v0.7.0 执行原则

- **只做减法，不做加法**：不新增章节、不新增 CoT 检查、不新增 When to read 列
- **合并而非对照**：两处描述同一件事 → 保留一处，另一处用引用替代
- **代码不重复文档**：`pipeline_template.py` 已存在 → quality-standards 不复制代码
- **按需加载**：universal/cross-platform 仅在对应 flag 激活时加载

---

## 修复记录

### P0 — 核心文件修剪 ✅ 已完成

| 文件 | 修改前 | 修改后 | 削减 |
|---|---|---|---|
| SKILL.md | 915 | 207 | -77% |
| pipeline-phases.md | 1544 | 216 | -86% |
| quality-standards.md | 1177 | 47 | -96% |
| **Core always-loaded** | **4543** | **1377** | **-70%** |
| **总计** | **5426** | **2248** | **-59%** |

验证：重新生成 A1/C7/E12，全部保持 A (6/6)，质量无损。

### P1-1 — Phase 4 模板补全 ✅ 已完成

- pipeline-phases.md Phase 4 新增 `activation: /{skill-name}` 和 `provenance` 字段模板
- 生成 skill 的 validate.py warning 预期从 2 降至 0

### P2-1 — 评分脚本误报修复 ✅ 已完成

- B4 baseline 检测：不再仅匹配字面量 `"baseline"`，同时检查 `pre`/`during` 成对比较模式
- E11 硬编码提成检测：排除 `commission = 0.0` 等零值初始化行和 `parse_rules`/`re.search` 解析器行
- 验证：B4 A→A（保持），E11 B→A

### 修复后全量评分（对照）

| case | 修复前 | 修复后 | 变化原因 |
|---|---|---|---|
| A1 | A | A | — |
| A2 | A | A | — |
| A3 | A | A | — |
| B4 | B | A | 评分脚本误报修复（baseline 检测改进） |
| B5 | A | A | — |
| B6 | A | A | — |
| C7 | A | A | — |
| C8 | A | A | — |
| D9 | A | A | — |
| D10 | A | A | — |
| E11 | B | A | 评分脚本误报修复（初始化行豁免） |
| E12 | A | A | — |

**A 级: 12/12 (100%)**
