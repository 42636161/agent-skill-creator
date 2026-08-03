# Phase 4: Skill Description Generation

## Objective

Generate a structured description and Quick Profile for the skill, designed for optimal agent retrieval via lexical matching.

The description in the SKILL.md frontmatter is the **primary activation mechanism** across all platforms. There are NO `activation.keywords` or `activation.patterns` fields in marketplace.json. All retrieval signal must be embedded in the `description` field and the Quick Profile body section.

**See also**: `references/description-guide.md` for the category taxonomy, description template, and Quick Profile format spec.


---

## Step 0: Trigger Generation (READ FIRST)

Generate activation triggers that a target user — who may not know the skill's name or
technical terminology — would actually say. Follow these rules in order:

1. **Native language first.** If the user's description or input material is in Chinese
   (or any non-English language), generate triggers in that language as the primary set.
   English equivalents are supplementary, not primary.

2. **Cover three speech patterns every user naturally uses:**
   - **Feature request** (user knows what they want but not the skill name):
     "帮我把会员分个层", "create a weekly sales report"
   - **Problem description** (user describes symptoms, not the tool):
     "哪些会员很久没买了", "our competitors dropped prices, how bad is it"
   - **Half-informed** (user gives a file or context but under-specifies):
     "帮我看看这个表格", "here's my data, tell me what's going on"

3. **No bare acronyms.** For every technical term in the triggers, include its everyday
   equivalent. "RFM" alone is blocked — write "会员分层 (RFM)", "customer segmentation (RFM)".
   The litmus test: a retail store manager who has never heard of "RFM" must be able to
   trigger this skill.

4. **Trigger grammar.** Triggers are space-separated fragments. No trailing periods.
   Embed them in the  frontmatter after "Activates on:" / "Triggers on:" labels.

**Example output** (for member-rfm-segmenter-skill):




---


## Step 2: Assign Category

Pick exactly one category from the taxonomy defined in description-guide.md.

Decision order:
1. If the skill has a DAG/steps (`STEPS` dict in pipeline.py) → `cleaning-pipeline`
2. If the final output is a formatted report or structured summary → `report-generator`
3. If it computes new derived metrics from input → `analyzer` or `enricher`
4. Otherwise → `transformer`, `monitor`, `validator`, or `extractor` based on primary action

The category determines the opening phrase of the description:
- `cleaning-pipeline` → `A cleaning pipeline for...`
- `report-generator` → `A report-generator for...`
- `analyzer` → `An analyzer of...`
- `transformer` → `A transformer for...`
- `monitor` → `A monitor for...`
- `validator` → `A validator for...`
- `extractor` → `An extractor for...`
- `enricher` → `An enricher for...`

---

## Step 3: Extract Entities and Scenarios

From the Phase 2 use cases, extract:

**Entities** — all concrete nouns that a user would search by:
- Data types (CSV, SQLite, JSON, API)
- Table/field names (contacts, deals, region, rep, product, revenue)
- Domain terms (pipeline, forecast, dedup, normalization, indicator)

**Scenarios** — 4-6 concise labels for "When to use":
- Start with the use case name, compress to 2-4 words
- Mirror real user query vocabulary
- Examples: "weekly standup prep", "data cleanup", "pipeline review", "quarterly wrap", "trend analysis"

**Anti-scenarios** — 2-3 labels for "When NOT to use":
- What would a similar-but-wrong skill do?
- Examples: "ad-hoc SQL queries", "real-time dashboards", "one-time calculations"

---

## Step 4: Render Description from Template

Use the fixed template from description-guide.md:

```
A {category} for {domain}. Use for {scenario-list}. Input: {input-type}. Output: {output-type}. {supplement}.
```

With the category from Step 1 and entities/scenarios from Step 2.

**Example** (CRM cleaning pipeline):

```yaml
description: >-
  A cleaning pipeline for CRM data management. Use for weekly dedup,
  email validation, phone normalization, and regional pipeline reports.
  Input: SQLite contacts, deals, activities. Output: deduplicated tables
  and summary JSON with [region, pipeline_stage, rep, revenue].
```

**Example** (stock analyzer):

```yaml
description: >-
  An analyzer of stock price data. Use for RSI, MACD, and Bollinger
  Band computations. Input: OHLCV CSV with [date, open, high, low,
  close, volume]. Output: indicator values and signal flags as JSON.
```

### Format rules

- Total length: 40-60 words target, 80 words soft warning
- First 200 characters must cover the primary use case (claude.ai UI truncation boundary)
- Third person, no "I"/"we"
- No marketing adjectives ("amazing", "best", "powerful")
- Each scenario in `Use for` must match a real user query
- Each entity in `Input:` and `Output:` must match an actual use case

---

## Step 5: Verify Coverage

For each use case from Phase 2:

1. List 3-5 likely user queries for that use case
2. Check each critical noun and verb from those queries against the description text and trigger list
3. If any query has no lexical match in either description or triggers, add its scenario label

No minimum keyword count. This is a coverage check against real query vocabulary, not a keyword list.

---

## Step 6: Generate Quick Profile Body Section

From the same data, generate the SKILL.md body section:

```markdown
## Quick Profile

**Category**: {category}
**Input**: {input type}
**Output**: {output type}
**When to use**: {scenarios, comma-separated}
**When not**: {anti-scenarios, comma-separated}
```

This is the first body section of SKILL.md after `# /skill-name`.

See description-guide.md for field rules and examples.
