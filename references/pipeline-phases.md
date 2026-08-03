# Pipeline Phases — Detailed Reference

**Loaded: always.** This file contains the step-by-step instructions, decision tables,
templates, and checklists for each pipeline phase. SKILL.md has the phase overview and CoT checks.
Read this file phase by phase — do NOT load all 5 phases at once. Load the current phase only.

---

## Phase 1: Discovery

### Decision Matrix

| Signal | Decision |
|---|---|
| File-only input (.xlsx, .csv, .sqlite) | Skip API search. Use local parser: openpyxl (Excel), csv, sqlite3. Mark as no-api-needed. |
| User mentions a specific API or service | Use it. Research endpoints, auth, rate limits. |
| User mentions a data format (CSV, SQLite, JSON, XLSX) | Use stdlib or the most lightweight parser for that format. |
| User describes a periodic workflow (weekly, monthly) | Default to a report-generator pipeline with date-bounded queries. |
| No API or format mentioned | Ask user to clarify before researching. |
| Chinese e-commerce context (京东, 天猫, 淘宝) | Target: JD Open Platform, Taobao Open Platform. Auth: OAuth 2.0 with AppKey+AppSecret. |

### Phase 1 Checklist

- [ ] Input triaged (file-only → no API search)
- [ ] If API needed: minimum 3 options compared
- [ ] Decision made with justification
- [ ] API coverage decision: what endpoints are used, what are deferred
- [ ] Technical details documented (auth, rate limits, quirks)
- [ ] DECISIONS.md content prepared

---

## Phase 2: Design

### Use Case Development

1. List 15-20 typical questions the user would ask
2. Group by analysis type (Simple Queries, Temporal Comparisons, Rankings, Trends, etc.)
3. Prioritize: implement top 4-6 that cover 80% of use cases
4. Always include a **comprehensive report function**

### Analysis Specification Template

```markdown
## Analysis: [Name]

**Objective**: [1 sentence]
**Required inputs**: [type, description]
**Expected outputs**: [type, description]
**Methodology**: [explanation in natural language]
**Formulas**: Formula = ...
**Validations**: [criteria]
**Interpretation**: If result > X: [interpretation]; If < Y: [interpretation]
**Concrete example**: Input → Processing → Output
```

### Retail Domain Formula Reference (compact)

| Analysis | Formula | Edge cases |
|---|---|---|
| Sell-through rate (动销率) | sold / ((begin + end) / 2) | begin≤0 or end<0 → flag as data error |
| Promo lift | (promo_sales - baseline) / baseline | baseline=0 → skip, flag |
| Cannibalization | max(0, baseline - post_promo) / promo_sales | promo_sales=0 → skip |
| Promo ROI | (incremental_profit - marketing_cost) / marketing_cost | marketing_cost=0 → skip, flag |
| RFM scoring | Quantile-based (configurable bins) or fixed thresholds | Single-transaction members → handle gracefully |
| Four-quadrant | Margin × Turnover matrix with median thresholds | Seasonal products → score only in active season |

### Eval Criteria Rules

- 3-6 binary checks: each graded by shell `command` or flagged `llm-judge`
- At least 3 golden cases: seeded from user artifacts when available
- **Every golden case must include one boundary edge**: zero value, negative value, missing field, or extreme value
- Mark normal case as `split: "train"` and boundary cases as `split: "test"`
- `--no-eval` flag skips eval generation entirely

### Phase 2 Checklist

- [ ] 15+ typical questions listed
- [ ] 4-6 analyses defined with complete specification (objective, inputs, outputs, methodology)
- [ ] Formulas detailed with validations and interpretations
- [ ] Comprehensive report function designed
- [ ] Eval criteria defined (3-6 binary + ≥3 golden cases with boundaries)
- [ ] Retail formulas verified against compact formula table above

---

## Phase 3: Architecture

### Workflow Definition (READ FIRST)

A **workflow** is one independently callable execution path that produces a complete, useful result.
**One litmus test**: if the user runs only this component, do they get an actionable output?

| Answer | Classification | Example |
|---|---|---|
| Yes — the output alone drives a decision | = 1 workflow | Sales report → manager decides on staffing |
| No — the output is an intermediate artifact only meaningful when combined | = 1 step (not a workflow) | "Aggregate sales by hour" → useless without the shift generator |

**Examples (to calibrate judgment):**

| Scenario | Workflows? | Architecture |
|---|---|---|
| Monthly ops: sales rate, inventory health, staff efficiency, cost control | 4 → **suite** | Manager can review any single dimension and act |
| Daily store report: read Excel → aggregate sales → compute returns → generate summary | 1 → **simple** | Intermediate aggregations are not independently useful |
| Shift scheduler: read traffic → allocate by peak → output schedule | 1 → **simple** | Traffic analysis alone is not a schedule |
| ERP-POS reconciliation: match records → flag discrepancies → produce audit report | 1 → **simple** | Matching alone without the discrepancy report is not actionable |
| Financial suite: stock analysis, portfolio tracking, tax reporting | 3 → **suite** | Each domain produces a complete report independently |

**Anti-pattern**: Counting processing steps as workflows. "This skill has 5 steps → must be a suite" is wrong.
A pipeline with 10 steps that produces one useful output = 1 workflow = simple skill.

### Decision Framework

| Factor | Simple Skill | Complex Suite |
|--------|-------------|---------------|
| Workflows | 1-2 | 3+ distinct |
| Code size | <1000 lines | >2000 lines |
| Maintenance | Single developer | Team |
| Structure | Single SKILL.md | Multiple component SKILL.md files |

### Directory Structure — Agent Skills Open Standard## Phase 4: Detection

### Description Design

- 1-1024 chars. MUST start with "A {category}" or "An {category}".
- Include activation keywords in the description and in trigger examples.
- For Chinese domains: include both Chinese (动销率, 门店日报) and English keywords.
- For single-word input: the description should cover all expanded dimensions from Phase 0.

### Frontmatter Fields (MUST)

The generated SKILL.md frontmatter must include these fields to eliminate validate.py warnings:

```yaml
# Top-level fields (REQUIRED):
activation: /skill-name          # namespace enforcement — top level, NOT inside metadata

metadata:
  # REQUIRED:
  author: Author Name
  version: 1.0.0
  created: YYYY-MM-DD
  last_reviewed: YYYY-MM-DD
  review_interval_days: 90
  # RECOMMENDED — eliminates provenance warning:
  provenance:
    maintainer: agent-skill-creator
    source_references: []
```

### Phase 4 Checklist

- [ ] Description starts with "A {category}" or "An {category}"
- [ ] Description includes domain-specific activation keywords
- [ ] Trigger examples match user's likely invocation patterns
- [ ] Multi-language keywords for non-English domains
- [ ] activation field in frontmatter: `/skill-name`
- [ ] provenance metadata in frontmatter (recommended)
## Phase 5: Implementation

### File Creation Order

1. `SKILL.md` — primary file, created FIRST
2. `scripts/pipeline.py` — core implementation (or `scripts/run_pipeline.py` for multi-script)
3. `scripts/run_evals.py` — eval harness (copy from `scripts/run_evals_template.py`)
4. `scripts/evolve.py` — maintenance loop (copy from `scripts/evolve_template.py`)
5. `evals/<name>.eval.md` — eval specification
6. `AGENTS.md` — ≤25 line dispatch card (run command + SKILL.md link. Do NOT read scripts/)
7. `README.md` — skillctl install instructions only (no manual install table)
8. `references/` — only if detail exceeds SKILL.md 500-line limit. Merge into single `references/guide.md`.

### Output Quality Rules (MUST)

- [ ] `report.md` first 5 lines start with executive summary ("本周结论" or "Executive Summary"), NOT a data table
- [ ] Pipeline stdout in default mode prints human-readable summary (≤8 lines)
- [ ] Pipeline has `--json` flag for machine-readable JSON output
- [ ] Generated SKILL.md includes `## Runtime Contract` section:
  "scripts/ are implementation details, do not read by default. Only run: `python3 scripts/pipeline.py --input <file> --output <dir>`"
- [ ] Summary text is rule-generated (template-based), not LLM-dependent

### Phase 5 Self-Check

Before running validate.py: self-check every MUST item in this checklist.
If validate or check_pipeline fail: read ONLY the reported errors, fix ONLY the affected files, re-run.
After 3 repeated failures: stop and report to user with full error output.

### Phase 5 Checklist

- [ ] All files listed in File Creation Order exist
- [ ] SKILL.md body < 500 lines
- [ ] Output Quality Rules all satisfied
- [ ] NO bash/ps1/bat wrapper files at skill root
- [ ] NO EVOLUTION.md in initial delivery (generated post-delivery only)
- [ ] NO references/api-guide.md unless the skill genuinely needs an API
- [ ] AGENTS.md ≤ 25 lines (dispatch card only)
- [ ] README.md uses skillctl install only (no manual install table)
- [ ] validate.py passes with 0 errors
- [ ] security_scan.py passes with 0 high-severity findings
- [ ] Pipeline runs on golden case data

### Harness Contract

The generated skill's eval harness:
- `run_evals.py --rollout`: runs skill on golden inputs, scores real output
- `--promote`: captures first-green baselines (regression gate)
- `--judge`: grades llm-judge criteria with pinned judge (model + temperature)
- `"split": "test"` holdout cases: scored only at release, never fed to optimization loop
- `evolve.py`: runs staleness/dependency/drift checks + rollout; failures append to EVOLUTION.md
