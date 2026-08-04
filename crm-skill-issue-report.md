# CRM Skill 问题报告

**日期**：2026-07-31
**对象**：`sqlite-crm-weekly-report-skill`（首次生成产物）
**背景**：针对生成的 CRM skill 做一次复盘，核对 creator（agent-skill-creator）在 VERSION.md 中新增的规则是否真正落到产物，并整理三个主要问题。
**状态**：草稿，待确认

---

## v2 — 2026-07-31 — creator 提示体系 token 效率审计

### 发现

生成 CRM skill 时，creator 自身的提示文件被实际读取的体量约为 5000+ 行，
其中约一半属于三类浪费：文件间大面积重复、生命周期后半段内容被全量加载、
代码模板在文档与脚本之间各自维护。

### 证据

**（1）SKILL.md 与 pipeline-phases.md 两套 Phase 描述**

两个文件各自独立描述了 5 个 Phase 的完整流程，且各自带 checklist 和代码示例。
pipeline-phases.md 中对生成有实际增量信息的（eval 阈值模板、文件创建顺序表、
harness patterns）不到 20%，其余是对 SKILL.md 的逐段展开重述。
pipeline-phases.md 内的「Discovery Examples」是三个固定域的长示例（农业 / 股票 /
气候），与当前 CRM 任务完全无关，属于沉没 token。

**（2）quality-standards.md 三层 checklist**

Phase 5 checklist 同时存在于 SKILL.md、pipeline-phases.md、quality-standards.md
三处，内容高度一致，后者还重复了 `pipeline_template.py` 的代码规范模板。

**（3）architecture-guide.md / cross-platform / universal 被大面积无关读取**

architecture-guide.md 的后半段（sizing 模式、性能策略、拆分重构、版本管理、
suite 编排）对单个简单 skill 的生成没有贡献，但在 SKILL.md 的引用指引下被全量加载。
cross-platform-guide.md 与 universal-standard.md 在未使用 `--universal` 的情况下
也被部分读取。

### 根因模式

1. **「按需读取」承诺未兑现**：SKILL.md 底部 Reference Files 表与正文散落的
   "See references/x.md" 让 agent 无法按需跳过——checklist 分散在三处，不读全
   就无法合规。
2. **用示例替代规则**：Phase 1 决策流程被写成了三个域的长示例，而不是一张
   generic 决策表；读示例花的 token 基本全浪费。
3. **文件角色未收敛**："SKILL.md 是入口、pipeline-phases.md 是详细参考" 在
   执行时等价于"两个都读"。真正只需保留 pipeline-phases.md 中唯一不重复的
   eval 边界模板 + 文件顺序表 + harness contract（约 300 行）。
4. **按需求态组织而非按使用态**：architecture-guide.md 覆盖了从创建到退役的
   全生命周期，但 80% 的生成只需要它的前 300 行。

### 建议

1. 删除 pipeline-phases.md 中与 SKILL.md 重叠的 Phase 1-5 流程描述和质量标准
   重述部分；只保留 checklist 表、eval 边界模板、文件顺序表、harness contract。
2. 删除 quality-standards.md 的 checklist（统一由 pipeline-phases.md 承载），
   代码规范模板直接指向 `pipeline_template.py`。
3. architecture-guide.md 后半段（sizing 以后）加显式条件：「仅用于复杂 skill
   或重构时读取」；SKILL.md 不再无条件引用其全文。
4. 增加 Phase 前置判断：读取 pipeline-phases.md 之前先检查这是否是
   `--universal` 模式，若不是则跳过 universal-standard.md 和
   cross-platform-guide.md。

---

## 结论摘要

生成的 skill 功能上可运行（pipeline、eval、security 均通过），但存在三个结构性问题：

1. 提示文件没有把“运行时契约”立起来，Agent 仍倾向通读 `scripts/` 源码来理解 skill（P1）。
2. 面向用户的输出是数据视角而不是阅读视角，`report.json / report.md / report.csv` 过于原始（P1）。
3. creator 新规则没有同步到生成模板，产物仍携带旧结构：8 个 markdown 文件、bash/ps1 wrapper、README 手动安装表、EVOLUTION.md 失败日志（P1）。

根因是 creator 内部文档自相矛盾（AGENTS.md 到底生成还是不生成）、VERSION.md 的新规没有回流到 Phase 5 模板与 validate.py，以及生成时把“机器可读”当成“用户可读”。

---

## 问题一：Agent 仍倾向通读 scripts，提示文件指引不足（P1）

### 现象

用户观察：Agent 了解 skill 时仍然选择全部阅读 `scripts/` 下的 Python 源码，而不是先信任 SKILL.md / AGENTS.md 给出的运行时入口。

### 证据

- 产物 `SKILL.md` 的 `## Workflow` 只写了 4 个步骤名，没有明确“`scripts/` 是实现细节、运行时不读”的阅读边界。
- `AGENTS.md` 写的是“Read SKILL.md and follow it”，但没有一行说明“不需要读 `scripts/*.py`”。
- `references/schema-guide.md` 等文档使用“loaded on demand”式描述，等于邀请 Agent 在不确定时自行翻文件。
- creator 侧 Phase 5 只强制“生成 `## How to run it`”，没有强制“How to run it 必须出现在 Workflow 之前”和“必须包含不读 scripts 的指令”，因此生成结果依赖模型自觉。
- 运行时的实际“契约”分散在 `pipeline.py`、`run_pipeline.py`、`contract.json`、README、SKILL.md 多处，Agent 只有通读才能确信。

### 影响

- 每次调用多消耗大量 token。
- Agent 可能按自己读到的源码“手动编排步骤”，绕过 `--report` 单入口。
- 文档与代码版本漂移时，Agent 更容易相信过时的源码注释。

### 建议

1. SKILL.md 增加 `## Runtime Contract` 或 `## Reading Rules` 段落，明确：
   - 正常使用只运行 `python3 scripts/pipeline.py --input <db> --output <out> --report`；
   - `scripts/*.py` 是实现细节，默认不读；
   - 仅在排障、改规则、扩展 schema 时才读 `references/` 和对应模块。
2. AGENTS.md 收敛为 25 行以内的 dispatch card（对齐 `references/universal-standard.md` §2），只保留一句话用途、运行命令、SKILL.md 链接。
3. creator Phase 5 模板与 checklist 强制顺序：`## Quick Profile` → `## How to run it` → `## Runtime Contract` → 其余正文，并让 validate.py 检查 `Runtime Contract` 存在（可作为 warning）。
4. pipeline 的 stdout 直接输出人读摘要和产物路径，让 Agent 不需要读源码就知道结果。

---

## 问题二：面向用户的输出过于原始（P1）

### 现象

当前产物把机器数据结构直接当作用户输出：`report.json` 是完整字段树，`report.md` 从 KPI 表格开始，`report.csv` 是行式数据；stdout 打印的是 JSON `status/kpis`，不是人读结论。

### 证据

- `report.md` 的结构是 `KPI Summary → Cleaning Summary → Pipeline by Stage → Region → Owner → Activities → Trend`，通篇表格，没有“本周结论”、环比、异常提醒。
- `report.json` 没有 `summary` / `highlights` / `alerts` 这类面向阅读的字段。
- SKILL.md 的 `## Output Example` 展示的也是原始 JSON。
- pipeline 结束后 stdout 输出完整 `kpis` 对象，而不是 5-8 行摘要。

### 影响

- 用户（或上层 Agent）需要二次加工才能回答“这周怎么样、哪里有问题”。
- 表格越多越容易漏掉关键信号（成交下滑、重复率上升、孤儿数据变多）。

### 建议

1. `report.md` 顶部新增 `## 本周结论`（executive summary）：
   - 3-5 句规则生成的模板文本，例如“本周新增 12 位联系人，成交 3 单共 $45,600；开放管道 $184,500，较上周 -8%；数据质量 96.4，仍有 2 个无效邮箱待处理。”
   - 不依赖 LLM，由 pipeline 按 KPI 与告警规则生成，保证可复现。
2. `report.json` 新增 `summary` 字段：`summary_text`、`highlights[]`、`alerts[]`，机器字段保持不变。
3. pipeline stdout 在 `--report` 后打印人读摘要 + 输出文件路径，JSON 状态改为 `--json` 可选。
4. 可加 `--brief` 只输出摘要；`report.csv` 与 `report.json` 继续作为原始数据层，文档标注“raw data”。
5. SKILL.md 的 Output Example 改为先展示摘要，再给 JSON 结构。

---

## 问题三：creator 新规则未落实，产物仍是旧结构（P1）

### 现象

VERSION.md 明确“统一 skillctl 安装、删除本地安装器、skill = 能力包”，但生成产物仍然带有旧结构。

### 证据

产物 markdown 文件共 8 个：

```
SKILL.md
AGENTS.md
README.md
EVOLUTION.md
evals/sqlite-crm-weekly-report-skill.eval.md
references/schema-guide.md
references/analysis-methods.md
references/troubleshooting.md
```

其他旧结构残留：

- `sqlite-crm-weekly-report-skill`（bash wrapper）与 `sqlite-crm-weekly-report-skill.ps1` 仍在根目录；VERSION.md v0.4.0 已删除本地安装器并把 lifecycle 归给 skillctl。
- `README.md` 仍保留“Manual installation”逐平台复制路径；VERSION.md v0.4.0 要求统一 `skillctl install <name>`。
- `EVOLUTION.md` 被打包进交付物，里面是开发期三次失败 rollout 的证据；该文件应只在交付后失败时按需生成。
- creator 自己的规范互相矛盾：
  - factory `SKILL.md` Phase 5 第 3 步要求生成 AGENTS.md，第 8 步又说 skill repo “carries only SKILL.md, AGENTS.md, scripts/, evals/, contract.json”；
  - `references/pipeline-phases.md` Step 2.5 与 checklist 明确“No per-skill AGENTS.md generated”，validate.py 却又对存在 AGENTS.md 发 warning；
  - v0.3.0 要求 AGENTS.md 的 `## Agent Constraints` 做阻断检查，而新 pipeline-phases 又把约束放进 SKILL.md 正文，双写导致漂移。

### 影响

- 每个新 skill 都会继续按旧模板产出多余文件，用户要手动清理。
- 多个 markdown 文件让 Agent 的阅读面更大，加剧问题一。
- 交付物携带开发期失败证据，污染用户侧排查。

### 建议

1. 以 VERSION.md 为源头收敛出一份**唯一权威文件清单**，默认模式与 universal 模式分别明确，并让 validate.py 按清单检查：
   - 建议默认：`SKILL.md`、`AGENTS.md`（25 行 dispatch card）、`README.md`、`scripts/`、`evals/`、`assets/`、`contract.json`；
   - `references/` 默认不生成；确实需要的细节合并进单一 `references/guide.md` 或移入 SKILL.md。
2. 生成模板删除 bash/ps1 wrapper；README 只写 `skillctl install <name>`。
3. 交付前清理 `EVOLUTION.md`；validate.py 增加“初始包不得携带 EVOLUTION.md”检查，只有 post-delivery 失败才生成。
4. 同步 factory `SKILL.md` 与 `pipeline-phases.md` 的 AGENTS.md 结论（二选一：生成 25 行 dispatch card，或彻底移除）。
5. 重新生成 CRM skill 验证收敛后的文件清单。

---

## 附加发现（P2）

- `scripts/validate.py` 的 description 正则存在 `\\s` 双反斜杠 bug（当前工作区未提交改动），导致合法描述“A cleaning pipeline ...”被误判；建议改为 `\s` 并补一条单测。
- `validate.py --check-contract` 对 `<output>` 模板路径固定报“file does not exist”warning；建议 contract schema 支持变量路径，或检查时跳过占位符。
- `contract.json` 的 DAG 检查把 `pipeline.py` 的 STEPS 解析成“0 个 pipeline function”，与模板的 `STEPS` dict 写法不匹配，建议放宽或改读 `contract.json.dag`。
- AGENTS.md 与 SKILL.md 双写 Agent Constraints，长期会漂移；收敛后只保留一份。

---

## 建议行动清单

1. 文档层：VERSION.md 牵头，统一文件清单与 AGENTS.md 政策，消除 factory SKILL.md 与 pipeline-phases.md 的矛盾。
2. 模板层：SKILL.md 强制 `Runtime Contract` + 不读 scripts；AGENTS.md 改 25 行 dispatch card；删除 wrapper 与 README 手动安装表。
3. 输出层：report.md 增加“本周结论”，report.json 增加 `summary`，stdout 输出人读摘要。
4. 校验层：修复 validate.py 正则；增加 EVOLUTION.md 初始包检查、文件清单检查、Runtime Contract 检查。
5. 回归验证：重新生成 `sqlite-crm-weekly-report-skill`，跑 validate/security/check_pipeline/run_evals，确认 0 error 且文件清单收敛。

---

## 待确认问题

- `references/` 是否彻底删除，还是合并为单个 `references/guide.md`？
- AGENTS.md 最终政策是“25 行 dispatch card”还是“不再生成”？
- 摘要输出是否需要支持中文/英文模板，还是跟随报告语言配置？
