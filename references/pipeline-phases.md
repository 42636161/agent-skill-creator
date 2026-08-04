# Pipeline Phases — Detailed Reference

**Loaded: always.** This file contains the step-by-step instructions, decision tables,
templates, and checklists for each pipeline phase. SKILL.md has the phase overview and CoT checks.
Read this file phase by phase — do NOT load all 5 phases at once. Load the current phase only.

---

## Phase 1: Discovery

### Mixed-input Gate (READ FIRST)

Before entering the Decision Matrix for mixed input (file + sentence): if the user's
sentence is a vague "automate this" / "帮我处理一下" with no stated output format,
audience, or trigger — do NOT proceed to the Decision Matrix. Instead, present a
one-line hypothesis and ask:

> "From this data, it looks like you need [X output] for [Y audience]. Right?"

Wait for confirmation. This is NOT Phase 0 — it is a one-question sanity check that
takes one exchange and prevents building the wrong thing.

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

### Domain-Specific Methodology

When the skill involves quantitative analysis, add a compact formula reference table documenting
each formula, its edge cases, and validation rules. This table lives in the generated skill's
SKILL.md for user reference, and the formulas are implemented in pipeline.py.

Template:
| Analysis | Formula | Edge cases |
|---|---|---|
| {analysis name} | {formula in mathematical notation} | {what happens with zero, negative, missing values} |

Examples of what belongs in this table (for illustration only — actual formulas depend on the domain):
- Time-series comparisons: YoY growth rate, moving averages
- Ratios: conversion rate, error rate, completion rate
- Rankings: percentile, z-score, weighted score
- Segmentation: clustering thresholds, binning rules

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
| Weather dashboard: fetch data → compute trends → generate charts → export PDF | 1 → **simple** | The PDF is the only independently useful output |
| ETL pipeline: extract → transform → load → validate | 1 → **simple** | Loading without validation is not actionable |
| DevOps suite: deploy monitor, log analyzer, incident responder | 3 → **suite** | Each component produces a complete independently useful result |
| Content system: grammar checker, style enforcer, SEO optimizer | 3 → **suite** | Checkers can run independently on any text |
| Data analysis report: load CSV → clean → analyze → generate report | 1 → **simple** | Cleaning alone produces no business value |

**Anti-pattern**: Counting processing steps as workflows. "This skill has 5 steps → must be a suite" is wrong.
A pipeline with 10 steps that produces one useful output = 1 workflow = simple skill.

### Decision Framework

| Factor | Simple Skill | Complex Suite |
|--------|-------------|---------------|
| Workflows | 1-2 | 3+ distinct |
| Code size | <1000 lines | >2000 lines |
| Maintenance | Single developer | Team |
| Structure | Single SKILL.md | Multiple component SKILL.md files |

### Directory Structure — Agent Skills Open Standard

## Phase 4: Detection

### Trigger Generation (READ FIRST)

Generate activation triggers that a target user — who may not know the skill name or
technical terminology — would actually say. Follow these rules in order:

1. **Native language first.** If the user description or input material is in Chinese
   (or any non-English language), generate triggers in that language as the primary set.
   English equivalents are supplementary, not primary.

2. **Cover three speech patterns every user naturally uses:**
   - **Feature request** (user knows what they want but not the skill name):
     "帮我把会员分个层", "create a weekly sales report"
   - **Problem description** (user describes symptoms, not the tool):
     "哪些会员很久没买了", "our competitors dropped prices, how bad is it"
   - **Half-informed** (user gives a file or context but under-specifies):
     "帮我看看这个表格", "here is my data, tell me what is going on"

3. **No bare acronyms.** For every technical term in the triggers, include its everyday
   equivalent. "RFM" alone is blocked — write "会员分层 (RFM)", "customer segmentation (RFM)".
   The litmus test: a retail store manager who has never heard of "RFM" must be able to
   trigger this skill.

4. **Trigger grammar.** Triggers are space-separated fragments. No trailing periods.
   Embed them in the `description` frontmatter after "Activates on:" / "Triggers on:" labels.

**Example output** (for member-rfm-segmenter-skill):

```
Triggers on: 会员分层, 哪些会员最近没买了, 帮我看看会员数据,
             把客户分一下类, 高价值会员是谁, 沉睡会员唤醒,
             customer segmentation, member loyalty analysis
```

### Description Design

- 1-1024 chars. MUST start with "A {category}" or "An {category}".
- Good: "An analyzer of member purchase behavior..."
- Bad: "A tool that does RFM analysis..." (too generic, acronym-heavy)
- For non-English domains: write the description body in the domain's primary language
  where it adds clarity, but keep the "A {category}" opening in English (it is a
  machine-readable category signal).
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
- [ ] Triggers generated following 4-rule scene-driven approach (native language, 3 speech patterns, no bare acronyms)
- [ ] Triggers include everyday equivalents for all technical terms
- [ ] Multi-language keywords for non-English domains
- [ ] activation field in frontmatter: `/skill-name`
- [ ] provenance metadata in frontmatter (recommended)
## Phase 5: Implementation

### Code Architecture: Validate-Compute-Report Pattern

All pipeline scripts MUST follow a three-function structure, called in sequence:

```
validate_input()  ->  compute()  ->  generate_report()
     |                   |               |
  I/O only           Pure function     I/O only
  exit(1) on error   No side effects   Format + write
```

```python
def validate_input(args) -> dict:
    """Load all inputs, check integrity, return validated data. Exit on failure."""
    # 1. Check files exist
    # 2. Check every required column exists in every input
    # 3. On missing column: print "Missing column: X. Your file has: A, B, C" -> exit(1)
    # 4. Handle BOM, blank lines, trailing whitespace (encoding="utf-8-sig", skip blanks)
    # 5. Check key fields for duplicates -- warn or error, never silently discard
    # 6. Return pure data dict -- no file handles, no global state

def compute(data: dict) -> dict:
    """Pure function. No I/O. No side effects. Input dict -> output dict."""
    # 1. All sorted()/max()/min() use explicit key parameter. Never rely on default ordering.
    # 2. Threshold comparisons (>, >=, <, <=) verified for boundary correctness.
    #    When in doubt: >= for "at or above", < for strict "below".
    # 3. All classification thresholds computed BEFORE classification starts.
    # 4. Division operations have zero-denominator guards.
    # 5. Empty/missing values use explicit placeholders: "(unknown)", "N/A".

def generate_report(results: dict, output_dir: Path):
    """Format results -> write files + print summary to stdout."""
    # 1. report.md starts with executive summary, not data table
    # 2. stdout prints human-readable summary (<= 8 lines), not JSON
    # 3. Empty values labeled with "(unknown)" / "N/A" -- never blank cells
    # 4. Pipeline output contains computed values from input data -- not static text.
```

### Error Message Format

All user-facing errors follow a three-part structure:

```
1. What went wrong:   "Missing column: 营销费用"
2. What was expected: "Your CSV contains: 活动名称, 折扣力度, 销售额"
3. What to do:         "Add column or check column name spelling"
```

Never: bare Python tracebacks (TypeError, KeyError, FileNotFoundError).
Never: argparse default usage output without context.

### Input Schema Documentation

Generated skill's SKILL.md "Input" section MUST list all required columns by name with description:

```markdown
- **Input**: CSV with columns:
  - transaction_id -- unique identifier matching ERP and POS
  - sale_amount -- gross sale amount in local currency
  - store_name -- one of the valid store identifiers
```


### Tuning Chapter

Generated skill's SKILL.md MUST include a `## Tuning` section exposing configurable parameters
in user-facing language. Generate after pipeline.py is complete — back-scan all argparse
parameters, hardcoded thresholds, and config.json fields.

**Template:**

```markdown
## Tuning

The following parameters can be adjusted. The agent should suggest
changes when the data suggests defaults are inappropriate.

| Parameter | Default | What it controls | When to adjust |
|-----------|---------|------------------|---------------|
| 异常值敏感度 | 3.0 | Outlier detection threshold (std deviations from mean) | When data has natural extreme variance (e.g., luxury goods, seasonal spikes) |
| 评分分档数 | 5 | Number of bins for scoring/segmentation | When you need finer or coarser granularity (e.g., 3 tiers for executive summary) |
| ... | ... | ... | ... |
```

**Rules:**

1. Parameter names MUST be translated to the target user's language
   (e.g., "异常值敏感度" not "outlier_std_threshold" for Chinese users).
2. Every argparse argument, hardcoded threshold, and config.json key becomes a row.
3. "When to adjust" must describe a real-world scenario, not implementation details.
4. If the skill has zero tunable parameters, still include the section with a single row:
   "This skill has no configurable parameters — it works with default behavior out of the box."


### Output Location (MUST)

Generated skills are written to the current working directory under
`skills/<skill-name>/`:

```
skills/<skill-name>/
├── SKILL.md
├── AGENTS.md
├── scripts/
│   └── pipeline.py
├── evals/                    # only when eval files exist
│   └── <name>.eval.md
└── references/               # only if needed
```

At the end of Phase 5, state the absolute output path clearly so the user can
locate, run, and publish the skill. Example:

> 技能已生成: `/path/to/current/dir/skills/inventory-replenishment-skill/`

### File Creation Order

1. `SKILL.md` -- primary file, created FIRST (inside `skills/<skill-name>/`)
2. `scripts/pipeline.py` -- core implementation with validate/compute/report structure
3. `scripts/run_evals.py` -- eval harness (copy from `scripts/run_evals_template.py`)
4. `scripts/evolve.py` -- maintenance loop (copy from `scripts/evolve_template.py`)
5. `evals/<name>.eval.md` -- eval specification, ONLY when evals are generated (skip with --no-eval). Do not create an empty evals/ directory.
6. `AGENTS.md` -- <=25 line dispatch card (run command + SKILL.md link. Do NOT read scripts/)
7. `references/` -- only if detail exceeds SKILL.md 500-line limit. Merge into single `references/guide.md`.
8. NO README.md in generated packages -- install instructions live in skillhub, usage in SKILL.md.

### Output Quality Rules (MUST)

- [ ] `report.md` first 5 lines start with executive summary, NOT a data table
- [ ] Pipeline stdout in default mode prints human-readable summary (<=8 lines)
- [ ] Pipeline has `--json` flag for machine-readable JSON output
- [ ] Generated SKILL.md includes `## Runtime Contract` section with all 5 mandatory fields:
  - `Activation signal:` — when activating, agent declares "正在运行 <skill-name>" to the user
- `Only run:` — exact command with required flags
  - `Do not read scripts/` — implementation detail gate
  - `Output:` — what files are produced and where
  - `Primary anchor:` — which file/section to read first for conclusions
  - `stdout:` — what stdout produces (human summary, JSON, or silent)
- [ ] Runtime Contract includes `### Presenting Results` sub-section guiding how the calling agent should present output:
  - Lead with headline from primary summary field
  - Show primary breakdown as top-5 table sorted by value
  - Surface notable findings (outliers, data quality issues, top/bottom performers)
  - Offer one natural follow-up question
- [ ] Summary text is rule-generated (template-based), not LLM-dependent
- [ ] All `sorted()`/`max()`/`min()` calls use explicit `key` parameter
- [ ] Pipeline output changes when input data changes (no static/placeholder output)
- [ ] Required columns documented in SKILL.md Input section



### Diagnostics Encoding Rule (MUST)

When ``validate_input()`` detects column mismatches or missing required fields,
the pipeline MUST populate a ``_diagnostics`` key in the output JSON. Never
silently skip unmatched columns or return empty results.

**Output format:**

```json
{
  "_diagnostics": {
    "status": "partial | failed",
    "column_detection": {
      "unmatched": ["列名列表"],
      "best_guess": {"Amount": "Deal Value"},
      "hint": "Column names do not match supported language. Supported columns listed in SKILL.md."
    },
    "missing_required": ["amount", "date"]
  },
  "results": { ... }
}
```

**Agent interaction:** The calling agent reads ``_diagnostics`` and tells the user:
"Did not find 'Amount' column. Your columns 'Deal Value' aren't in the supported list. Rename or add support?"

**Template code:** ``_build_diagnostics()`` in ``pipeline_template.py`` provides the
structured helper. ``_match_columns()`` now returns ``(mapping, unmatched_list)`` instead
of only ``mapping``.

### Phase 5 Self-Check

Before running validate.py, verify the following content checks (in addition to
the existing Output Quality Rules):

- [ ] SKILL.md includes `## Runtime Contract` with all 5 mandatory fields
- [ ] SKILL.md includes `### Presenting Results` sub-section under Runtime Contract
- [ ] SKILL.md includes `## Tuning` section with a parameter table

Before running validate.py: self-check every MUST item in this checklist.

Before running validate.py: self-check every MUST item in this checklist.
If validate or check_pipeline fail: read ONLY the reported errors, fix ONLY the affected files, re-run.
After 3 repeated failures: stop and report to user with full error output.

### Phase 5 Checklist

- [ ] All files listed in File Creation Order exist
- [ ] SKILL.md body < 500 lines
- [ ] Output Quality Rules all satisfied
- [ ] Pipeline follows validate-compute-report pattern
- [ ] validate_input() checks all required columns exist before compute
- [ ] Error messages follow three-part format (what / expected / fix)
- [ ] Input files with BOM, blank lines, or trailing whitespace handled automatically
- [ ] SKILL.md includes ## Runtime Contract (5 mandatory fields + ### Presenting Results)
- [ ] SKILL.md includes ## Tuning section with user-facing parameter table
- [ ] Pipeline uses _build_diagnostics() when column mismatch detected (never silent skip)
- [ ] SKILL.md Input section lists all required columns by name
- [ ] NO bash/ps1/bat wrapper files at skill root
- [ ] NO EVOLUTION.md in initial delivery (generated post-delivery only)
- [ ] NO references/api-guide.md unless the skill genuinely needs an API
- [ ] NO empty evals/ directory (only create when eval files exist)
- [ ] NO README.md in generated package (skillhub + SKILL.md cover install/usage)
- [ ] AGENTS.md <= 25 lines (dispatch card only)
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

