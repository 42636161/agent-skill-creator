# Creator Prompt Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply token efficiency, accuracy, failure handling, hallucination reduction, and two-layer prompt engineering techniques to the creator's instruction files.

**Architecture:** Four files are modified (SKILL.md, pipeline-phases.md, quality-standards.md, architecture-guide.md); VERSION.md records the change. Each task targets one file with precise edits.

**Tech Stack:** Markdown.

---

## File Structure

- Modify: `SKILL.md`
- Modify: `references/pipeline-phases.md`
- Modify: `references/quality-standards.md`
- Modify: `references/architecture-guide.md`
- Modify: `VERSION.md`

---

## Task 1: SKILL.md — Phase descriptions condensed to index + CoT gates + fix-only retry + grounding

- [ ] **Step 1: Condense Phase 1-5 overview paragraph**

The paragraph at "### Stage 2: Build and Verify (Phases 3-5)" followed by the 5-phase bullet list — replace the bullet list with compact phase summaries:

Change from:
```
Phase 1: DISCOVERY       Read all material, research APIs, data sources, tools
Phase 2: DESIGN          Generate internal specification (use cases, methods, outputs)
Phase 3: ARCHITECTURE    Structure the skill directory (simple vs. complex suite)
Phase 4: DETECTION       Generate structured description + Quick Profile section
Phase 5: IMPLEMENTATION  Create all files, validate, security scan, deliver
```
To:
```
Phase 1: DISCOVERY       Research APIs, data sources, tools → internal research notes.
                         Before starting: verify the user's raw material is fully read.
                         See pipeline-phases.md §Phase 1 for the full procedure.
Phase 2: DESIGN          Use cases, analyses, eval criteria → internal spec.
                         Before starting: verify Phase 1 research is complete.
                         See pipeline-phases.md §Phase 2.
Phase 3: ARCHITECTURE    Simple skill vs complex suite decision → directory structure.
                         Before starting: verify Phase 2 use cases are defined.
                         See architecture-guide.md §1-2 then pipeline-phases.md §Phase 3.
Phase 4: DETECTION       Description, keywords, Quick Profile → SKILL.md frontmatter.
                         See description-guide.md then pipeline-phases.md §Phase 4.
Phase 5: IMPLEMENTATION  Create all files, validate, security scan, deliver.
                         Before running validate.py: self-check every MUST item in
                         pipeline-phases.md Phase 5 Checklist.
                         If validate.py/check_pipeline.py fail: read ONLY the reported
                         errors, fix ONLY the affected files, re-run the validator.
                         Do NOT restart the entire pipeline.
```

- [ ] **Step 2: Add CoT pre-checks to each Phase instruction section**

For each Phase section in SKILL.md (Phases 1-5 under "### Stage 1/2"), add one line at the top:

Phase 1 (SDK-based detection section): add
`Before starting Phase 1: verify all user-provided material (text, URLs, files, PDFs) has been fully read and understood.`

Phase 2 (after "### Stage 2"): add
`Before starting Phase 2: verify the full spec from Phase 1 Discovery is complete — APIs documented, data sources named, domain entities listed.`

Phase 3 (before architecture section): add
`Before starting Phase 3: verify Phase 2 Design has produced a complete internal specification with use cases, analyses, and eval criteria. Phase 3 decisions must reference these use cases.`

Phase 4 (before detection section): add
`Before starting Phase 4: verify Phase 2 use cases and Phase 3 architecture decisions are finalized. The description must be derived from these, not invented.`

Phase 5 (before implementation section — already partially done in Step 1, add self-check line): ensure the self-check line from Step 1 is in place.

- [ ] **Step 3: Replace Phase 5 embedded checklist with reference**

In the Phase 5 section, locate any embedded checklist items and replace with:
`Complete the Phase 5 Checklist in pipeline-phases.md. Every MUST item must pass before deliver.`

- [ ] **Step 4: Add fix-only retry to Phase 5**

In the Phase 5 "validation" paragraph (around line where validate.py/security_scan.py are mentioned), ensure this text is present:

`If validate.py or check_pipeline.py return errors: read ONLY the [ERROR] lines, fix ONLY the files named in those lines, re-run the failing validator. Do NOT restart the pipeline from Phase 1. If the same error repeats 3 times, stop and report to the user with the full error output.`

- [ ] **Step 5: Add structured error interpretation note**

After the first mention of validate.py in Phase 5, add:
`validate.py output format: [ERROR] = blocking — the skill cannot be delivered until fixed. [WARN] = advisory — fix recommended but does not block delivery. Status below the divider line reports VALID or INVALID.`

- [ ] **Step 6: Update Reference Files table with conditional gates**

The Reference Files table at the bottom of SKILL.md — update each entry's description column:

Replace unconditional descriptions with conditional triggers:
- `pipeline-phases.md`: `Detailed Phase 1-5 implementation instructions (always read)`
- `quality-standards.md`: `Code quality patterns, testing strategy, dependency management (always read)`
- `architecture-guide.md`: `Read §1-2 for every skill (decision framework + simple skill structure). Read §3+ only when the skill is complex (3+ workflows) or a refactoring.`
- `description-guide.md`: `Quick Profile template, category taxonomy (always read during Phase 4)`
- `phase4-detection.md`: `Detection & description generation process (always read during Phase 4)`
- `phase2-eval-assessment.md`: `Eval spec design reference (always read during Phase 2)`
- `cross-platform-guide.md`: `Only read when the skill targets Tier 2 (Cursor, Windsurf, Trae, Junie) or Tier 3 platforms (Zed, Augment, Aider)`
- `universal-standard.md`: `Only read when --universal mode is active`
- `export-guide.md`: `Only read when exporting the skill for Desktop/Web or API use`
- `multi-agent-guide.md`: `Only read when the skill requires 3+ distinct independent components`
- `interactive-mode.md`: `Only read when in interactive (wizard) creation mode`
- `templates-guide.md`: `Only read when using template-based skill creation`
- `agentdb-integration.md`: `Future design sketch — not implemented; skip`

---

## Task 2: pipeline-phases.md — Delete duplicates, replace examples, add negative patterns

- [ ] **Step 1: Delete Phase 1 long domain examples**

Locate Phase 1's "Discovery Examples" section (agriculture, stock, climate narratives). Replace with:

```
### Decision matrix (replaces domain-specific examples)

When choosing APIs and analyses, use this table instead of fixed examples:

| Signal | Decision |
|---|---|
| User mentions a specific API or service | Use it. Research its endpoints, auth, rate limits. |
| User mentions a data format (CSV, SQLite, JSON, XLSX) | Use stdlib or the most lightweight parser for that format. |
| User describes a periodic workflow (weekly, monthly) | Default to a report-generator pipeline with date-bounded queries. |
| User mentions multiple data sources | Start with the source that has the richest schema; enrich from others. |
| No API or format mentioned | Ask the user to clarify data source and format before researching. |
| Task involves visualization or charting | Use matplotlib (static) or generate data for React chart components. |
```

- [ ] **Step 2: Delete Phase 1-5 overview paragraphs that duplicate SKILL.md**

For each Phase section in pipeline-phases.md, delete the opening paragraph that describes "what this phase does" (it's already in SKILL.md). Replace with:

`See SKILL.md Phase N for the phase overview and CoT pre-checks. This section covers the implementation procedure.`

- [ ] **Step 3: Add "Do NOT" negative examples to SKILL.md body template**

In the Phase 5 body structure section, after the Output Example block and before the template closing, add:

```
## Do NOT

- Do NOT include a file tree in README or SKILL.md — the agent can derive it.
- Do NOT hand-write the Output Example; copy it from an actual pipeline run.
- Do NOT generate bash/ps1 wrapper scripts at the skill root.
- Do NOT generate multiple reference files; merge into single references/guide.md.
- Do NOT ship EVOLUTION.md in the initial delivery.
```

- [ ] **Step 4: Enforce Output Example source**

In the Phase 5 body structure section, update the Output Example paragraph to include:
`The Output Example must be copied from a real pipeline run — do not hand-write or guess field values.`

- [ ] **Step 5: Add anti-fabrication clause to Agent Constraints template**

In the AGENTS.md dispatch card template (Step 2.5), add this as a fixed constraint:

`N. Must NOT fabricate or guess data. If a metric is not computable from the pipeline output, return null or "Unknown" — never a plausible value.`

- [ ] **Step 6: Add grounding chain to Phase 3 instructions**

In Phase 3 architecture section, add before the decision flowchart:

`Phase 3 decisions (simple vs complex, directory structure) must reference the use cases defined in Phase 2 Design. Do not introduce new use cases here.`

---

## Task 3: quality-standards.md — Remove checklist duplicates

- [ ] **Step 1: Delete duplicated Phase 5 checklist**

Search for any section containing checklist items that also appear in pipeline-phases.md Phase 5 Checklist. Replace with:

`The full Phase 5 implementation checklist is in pipeline-phases.md. This file covers quality standards that apply across all phases and are not phase-specific.`

- [ ] **Step 2: Replace duplicated code template with reference**

If there is a code quality template section that duplicates content from pipeline_template.py, replace with:

`Code-level templates (shebang, docstrings, type hints, error handling) are defined in scripts/pipeline_template.py. Follow that template; do not maintain a second copy here.`

---

## Task 4: architecture-guide.md — Add conditional reading gate

- [ ] **Step 1: Add reading guide at top**

Insert after the Version/Purpose header line:

```
## Reading guide

- Sections 1-2 (decision framework + simple skill structure) are needed for
  every skill generation. Always read these first.
- Sections 3+ (sizing patterns, refactoring, complex suites, versioning,
  performance) are on-demand — only read when the skill is complex (3+
  distinct workflows), a refactoring of an existing skill, or a suite.
  SKILL.md will tell you when to come back here.
```

- [ ] **Step 2: Add visible split marker before Section 3**

Before `## 5. Directory Sizing Patterns` (the beginning of "on-demand" content), insert:

```
---
<!-- Everything below is on-demand. Only read if SKILL.md or Phase 3 tells you to. -->
---
```

---

## Task 5: VERSION.md and verification

- [ ] **Step 1: Add VERSION entry**

Insert at top of VERSION.md:

```
## v0.6.0 — 提示词工程优化（2026-07-31）

### 变更

- **token 效率** — SKILL.md Phase 描述收为索引；Reference Files 表加条件触发；
  pipeline-phases.md 去掉与 SKILL 重复的 Phase 概述和长示例（改为决策表）；
  quality-standards.md 去掉重复 checklist；architecture-guide.md §3+ 加条件门。
- **命中率** — 每个 Phase 前加 CoT 前置检查；模板加「Do NOT」负例；
  PipelinePhase 加 self-check 步骤；Phase 2/3 加 grounding 链。
- **失败处理** — Phase 5 加 fix-only 重试指令和结构化错误解读。
- **幻觉减少** — Output Example 强制从真实运行复制；Agent Constraints 加
  Must NOT fabricate 固定条款；Uncertainty 标注规范。

### 变动文件

```
SKILL.md                     — 改写：Phase 摘要 + CoT 前置检查 + fix-only 重试 + 条件引用表
references/pipeline-phases.md — 改写：删重复 Phase 概述 + 决策表替代长示例 + 负例 + 反编造条款
references/quality-standards.md — 改写：删重复 checklist
references/architecture-guide.md — 改写：阅读引导 + 条件分隔线
VERSION.md                   — 新增：本次版本记录
```
```

- [ ] **Step 2: Run verification**

```bash
python3 scripts/validate.py /Users/syh/Documents/Codex/2026-07-31/agent-skill-creator-users-syh-desktop-2/outputs/sqlite-crm-weekly-report-skill
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -q
```

Expected: no new test failures beyond the 20 pre-existing validate.py Quick Profile / description format issues.

- [ ] **Step 3: Commit**

```bash
git add SKILL.md references/pipeline-phases.md references/quality-standards.md references/architecture-guide.md VERSION.md
git commit -m "feat: prompt engineering optimization — token efficiency, accuracy, failure handling, hallucination reduction"
```
