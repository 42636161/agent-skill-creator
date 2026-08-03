## v0.7.0 — 提示词去重与质量收敛（2026-08-03）

### 变更

- **P0 核心文件去重** — SKILL.md（915 → 207, -77%）、pipeline-phases.md（1544 → 216, -86%）、
  quality-standards.md（1177 → 47, -96%）。三文件总量从 4543 行降至 1377 行（-70%）。
  删除原则：Phase 1-5 详细 prose 收敛到 pipeline-phases.md、代码块引用 pipeline_template.py
  而非复制、17 平台兼容表保留在 cross-platform-guide.md 按需加载、Checklist 统一由
  pipeline-phases.md 承载。
- **SKILL.md 重构** — 保留原创内容（Clarity Principles、Input hierarchy、Hypothesis pattern、
  Progressive refinement、Fail forward），删除与 reference 文件重复的 Phase 详细描述、
  17 平台表、Export/Templates/Suites/Interactive 章节。新增 Pipeline 索引段 + CoT 前置检查 +
  Phase guard 规则。Reference Files 表改为条件加载（When to read → Load only when）。
- **pipeline-phases.md 重构** — 仅保留 Phase 1-5 的 checklist、决策表（Decision Matrix +
  API 路由）、模板（Analysis Spec、Directory Structure、File Creation Order）、
  harness contract。新增零售域公式 compact 表（动销率、促销 ROI、RFM、四象限）。
  新增 Phase 5 Output Quality Rules（report 以摘要开头、stdout 人读、Runtime Contract）。
  新增 Phase 5 File Hygiene Checklist（禁 bash wrapper、禁 EVOLUTION.md 交付）。
- **Phase 4 模板补全** — 强制生成 activation 和 provenance 字段，
  消除 validate.py 的 2 个 persistent warning。
- **Phase 1 guard** — Decision Matrix 增加文件输入显式规则："File-only input → skip API
  search, use local parser, mark as no-api-needed"。中文 API 平台列表（京东/淘宝开放平台）。
- **Phase 3 反例** — 排班/对账等单管道任务即使有多步骤也保持 simple，不拆 suite。
- **Phase 2 公式表** — 零售域分析公式以 compact 表替代长示例（动销率、lift/cannibalization/ROI、
  RFM quantile、四象限 median 阈值）。
- **AGENTS.md 政策统一** — pipeline-phases.md Phase 5 明确 AGENTS.md ≤25 行 dispatch card。

### 验证

- 零售 skill 测试套件 12 个 case 全量评分：修复前 10A/2B → 修复后 12A。
- P0 修剪后重生成 A1/C7/E12：全部保持 A（6/6），质量无损。
- P2 评分脚本误报修复：B4 baseline 检测改进（pre/during 成对模式）、
  E11 硬编码提成检测改进（零值初始化豁免）。

### 变动文件

```
SKILL.md                              — 改写：去重、索引、CoT 前置、Phase guard
references/pipeline-phases.md         — 改写：去重、零售公式表、输出质量规则、文件卫生
references/quality-standards.md       — 改写：去重、引用 pipeline_template.py
tests/retail_skills/score_skill.py    — 修改：反模式扫描 B4/E11 误报修复
tests/retail_skills/results/          — 新增：creator 缺陷归因报告、UX 评分表、12 skill 全量评分
VERSION.md                            — 新增：本次版本记录
```

---

## v0.6.0 — 提示词工程优化（2026-07-31）

### 变更

- **token 效率** — SKILL.md Phase 描述收为索引 + CoT 前置检查；Reference Files 表
  加第三列「When to read」和条件触发；pipeline-phases.md 三个长域示例改为通用决策表；
  quality-standards.md 加 pipeline-phases checklist 引用；architecture-guide.md
  §3+ 加条件分隔线和阅读引导。
- **命中率** — 每个 Phase 前加 CoT 前置检查（`Before Phase N: verify...`）；
  SKILL.md body 模板加「Do NOT」负例段；Phase 5 加 self-check 步骤。
- **失败处理** — Phase 5 加 fix-only 重试指令和 validate.py 结构化错误解读。
- **幻觉减少** — Output Example 强制从真实 pipeline 运行复制；Agent Constraints 模板
  加固定反编造条款（`Must NOT fabricate or guess data`）。

### 变动文件

```
SKILL.md                              — 改写：Phase 摘要 + CoT 前置 + fix-only 重试 + 条件引用表
references/pipeline-phases.md         — 改写：决策表 + 负例 + Output 来源 + 反编造条款
references/quality-standards.md       — 改写：pipeline-phases 引用提示
references/architecture-guide.md      — 改写：阅读引导 + 条件分隔线
VERSION.md                            — 新增：本次版本记录
```

---

## v0.5.0 — creator 规范收敛（2026-07-31）

### 变更

- **AGENTS.md 政策统一** — 保留生成，收敛为 ≤25 行 dispatch card；Agent Constraints
  只保留在 AGENTS.md，SKILL.md 不再双写；factory `SKILL.md`、`pipeline-phases.md`、
  `validate.py` 三方对齐，消除规则矛盾。
- **SKILL.md 新增 Runtime Contract** — Phase 5 模板强制 `## Runtime Contract`
  段，声明正常使用只运行单条命令、`scripts/` 默认不读。
- **删除自引导包装器** — Phase 5 不再生成 `./skill-name`（bash）和
  `.\skill-name.ps1` 根目录包装器。
- **validate.py 新增检查** — 初始包不得携带 EVOLUTION.md（error）；Runtime Contract
  存在（warning）；AGENTS.md 超过 25 行（warning）。
- **validate.py 修复** — contract 输出路径跳过 `<output>` 占位符，不再误报
  「file does not exist」；DAG 检测也读 `pipeline.py`（原来只读 `run_pipeline.py`）。

### 改动文件

```
references/pipeline-phases.md        — 修改：Step 2.5、模板、Step 7b 包装器移除、checklist
scripts/validate.py                  — 修改：AGENTS 行数/EVOLUTION/Runtime Contract 检查、contract 修复
scripts/tests/test_validate.py       — 修改：新增 DescriptionFormat 4 条测试（来自 v0.4.1 修复）
VERSION.md                           — 新增：本次版本记录
```

---

## v0.4.0 — 统一 skillctl 安装清理（2026-07-31）

### 变更

- **删除本地安装器** — `install.sh` / `install.ps1`、`scripts/bootstrap.sh/.ps1/.bat`、`scripts/install-skill.sh/.ps1`、`scripts/install-template.sh/.ps1` 及 `scripts/claude-plugin-template/` 全部移除。
- **删除插件清单入口** — `.claude-plugin/`、`.cursor-plugin/`、`.codex-plugin/`、`.agents/plugins/marketplace.json` 与示例技能附带清单移除，工具不再通过 plugin marketplace 安装本仓库。
- **统一安装方式** — 工厂与生成技能统一通过 `skillctl install <name>` 安装；`skillhub` 仓库的 `install.sh` / `install.ps1` 只负责安装 skillctl CLI。
- **文档与页面同步** — SKILL.md、README.md、docs/INSTALL.md（重写为 skillctl 统一安装文档）、CONTRIBUTING.md、references 全部清除 installer / plugin marketplace / npx 残余引用；docs/index.html 安装入口改为 skillctl；CI 删除 PowerShell 安装器解析 job；架构图标签改为 skillctl。
- **测试同步** — 删除随安装器失效的 `test_plugin_manifests.py`、`test_install_parity.py`；`test_platforms.py` 移除 install-template.sh 漂移检测。

### 验证

- 全局 grep `install.sh|bootstrap|claude-plugin|plugin marketplace|npx skills`：活跃文档仅剩 skillhub 统一引导器命令；其余命中为历史记录（CHANGELOG、docs/superpowers）与 `validate.py` 的 universal 布局 denylist。
- 清理相关脚本通过 `py_compile`；除工作区未提交的 validate.py 新校验导致的既有失败外，测试套件其余 266 项通过。

### 改动文件

```
install.sh / install.ps1                            — 删除：自安装器
scripts/bootstrap.sh / .ps1 / .bat                  — 删除：一键安装
scripts/install-skill.sh / .ps1                     — 删除：技能安装器
scripts/install-template.sh / .ps1                  — 删除：安装器模板
scripts/claude-plugin-template/                     — 删除：插件清单模板
.claude-plugin/ .cursor-plugin/ .codex-plugin/      — 删除：各工具插件清单
.agents/plugins/marketplace.json                    — 删除：Codex 插件商店清单
scripts/tests/test_plugin_manifests.py              — 删除：失效测试
scripts/tests/test_install_parity.py                — 删除：失效测试
SKILL.md README.md CONTRIBUTING.md                  — 修改：统一 skillctl 安装说明
docs/INSTALL.md                                     — 重写：skillctl 统一安装文档
docs/index.html                                     — 修改：安装入口改为 skillctl
references/*                                        — 修改：清除 installer/plugin 残余引用
scripts/export_utils.py                             — 修改：移除 .claude-plugin 排除与 npx 说明
scripts/platforms.py scripts/tests/test_platforms.py — 修改：移除 shell 安装器漂移逻辑
.github/workflows/ci.yml                            — 修改：删除 PowerShell 解析 job
assets/architecture.excalidraw                      — 修改：install.sh 标签改为 skillctl
```

---

## v0.3.0 — 质量框架实现（2026-07-30）

### 新增

- **contract.json** — 生成技能自描述契约，含输入假设、输出字段、步骤 DAG、字段语义。validate.py 新增 `--check-contract` 验证代码与契约一致性。各字段按类型生成边界测试用例。
- **DAG 依赖自动解析** — pipeline_template.py 新增 `STEPS` 依赖图 + `resolve_steps()` 拓扑排序。入口接受最终目标（`--report`），engine 自动补全前置步骤，`--clean` 保持向后兼容。
- **Agent Constraints 检查** — AGENTS.md 新增 `## Agent Constraints` 节（至少 3 条可验证约束），validate.py 默认阻断式检查，`--skip-agent-constraints` 可跳过。
- **AST 级静态验证** — `validate.py --check-ast` 检测死函数、死变量、魔法数字。`--rollout` 模式下死函数升级为错误。仅使用 Python 标准库 ast 模块。
- **防御性 I/O 模板** — pipeline_template.py 新增四项实用函数：`_detect_encoding`（6 种编码自动探测）、`_match_columns`（列名模糊匹配）、`_ensure_dir`（目录自动创建）、`_safe`（NULL 安全处理）。SKILL.md 与 pipeline-phases.md 增加对应指导。
- **完整静态分析** — `validate.py --static-analysis`：导入链解析（局部/第三方/循环检测）、未定义引用检测、类型冲突检测。11 个测试覆盖全部路径。
- **Golden case 边界模板** — phase2-eval-assessment.md 定义按数据类型（string/integer/float/date/boolean）的 NULL/空/最大值/特殊字符边界模板，生成时标记为 holdout（`"split": "test"`）。

### 质量提升

| 维度 | 改进 | P0/P1/P2 |
|---|---|---|
| AI 可解读性 | contract.json + Agent Constraints | P0 |
| 执行可靠性 | DAG 自动解析 + 防御性 I/O | P0 |
| 验证完备性 | AST 验证 + 静态分析 + universal CI lint | P1 |
| 测试有效性 | 边界模板扩增 | P2 |

| 验证标志 | 功能 | 阻断级别 |
|---|---|---|
| `--check-contract` | 契约-代码一致性 | warning (default), error (universal) |
| `--check-ast` | 死代码/魔法数字 | warning, error (--rollout) |
| `--static-analysis` | 导入链/引用/类型 | error |
| Agent Constraints | AGENTS.md 约束存在性 | error (blocking) |
| `--check-universal` (CI) | universal 布局合规 | lint (continue-on-error) |

### 改动文件

```
references/contract-schema.json            — 新增：contract.json JSON Schema
scripts/pipeline_template.py               — 新增：DAG 解析 + 防御性 I/O 模板
scripts/tests/test_validate.py             — 新增：27 个测试（契约/AST/约束/静态分析）
EVALUATION.md                              — 重写：质量框架 v2.0
README.md                                  — 修改：--universal 入口提示
SKILL.md                                   — 修改：Phase 2/5 新增 contract/约束/防御/DAG/边界指令
references/pipeline-phases.md              — 修改：Phase 3/5 新增 DAG/contract/约束/防御/universal CI 条目
references/phase2-eval-assessment.md       — 修改：新增边界模板节
scripts/validate.py                        — 修改：新增 5 个验证模块（contract/AST/约束/静态分析）
.github/workflows/ci.yml                   — 修改：新增 universal 布局 lint 步骤
docs/superpowers/plans/2026-07-30-quality-framework-implementation.md    — 新增：质量框架执行计划
docs/superpowers/plans/2026-07-30-universal-skill-output-implementation.md — 新追踪：universal 模式执行计划
```

### 历史版本

- v0.1.0 存档在 `archive/v0.1-skill-distribution` 分支




---


## v0.2.0 — 平台中立技能输出模式（2026-07-30）

### 新增

- **``--universal`` 生成模式** — 生成纯能力包，不含平台适配器和生命周期工具
- **references/universal-standard.md** — universal 模式的唯一权威规范文件
- **scripts/run_evals_universal.py** — 精简 eval 引擎（569 行，移除了 llm-judge、模型比较、EVOLUTION.md）
- **scripts/validate.py --check-universal** — universal 布局合规性检查（禁止 platform-specific 文件）

### 设计决策

| 决策 | 结果 |
|---|---|
| skill 本体 vs 生命周期管理 | skill = 能力包；agent-skill-creator + skillctl = 生命周期管理器 |
| 工具 vs 技能分类 | Phase 2 新增二分类：工具（无领域判断）和技能（领域知识 + 对话模式） |
| SKILL.md 结构 | 工具 7 段、技能 12 段（含 Agent behavior、Diagnostics、Feature discovery） |
| 领域知识存儲 | 数据文件（assets/JSON），非 hardcode Python |
| 分发路径 | skillctl 外部分发，generated skill 不携带任何平台适配器 |

### 改动文件

```
references/universal-standard.md       — 新增：universal 输出规范（517 行）
scripts/run_evals_universal.py         — 新增：精简 eval 引擎（569 行）
SKILL.md                               — 修改：--universal 标志检测 + Trigger 示例
references/architecture-guide.md       — 修改：Section 2.2 universal 目录布局
references/pipeline-phases.md          — 修改：Phase 2/3/4/5 universal 分支条件
references/phase2-eval-assessment.md   — 修改：universal mode 子节
scripts/validate.py                    — 修改：--check-universal 验证标志
scripts/tests/test_skillctl_publish.py — 修改：universal skill 发布测试
```

### 历史版本

- v0.1.0 存档在 `archive/v0.1-skill-distribution` 分支

---

# 版本说明

## v0.1.0 — 技能分发架构（2026-07-29）

### 新增

- **skillctl CLI** — 技能发现、安装、发布、更新
- **集中索引仓库** — `42636161/skillhub`，registry.json + JSON Schema
- **语义匹配** — 自然语言意图匹配，中文/英文双语言支持
- **Agent 自动发现** — 索引仓库 AGENTS.md 驱动，置信度 >70% 自动安装
- **安全模型** — 来源信任、内容扫描、校验和验证三层
- **17 平台支持** — 同 agent-skill-creator 的跨平台安装矩阵

### 命令速查

```
skillctl search <关键词>        # 搜索技能
skillctl install <名称>         # 安装技能
skillctl info <名称>            # 查看详情
skillctl update <名称>          # 升级技能
skillctl publish <目录>         # 发布技能
skillctl list                   # 列出全部
skillctl categories             # 列出分类
skillctl doctor                 # 健康检查
```

### 文件清单

```
scripts/skillctl/     — CLI 包（models，config，index，search，install，publish，update）
scripts/tests/        — 16 个单元测试
skillctl              — Shell 包装器
```

### 索引仓库

| 文件 | 用途 |
|------|------|
| `registry.json` | 技能目录，按名索引 |
| `registry.schema.json` | JSON Schema |
| `AGENTS.md` | Agent 自动发现指令 |

### 协作

在 `registry.json` 提交 PR 注册新技能。第三方技能标记 `verified: false`。
