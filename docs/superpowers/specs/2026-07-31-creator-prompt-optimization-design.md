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
