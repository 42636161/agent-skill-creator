# Skill Retrieval Optimization Design — 修订版

**Date**: 2026-07-30  
**Status**: Draft  
**Author**: Codex  

---

## 1. 问题

### 1a. 文件重叠
生成的 skill 中 SKILL.md 和 AGENTS.md 的 frontmatter `description` 完全一致，AGENTS.md 的 `## Purpose` 是 SKILL.md description 的同义改写。两处维护，靠人保持同步，实际上不会同步。

### 1b. 描述生成是关键词枚举法
Phase 4 当前策略：列举 60+ 关键词来确保 lexical 命中。优化了关键词密度，但没有优化语义覆盖和决策引导。不同 skill 的描述风格不统一，agent 学了一个的匹配模式不能推广到另一个。

### 1c. 选择信息散在正文中
"什么时候该用这个 skill" 的信息隐含在 workflow 的 prose 里。选择阶段的 agent 不应该为做决定而解析 workflow 细节。

---

## 2. 解决思路

基于真实 GitHub 高星 skill 项目的行业共识（gamedev-skills, ok-skills, bazi-ziwei-skill, awesome-design-skills）：

- 每个 skill **只有 SKILL.md** 一个文件
- 选择信号集中在 frontmatter `description`（代理预读）
- 选择细节在 body 首段 Quick Profile（激活后读）
- 执行信息在 Quick Profile 之后的 Workflow
- 不生成 per-skill AGENTS.md

### 渐近披露

| Tier | 内容 | 加载时机 | 预算 |
|------|------|---------|------|
| 1 — 选择 | frontmatter name + description | 启动时，每个 skill 都加载 | ~100 tokens/skill |
| 2 — 执行 | SKILL.md body：Quick Profile + Workflow | skill 激活后 | <5000 tokens |
| 3 — 资源 | scripts/ + references/ | 按需 | 不限 |

---

## 3. SKILL.md 规格

### 3.1 Frontmatter

```yaml
---
name: weekly-crm-skill
description: >-
  A cleaning pipeline for CRM data management. Use for weekly dedup of
  contacts, email validation, phone normalization, and pipeline reports
  by region and rep. Input: SQLite contacts/deals/activities. Output:
  deduplicated tables and regional summary JSON. Works with any SQLite
  CRM database.
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
  created: 2026-07-30
  last_reviewed: 2026-07-30
  review_interval_days: 90
---
```

description 的固定结构：`A {category} for {domain}. Use for {场景}. Input: {输入}. Output: {输出}. {补充条件}.`

### 3.2 Body — Quick Profile（首段）

```markdown
# /skill-name

## Quick Profile

**Category**: cleaning-pipeline  
**Input**: SQLite: contacts, deals, activities  
**Output**: deduplicated tables + report JSON with [region, pipeline_stage, rep, revenue]  
**When to use**: weekly dedup, standup prep, pipeline review, data prep for forecast-skill  
**When not**: ad-hoc SQL queries, real-time dashboards  

## Trigger

/skill-name

## Workflow

...
```

Quick Profile 是 body 的第一个 section。Workflow 紧随其后。

---

## 4. Description 生成（Phase 4 替换）

替换当前的关键词枚举法。使用两步骤：

### Step 1: 构建本体骨架

```
category = pick one from [cleaning-pipeline, report-generator, analyzer, ...]
domain   = pick from domain tree
input    = 数据类型加具体字段名
output   = 产出类型加具体结构
```

### Step 2: 渲染 description

模板：`A {category} for {domain}. Use for {场景}. Input: {输入}. Output: {输出}.`

### Step 3: 覆盖率检查

对每个 use case，检查核心名词和动词是否在 description 中出现。遗漏则补到 Use for 句尾。

---

## 5. 类别分类法

| Category | 开头 | 适用条件 |
|----------|------|---------|
| cleaning-pipeline | `A cleaning pipeline for...` | 有 DAG/STEPS 的多步数据处理 |
| report-generator | `A report-generator for...` | 从数据生成结构化报告 |
| analyzer | `An analyzer of...` | 计算指标、评分、衍生数据 |
| transformer | `A transformer for...` | 格式或 schema 转换 |
| monitor | `A monitor for...` | 监控阈值、变化、条件 |
| validator | `A validator for...` | 检查质量、一致性、合规性 |
| extractor | `An extractor for...` | 从外部源拉取数据 |
| enricher | `An enricher for...` | 在已有记录上增加衍生数据 |

---

## 6. 验证规则（validate.py 新增）

| Rule | Severity | Condition |
|------|----------|-----------|
| Quick Profile present | error | body 必须有 `## Quick Profile` section |
| Category in Quick Profile | error | Must have `**Category**` |
| Input in Quick Profile | error | Must have `**Input**` |
| Output in Quick Profile | error | Must have `**Output**` |
| When to use ≥ 2 | error | Must have ≥ 2 use bullets |
| When not ≥ 1 | error | Must have ≥ 1 not-use bullet |
| description 格式 | error | 必须以 `A {noun}` 或 `An {noun}` 开头 |
| 无 per-skill AGENTS.md | warning | skill 目录下不应有 AGENTS.md（工厂根目录的保留） |
| README.md present | warning | 应包含 README.md |

---

## 7. 文件改动

| File | Action | Reason |
|------|--------|--------|
| references/description-guide.md | Create | Quick Profile 模板 + description 生成规范 + 类别分类法 |
| references/phase4-detection.md | Rewrite | 关键词枚举 → 本体生成 + 覆盖率验证 |
| references/pipeline-phases.md | Update | Phase 4 和 Phase 5 引用到新格式 |
| scripts/validate.py | Update | 新增 8 条验证规则 |
| Generated AGENTS.md | Remove | 不再生成 per-skill AGENTS.md |
| Generated SKILL.md template | Update | 首段加上 Quick Profile |
| README.md template | Add | 生成的 skill 必须带安装说明 |

## 8. 不动的内容

- SKILL.md frontmatter schema（不改字段结构）
- contract.json schema（不改）
- 目录结构（不改）
- `--universal` 模式兼容性（不变）
- scripts/pipeline_template.py（不变）
- install.sh（不变）
