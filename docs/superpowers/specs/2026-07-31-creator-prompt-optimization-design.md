# Creator 提示文件 token 效率优化 — 设计文档

**日期**：2026-07-31
**来源**：crm-skill-issue-report.md v2 章节 + jgobuilds/ai-standards-public 模式参考
**状态**：设计阶段，待实施
**原则**：不改架构，不硬套外部基准；以「职责收敛 + 条件门控」消除五类浪费，保证生成质量不退化。

## 问题回顾（从 v2 审计）

| # | 浪费模式 | 涉及文件 | 根因 |
|---|---|---|---|
| 1 | SKILL.md 与 pipeline-phases.md 各自描述 5 个 Phase 完整流程 | SKILL.md、pipeline-phases.md | 两文件角色未分化 |
| 2 | Phase 5 checklist 同时出现在三处 | SKILL.md、pipeline-phases.md、quality-standards.md | checklist 没有单一归属 |
| 3 | architecture-guide 后半段被无条件全量读 | architecture-guide.md | 引用方式等于「必须全读」 |
| 4 | 三个长域示例替代通用规则 | pipeline-phases.md Phase 1 | 示例替代规则 |
| 5 | 按需读取承诺未兑现 | SKILL.md Reference Files 表 | 引用没有条件，agent 无法按需跳过 |

## 设计目标

1. SKILL.md 是 agent 读的第一个文件，应回答「要做什么、按什么顺序、读哪个 reference」三个问题，不负责展开「怎么做」的细节。
2. pipeline-phases.md 是「怎么做」的唯一权威，承载所有模板、阈值、checklist 和 harness 规范。
3. 其他 reference 文件各有明确触发条件；SKILL.md 的引用表用条件句式，agent 可以判断「这一轮不需要」就跳过。
4. 改完后生成一个 test skill 跑全链路校验，确保质量没有退化。

## 方案

### 一、SKILL.md：收成「索引 + 规则」

| 改什么 | 具体操作 |
|---|---|
| Phase 1-5 展开描述 | 删除 pipeline-phases 中已经有的详细步骤（约占 60 行）；保留每个 Phase 一句摘要 |
| Phase 5 checklist | 删除正文中 embedded 的 checklist 条目；改为一行「See pipeline-phases.md Phase 5 Checklist」 |
| Reference Files 表 | 每一条加触发条件；无条件必读的只保留 pipeline-phases.md、质量类文件 |

### 二、pipeline-phases.md：删重复、留唯一

| 改什么 | 具体操作 |
|---|---|
| 与 SKILL 重复的 Phase 1-5 概述段落 | 删除，用一行「See SKILL.md Phase X for overview; this section covers implementation」替代 |
| Phase 1 长示例 | 将农业/股票/气候三个域的长示例替换为一张「API selection decision matrix」——从 API 特征到分析排名的通用决策表 |
| Phase 5 body structure 模板 | 保留在 pipeline-phases（这是 implementation 细节，SKILL 只需引用它） |

### 三、quality-standards.md：去重

| 改什么 | 具体操作 |
|---|---|
| Phase 5 checklist 重复部分 | 删除，改为「The full Phase 5 checklist is in pipeline-phases.md」 |
| 代码规范模板 | 改为引用 `pipeline_template.py`，不在两个文件各维护一份 |

### 四、architecture-guide.md：加条件门

| 改什么 | 具体操作 |
|---|---|
| 文件顶部入口 | 加阅读指南：「Read §1-2 for every skill. Read §3+ only when the skill is complex or a refactoring.」 |
| Section 3 前 | 加显式分隔线：「── Everything below is on-demand ──」 |

### 五、其他 reference：引用门

在 SKILL.md 的 Reference Files 表，把当前无条件引用改为条件触发：

| 文件 | 当前 | 改后 |
|---|---|---|
| `cross-platform-guide.md` | 无条件 | Only read when skill targets Tier 2 or Tier 3 platforms |
| `universal-standard.md` | 无条件 | Only read when `--universal` is active |
| `export-guide.md` | 无条件 | Only read when exporting for Desktop/Web or API |
| `multi-agent-guide.md` | 无条件 | Only read when skill requires 3+ distinct components |
| `interactive-mode.md` | 无条件 | Only read when in interactive (wizard) mode |
| `templates-guide.md` | 无条件 | Only read when using template-based creation |

### 六、Reference Files 表收敛

| 始终读（每次生成） | 条件读（仅在特定场景） |
|---|---|
| `pipeline-phases.md` | `cross-platform-guide.md` |
| `quality-standards.md` | `universal-standard.md` |
| `architecture-guide.md` §1-2 only | `architecture-guide.md` §3+ |
| `description-guide.md` | `export-guide.md` |
| `phase4-detection.md` | `multi-agent-guide.md` |
| `phase2-eval-assessment.md` | `interactive-mode.md` |
| `contract-schema.json` | `templates-guide.md` |

## 实施检查清单

- [ ] SKILL.md：Phase 1-5 改为摘要 + 引用 pipeline-phases；Phase 5 checklist 改为一行引用；Reference Files 表加条件
- [ ] pipeline-phases.md：删除与 SKILL 重复的 Phase 概述；Phase 1 三个域示例改为通用决策表
- [ ] quality-standards.md：删除重复 checklist，保留代码质量模式 + 测试策略
- [ ] architecture-guide.md：顶部加阅读条件；Section 3 前加显式分隔
- [ ] 其他 reference：SKILL 引用表加条件触发
- [ ] 运行 `python3 scripts/validate.py <生成的 CRM skill>` 确认质量不退化
- [ ] 运行 `python3 -m unittest discover -s scripts/tests -p 'test_*.py'` 确认全量测试无新增失败
- [ ] 更新 VERSION.md

## 验收标准

- 生成一个 test skill，与优化前产物在 SKILL.md / AGENTS.md / README 文件结构和关键段落上没有退化。
- validate / security / check-pipeline 全通过。
- agent 不会因为少读了某个 reference 而遗漏必要指令（SKILL 里每条 reference 引用前都给出了触发条件，agent 按条件判断）。

## 两层 Agent 提示词区分

Creator 涉及两个 prompt 层级。两者都需要提示词工程，但需求不同：

| 层 | 角色 | 读者 | 文件 | 优化重点 |
|---|---|---|---|---|
| 层 1 — creator 提示 | 创造者 | 生成 skill 的 agent | `SKILL.md`、`pipeline-phases.md`、`references/*` | token 效率、命中率、失败回退 |
| 层 2 — 生成物提示 | 产品 | 使用 skill 的 agent | 产物 `SKILL.md`、`AGENTS.md`、`contract.json` | 幻觉减少、指令精确性、运行时行为约束 |

层 2 是最终交付物——它本身就是一个 prompt，被另一个 LLM 读取。层 2 的幻觉比层 1 的幻觉破坏力更大（用户 agent 会按错误指令行事）。

## 命中率提升技巧（层 1 为主，层 2 为辅）

| 技巧 | 原理 | 层 1 怎么用 | 层 2 怎么用 |
|---|---|---|---|
| **CoT 前置检查** | 每步决策前让 agent 自问是否有足够信息 | 每个 Phase 前加 `Before Phase N: verify you have X. If not, re-read Y.` | 不直接适用 |
| **负例** | 告诉模型「不要做什么」比「要做什么」更能阻断错误 | `No TODO, no pass, no NotImplementedError, no placeholders`——已有；可加强：`Do NOT restart the entire pipeline on failure; fix only affected files.` | Agent Constraints 加 `Must NOT fabricate data. If a metric is not computable, return null.` |
| **自检循环** | 跑校验前先用 checklist 自查 | Phase 5 加 `Self-check: go through every MUST item in the checklist before running validate.py` | 已有 `run_evals.py --validate` |
| **Few-shot 精简** | 用决策表替代长叙事示例 | Phase 1 三个域示例 → API 选择决策矩阵 | Output Example 从真实 pipeline 运行结果复制，不是手写 |
| **Grounding 链** | 每个 Phase 的输出引证上一阶段的发现 | Phase 3 必须引用 Phase 2 的 use cases | contract.json 锚定输出 schema |

## 失败处理技巧（层 1）

| 技巧 | 原理 | 具体操作 |
|---|---|---|
| **fix-only 重试** | 校验失败时只修报错的文件，不回滚整个 pipeline | Phase 5 补充：`If validate.py or check_pipeline.py fail, read ONLY the reported errors, fix ONLY the affected files, re-run the validator. Do NOT restart the entire pipeline.` |
| **结构化错误解读** | 告诉 agent 校验输出的格式和含义 | SKILL 里加注：`validate.py output: [ERROR] = blocking (must fix), [WARN] = advisory (fix recommended), Status: VALID = all gates pass` |

## 幻觉减少技巧（层 2 为主，层 1 为辅）

| 技巧 | 原理 | 层 2（生成物）怎么用 | 层 1（creator）怎么用 |
|---|---|---|---|
| **Output 来源强制** | 生成的 Output Example 必须是真实输出，不是手写 | pipeline-phases.md 模板加：`Output Example must be copied from a real pipeline run, not hand-written` | 不适用 |
| **Negative constraints** | 「不要编造」比正向约束更能阻断幻觉 | Agent Constraints 固定一条：`Must NOT fabricate or guess data. If a metric is not computable, return null.` | Phase 2 强化：`Every API call must reference a finding from Phase 1 Discovery` |
| **Uncertainty 标注** | 让 pipeline 标注它不确定的输出 | pipeline 输出加 `confidence` 字段；无法确定的值标 `null` 而非 mock 值 | 不适用 |
| **Grounding** | 输出锚定在具体数据上 | contract.json + Runtime Contract + 报告输出都来自计算 | 每个 Phase 命名依赖：`Phase 3 relies on Phase 2 output; Phase 4 relies on Phase 2+3 decisions` |
| **Chain-of-Verification** | 生成 → 自检 → 只保留通过的部分 | `run_evals.py` 逐条 golden case 验证输出一致性 | `validate.py` + `check_pipeline.py` + `security_scan.py` 三道门 |

## 扩展实施检查清单（在原基础上追加）

- [ ] SKILL.md：Phase 1 改为决策表，Phase 1-5 改为摘要 + 引用 pipeline-phases；Phase 5 checklist 改为一行引用；Reference Files 表加条件
- [ ] SKILL.md：Phase 5 加 fix-only 重试指令
- [ ] SKILL.md：每个 Phase 前加 CoT 前置检查（`Before Phase N: verify you have...`）
- [ ] SKILL.md：Phase 2/3 加 grounding 链依赖声明
- [ ] pipeline-phases.md：删除与 SKILL 重复的 Phase 概述；Phase 1 三个域示例改为 API 选择决策表
- [ ] pipeline-phases.md：SKILL.md body 模板加 `Do NOT` 负例段
- [ ] pipeline-phases.md：Output Example 模板标注「必须从真实 pipeline 运行结果复制」
- [ ] pipeline-phases.md：Agent Constraints 模板加 `Must NOT fabricate data` 固定条款
- [ ] quality-standards.md：删除重复 checklist，保留代码质量模式 + 测试策略
- [ ] architecture-guide.md：顶部加阅读条件；Section 3 前加显式分隔
- [ ] 其他 reference：SKILL 引用表加条件触发
- [ ] 运行 `python3 scripts/validate.py <生成的 CRM skill>` 确认质量不退化
- [ ] 运行 `python3 -m unittest discover -s scripts/tests -p 'test_*.py'` 确认全量测试无新增失败
- [ ] 更新 VERSION.md
