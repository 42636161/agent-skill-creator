# User-Facing Quality Improvements for Generated Skills

**Status:** Draft
**Date:** 2026-07-29
**Author:** syh + Codex
**Subject:** Quality gaps discovered by evaluating the crm-reports-skill from a
            user's interaction perspective.

---

## 1. Context

This spec is the output of a brainstorming session that started from a single
question: "When a real user talks to their agent, and the agent loads a skill
we built — what actually happens?"

To answer that, we took a concrete generated skill — `crm-reports-skill` — and
simulated real user-agent conversations across four interaction patterns: the
ideal path, the boundary friction case, the disappointing-result case, and the
repeat-workflow case. Every interaction pattern exposed a different class of
quality gap. These gaps are not bugs in the current pipeline (the skill passes
all technical quality gates) but failures of *user experience design in the
skill artifact itself*.

The improvements below are structured as orthogonal concerns — each addresses a
distinct dimension of the user's experience. They are ordered from most
consequential (changes that reshape how a user perceives the skill's existence
and value) to most tactical (edge-case hardening).

---

## 2. Improvement Areas

### 2.1 Output presentation: close the JSON-to-human gap

**Problem.** The skill produces raw JSON. The user never sees it. The agent
must read the JSON, interpret it, and re-present it in natural language — but
the SKILL.md gives the agent zero guidance on how to do this. As a result,
different agents on different platforms will present the same report in wildly
different ways, from "Done. Report saved to report.json." (awful) to a
well-formatted table with narrative context (great but random).

**Root cause.** The skill defines its *output format* (the JSON schema) but
not its *output presentation contract*. The factory's quality gates
(validate.py, security_scan.py, run_evals.py) verify the JSON structure but
are structurally blind to what happens on the other side of the agent-skill
boundary.

**Proposed fix.** Add a `## Presenting Results` section to the SKILL.md
template that tells the agent *how to read the JSON and what to tell the user*:

```
## Presenting Results

After the pipeline runs and produces report.json, ALWAYS present results to
the user as follows:

1. **Lead with the headline.** Read `summary.grand_total` and
   `summary.date_range`. Display a one-line summary:
   "报告完成。{date_from} 到 {date_to}，全国总销售额 ¥{grand_total}。"

2. **Show regional breakdown.** For each dimension in `per_category`, render
   a table of the top 5 entries by total. If the user's prompt named a
   specific dimension (e.g., "按区域"), show that dimension first.

3. **Surface cleaning flags.** Check `cleaning.warnings` and
   `cleaning.actions`. Always mention:
   - How many duplicates were removed
   - How many outliers were flagged
   - Any date normalisations performed

4. **Offer a follow-up.** End with one natural question connected to the data,
   e.g., "华东销售下降明显，需要我深入分析华东的数据吗？"
```

This template is not prescriptive — it tells the agent what matters and in what
order, leaving the exact wording to the platform's native tone.

**What this changes for the factory.** The SKILL.md section template in the
factory's `references/templates/` directory gains a new section. The quality
standards gain a check: "SKILL.md contains a Presenting Results section."

---

### 2.2 Activation triggers: cover what users say, not what the spec expects

**Problem.** The AGENTS.md trigger list currently reads like an intent
catalogue written by the skill author:

```
- /crm-reports-skill
- "clean this CRM export"
- "weekly sales report"
- "regional totals from this CSV"
- "CRM report"
```

But real users say things like:

| User says | Matches current triggers? |
|---|---|
| "Here's this week's Salesforce export, can you look at it?" | No |
| "帮我看看这个表格" | No |
| "How did regions do last week?" | No |
| "Process this CSV" | Maybe — "CSV" matches but no CRM context |
| "I need numbers for the Monday standup" | No |
| "这份数据帮我整理一下" | No |

The skill lives or dies on whether the agent *recognizes that this is the skill
to use*. Missing triggers mean the skill never activates — the user gets a
generic answer from the agent's base knowledge instead of the specialized
pipeline.

**Root cause.** The current trigger-authoring process is: the skill creator
writes triggers based on what the skill *does*, not what users *say*. The
factory's prompt to the creator model asks "list activation phrases" but
doesn't push the model to role-play as a non-technical user.

**Proposed fix.** Three changes:

1. **Factory prompt upgrade.** During the Phase 3 (skill specification) step,
   the factory should explicitly instruct the creator model to generate
   triggers from the *user's mouth*, not the skill author's:
   > "Generate 8-12 activation triggers by role-playing a user who has
   > this problem. What would they type in natural language to their agent?
   > Include at least 3 triggers that don't mention the word CRM or report."

2. **Trigger template.** The AGENTS.md template gains structure:

   ```
   ## Triggers

   Trigger on ANY of these user statements:

   **Explicit intents** (user knows what they want):
   - "clean this CRM export"
   - "weekly sales report"

   **Implicit intents** (user describes the problem):
   - "this data looks messy, can you clean it up?"
   - "I need to present these numbers to my manager"

   **File-centric** (user provides a file without naming the domain):
   - "here's a CSV, make sense of it"
   - "can you analyze this spreadsheet?"

   **Chinese / localized** (must cover the user's native language):
   - "帮我整理这个销售表格"
   - "这周的数据帮我出个报告"

   Do NOT activate on: general spreadsheet questions, pivot table requests,
   or any task that doesn't involve sales/CRM data.
   ```

3. **Eval extension.** The run_evals.py spec gains an `activation_tests`
   block — a list of user utterances with a boolean `should_activate`. The
   eval runner doesn't execute these (activation depends on the agent
   platform) but emits a human-readable table so the skill reviewer can
   manually verify that the activation surface is adequate.

---

### 2.3 Error paths: fail loudly, helpfully, and in the user's language

**Problem.** When the skill encounters data it doesn't understand (e.g., a CSV
with Chinese column names like "区域" / "金额" / "日期"), the current code
returns an empty `per_category` dict with no error message. The only clue the
user gets is a JSON report full of empty sections. The user doesn't know what
went wrong or how to fix it.

Worse, when `detect_column_roles` finds zero matches, the agent has nothing to
tell the user. The skill failed silently.

**Root cause.** The pipeline treats "no columns matched" as a valid empty state
rather than a diagnostic event. There's no structured error output that the
agent can interpret and relay.

**Proposed fix.** Two-tier change:

**Tier 1: Structured diagnostics in the output JSON.** When column detection
finds zero matches for critical roles (amount, region), the output JSON
includes a `_diagnostics` field:

```json
{
  "summary": { ... },
  "per_category": {},
  "_diagnostics": {
    "status": "partial",
    "column_detection": {
      "detected_roles": {},
      "unmatched_columns": ["区域", "金额", "日期", "产品线", "销售代表"],
      "best_guess": {
        "区域": {"role": "region", "confidence": "high"},
        "金额": {"role": "amount", "confidence": "high"}
      },
      "help": "Column names not recognized. Supported languages: English, Portuguese, Spanish. Nearest match for each column: see best_guess."
    }
  }
}
```

This gives the agent actionable information: "I found these columns but they
don't match my dictionary. '区域' looks like it might be the 'region' column.
Do you want me to add Chinese column name support?"

**Tier 2: Agent-facing error contract.** The SKILL.md gains a section telling
the agent what to do with `_diagnostics.status === "partial"`:

```
## Error Handling

When the output contains `_diagnostics.status: "partial"`:
- Do NOT present an empty report as if it succeeded.
- Read `_diagnostics.column_detection` and tell the user which columns
  were not recognized.
- If `best_guess` exists, offer those as suggestions.
- Offer to retry with custom column mapping.
```

**What this changes for the factory.** The `clean_crm.py` and `analyze_crm.py`
templates gain a diagnostics-emitting code path. The quality standards gain a
check: "Skill produces `_diagnostics` on partial matches."

---

### 2.4 Configuration visibility: if the user can't find it, it doesn't exist

**Problem.** The skill has 6 configurable parameters (`dedup`,
`normalize_dates`, `date_format`, `flag_outliers`, `outlier_std_threshold`,
`fill_missing_amount`) but they live silently in `assets/config.json`. A user
in conversation will never discover them unless the agent volunteers the
information — and the current SKILL.md / AGENTS.md gives the agent no reason
to.

The result: every user runs the skill with default settings. If the defaults
don't fit their data (e.g., 3σ outlier threshold is too aggressive for their
deal sizes), they won't know they can fix it. They'll just conclude "this skill
doesn't work well for me."

**Root cause.** Configuration is treated as a filesystem concern
(`assets/config.json`) rather than a conversational concern. The agent's
"tool surface" doesn't include configuration as a discoverable concept.

**Proposed fix.** Add a lightweight configuration discovery line to the
SKILL.md Usage section, plus a configuration mention in the agent's post-run
presentation guidance:

In SKILL.md:
```
## Usage

You can tune the pipeline's behavior — just tell the agent and it will pass
the right flags:

| What you might want | Config key        | Default |
|---------------------|-------------------|---------|
| Keep duplicate rows | `dedup: false`    | `true`  |
| Change outlier sensitivity | `outlier_std_threshold: 2.0` | `3.0`  |
| Skip date reformatting | `normalize_dates: false` | `true`  |
| Change missing-amount fill value | `fill_missing_amount: 0.0` | `0.0`  |

The agent will capture your preference in a one-off config file and
pass `--config` to the pipeline.
```

In the presenting-results section, add:
```
5. **Surface configurability.** After presenting results, if outliers were
   flagged or defaults were applied, briefly mention one tunable option:
   "检测到 3 个异常值（当前阈值：3 个标准差），需要调低阈值让我更敏感地标注吗？"
```

**What this changes for the factory.** The SKILL.md template gains a tunable-
configuration table section. The presenting-results section gains a
configuration-surfacing rule.

---

### 2.5 Preview-confirm: let users inspect before committing

**Problem.** The pipeline is a single-shot operation: `--input → --output`.
There is no way to say "just show me what the cleaning step would do" or
"dedup these rows but don't discard them yet — let me review first."

For users working with messy, real-world CRM data, the ability to preview
changes is critical. They don't trust the machine to silently delete rows or
flag outliers without their review. The current design forces an all-or-nothing
decision.

**Root cause.** The pipeline's API is designed as a batch processor, not an
interactive tool. There's no intermediate output and no stage-gating.

**Proposed fix.** Add `--dry-run` mode to the pipeline:

```bash
python3 scripts/run_pipeline.py --input export.csv --output report.json --dry-run
```

In dry-run mode:
- The pipeline runs all cleaning steps but writes the *cleaning plan* instead
  of the final report
- Output is a preview JSON:

```json
{
  "dry_run": true,
  "plan": {
    "dedup": {"rows_affected": 3, "sample": ["Row 5 (duplicate of Row 2)", "Row 12 (duplicate of Row 7)"]},
    "normalize_dates": {"values_changed": 5, "sample": ["2026/07/21 → 2026-07-21"]},
    "outliers": {"flagged": 1, "detail": ["¥14,500 is 3.2σ above mean"]},
    "missing_fill": {"values_filled": 2, "detail": ["Row 8: amount blank → 0.00"]}
  },
  "estimated_report_summary": {
    "grand_total": 92399.50,
    "rows_after_clean": 47,
    "dimensions_detected": ["region", "product", "rep", "segment"]
  }
}
```

The agent then presents: "Here's what I'll do: remove 3 duplicate rows,
normalize 5 date formats, flag 1 outlier (¥14,500). Estimated grand total:
¥92,399.50 across 47 cleaned rows and 4 dimensions. Proceed?"

If the user says no to a specific operation (e.g., "don't flag outliers"),
the agent re-runs with the corresponding config override.

**What this changes for the factory.** The `run_pipeline.py` template gains
`--dry-run` logic. The quality standards gain a check: "Pipeline supports
`--dry-run` mode with a preview of cleaning actions."

Additionally, the SKILL.md gains a line in the Usage section documenting the
dry-run flow and what the agent should do with the preview.

---

### 2.6 Incremental / comparative workflows: "same report, this week's data"

**Problem.** A user who runs this report weekly experiences the skill as a
series of disconnected one-off invocations. Each week they must:
- Locate the new CSV
- Specify the output path
- Wait for the report
- Manually compare to last week's numbers

The skill has no concept of "last week's report" — no state, no comparison,
no diff. The user's mental model is "run the weekly report" but the skill's
model is "run a single pipeline on a single file."

**Root cause.** The skill is stateless by design. Statefulness is a
non-trivial feature that crosses into territory the current factory pipeline
wasn't designed for.

**Proposed fix.** A lightweight approach that doesn't require persistent
state: a `--compare` flag that accepts a previous report JSON and adds a
`comparison` section to the output:

```bash
python3 scripts/run_pipeline.py --input this_week.csv --output report.json \
  --compare last_week/report.json
```

The output gains:

```json
{
  "comparison": {
    "baseline": "last_week/report.json",
    "grand_total": {"this": 92399.50, "last": 95500.00, "delta": -3100.50, "delta_pct": -3.2},
    "by_region": {
      "East": {"this": 38110.00, "last": 41500.00, "delta": -3390.00, "delta_pct": -8.2},
      "West": {"this": 40210.50, "last": 39500.00, "delta": 710.50, "delta_pct": 1.8}
    }
  }
}
```

The presenting-results section then tells the agent to lead with the comparison
when a baseline exists, rather than starting from zero.

**What this changes for the factory.** The `run_pipeline.py` template gains
`--compare`. The quality standards add an optional check: "Pipeline supports
`--compare` with a previous report."

**Alternative considered.** A more ambitious approach would store report
metadata in the skill's output directory and automatically load the previous
report for comparison. This was rejected as too invasive — it introduces
mutable state into a skill that otherwise runs cleanly in a sandbox. The
`--compare` flag keeps state external and explicit.

---

### 2.7 Format flexibility: meet users where their data lives

**Problem.** The skill explicitly only supports CSV. Real CRM exports commonly
come as XLSX, XLS, or even TSV. The current response path is: the agent must
detect a non-CSV file and convert it first (consuming tokens and introducing
a failure point). Many agents won't do this automatically — they'll just say
"I can't handle XLSX files."

**Proposed fix.** The bootstrap wrapper (`crm-reports-skill`) gains
transparent format detection and conversion, leveraging Python's stdlib
`csv` module for CSV/TSV and the `openpyxl` library (if available) for XLSX.
The wrapper converts to a temporary CSV before calling the pipeline.

The quality standard becomes: "Bootstrap wrapper auto-converts XLSX, XLS,
and TSV to CSV. Conversion failures produce a structured error, not a crash."

**What this changes for the factory.** The bootstrap template gains
format-detection logic. The pipeline's prerequisite check gains a note:
"If openpyxl is not installed, XLSX support is unavailable — CSV/TSV only."

---

### 2.8 Activation transparency: tell the user which skill is running

**Problem.** When the agent loads a skill and starts executing it, the user
has no visibility into *which* skill is running. They see the agent's output
but don't know whether it came from base knowledge, a skill, or a tool call.
This matters when something goes wrong — the user needs to know "ah, this
behavior is from the crm-reports-skill, not from the agent itself" to debug.

**Proposed fix.** The AGENTS.md template gains a first-line rule:

```
## Activation Behavior

When this skill activates, ALWAYS begin your response with a brief
transparency note:
"📋 Running crm-reports-skill — cleaning and analysing your CRM export..."
```

This is a small addition that dramatically improves the user's mental model:
they know what's happening, who's doing it, and where to direct complaints.

**What this changes for the factory.** The AGENTS.md template gains one line.
No tooling changes needed.

---

## 3. Change Inventory

| # | Improvement | Files affected | Factory impact |
|---|------------|---------------|----------------|
| 2.1 | Output presentation guide | SKILL.md template | New section; quality check |
| 2.2 | Activation trigger coverage | AGENTS.md template; factory prompt | Prompt patch; eval extension |
| 2.3 | Error path diagnostics | `clean_crm.py`, `SKILL.md` templates | New code path; quality check |
| 2.4 | Configuration visibility | SKILL.md template | New section in usage + presenting |
| 2.5 | Preview-confirm mode | `run_pipeline.py`, `SKILL.md` templates | New flag; quality check |
| 2.6 | Comparative workflows | `run_pipeline.py`, `SKILL.md` templates | New flag; optional quality check |
| 2.7 | Format flexibility | Bootstrap wrapper template | New conversion logic |
| 2.8 | Activation transparency | AGENTS.md template | One-line addition |

---

## 4. Non-Goals (for this spec)

- **Persistent state or databases.** The skill remains stateless. Comparison
  (2.6) uses explicit references, not automatic state tracking.
- **Live CRM API integration.** Explicitly out of scope per the skill's
  anti-goals.
- **PDF/dashboard generation.** The skill outputs JSON — presentation is the
  agent's responsibility (per 2.1).
- **Changing the factory's five-phase pipeline.** This spec describes template
  and prompt improvements within the existing pipeline structure, not a new
  pipeline phase.
- **Evaluation of non-English language support beyond column detection.**
  The trigger coverage in section 2.2 recommends localized triggers but a full
  multilingual evaluation framework is a separate spec.

---

## 5. Self-Review

### Placeholder scan
None — all sections are complete.

### Internal consistency
All eight improvements are orthogonal (no two change the same template section
in conflicting ways). 2.1 (presentation guide) and 2.4 (config visibility)
both touch SKILL.md's usage section but are additive, not overlapping.

### Scope check
This is a focused spec. Each improvement is independently implementable. The
most impactful trio (2.1 + 2.2 + 2.3) could ship as a single PR.

### Ambiguity check
- Presentation guide (2.1): the tone is deliberately broad ("lead with the
  headline" rather than a mandatory format string) to accommodate different
  agent platforms.
- Trigger coverage (2.2): "8-12 triggers" is a guideline, not a hard gate.
  The eval extension is human-review, not automated.
