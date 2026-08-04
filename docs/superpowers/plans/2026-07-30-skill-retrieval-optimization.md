# Skill Retrieval Optimization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve agent retrieval of generated skills by replacing keyword-enumeration descriptions with an ontological Quick Profile structure, and updating validation to enforce the new format.

**Architecture:** Six files changed, one file created. The core reference (`description-guide.md`) defines a fixed category taxonomy, the description generation template, and the Quick Profile body format. Phase 4 uses the template instead of keyword enumeration. validate.py enforces Quick Profile required fields, description format, and the absence of per-skill AGENTS.md. No directory structure change, no schema change, no breaking change to existing skills.

**Tech Stack:** Python 3.10+, YAML frontmatter, Markdown, agent-skill-creator v6 pipeline.

---

### Task 1: Create `references/description-guide.md`

**Files:**
- Create: `references/description-guide.md`

- [ ] **Step 1: Write the Quick Profile section spec**

Write the body standard for generated SKILL.md. The Quick Profile sits as the first body section after the `# /skill-name` header:

```markdown
## Quick Profile

**Category**: {category}
**Input**: {input type and columns}
**Output**: {output type and structure}
**When to use**: {≥2 scenario labels}
**When not**: {≥1 anti-scenario}
```

Each field's rules:
- `Category` — exactly one value from the taxonomy (Task 1 Step 2)
- `Input` — data type first, then specific field names if applicable. Examples: `SQLite: contacts, deals, activities`, `CSV with columns [region, amount, rep]`, `API response: JSON array of sales records`
- `Output` — shape description. Examples: `cleaned tables + report JSON with [region, pipeline_stage, rep, revenue]`, `summary JSON: {regions, totals, rankings}`, `normalized CSV + schema card`
- `When to use` — 2-5 scenario labels, comma-separated. Not full sentences. Examples: `weekly dedup, standup prep, pipeline review, data prep for forecast-skill`
- `When not` — 1-3 **anti-scenarios**. Examples: `ad-hoc SQL queries, real-time dashboards`

- [ ] **Step 2: Write the category taxonomy**

```markdown
## Category Taxonomy

Every generated skill picks exactly one category. The choice is deterministic from the DAG and use case shape:

| Category | Opening phrase | Decision rule |
|----------|---------------|---------------|
| cleaning-pipeline | `A cleaning pipeline for...` | Has STEPS/DAG, primary action is data transform |
| report-generator | `A report-generator for...` | Output is a formatted report or structured summary |
| analyzer | `An analyzer of...` | Computes metrics, indicators, or scores from input |
| transformer | `A transformer for...` | Changes format or schema without computing new metrics |
| monitor | `A monitor for...` | Watches for threshold breaches, changes, or conditions |
| validator | `A validator for...` | Checks quality, consistency, or compliance of input |
| extractor | `An extractor for...` | Pulls data from external sources (APIs, databases, files) |
| enricher | `An enricher for...` | Adds derived fields or cross-references to existing records |

If the DAG has ≥2 steps with data passing between them → `cleaning-pipeline`.  
If the final output is a report → `report-generator`.  
If it computes new data from input → `analyzer` or `enricher`.

- [ ] **Step 3: Write the description generation template**

```markdown
## Description Generation Template

Fixed structure for the `description` frontmatter field:

```
A {category} for {domain}. Use for {scenario-list}. Input: {input-type}. Output: {output-type}. {supplement}.
```

Rules:
- Opens with category article: `A cleaning-pipeline for`, `An analyzer of`, `A report-generator for`
- `Use for` clause: 2-4 comma-separated scenario phrases. Each should match a real user query pattern
- `Input:` and `Output:`: same data as Quick Profile, but compressed to fit 40-60 words
- `{supplement}`: optional — additional constraints or context (e.g. "Works with any SQLite CRM database.")
- Total description length: 40-60 words soft target, 80 words hard warning in validate.py
- First 200 chars should cover the primary use case (claude.ai UI truncation boundary)
```

- [ ] **Step 4: Write the coverage check spec**

```markdown
## Coverage Verification

After generating the description, for each use case from Phase 2:

1. List the 3-5 most likely user queries for that use case (e.g. "clean my CRM data", "deduplicate contacts", "show me pipeline by region")
2. Check each critical noun and verb from those queries against the description text
3. If any query has no lexical match in the description, add its scenario label to the `Use for` clause or append to the scenario list

This is not a keyword count — it's a coverage check against real query vocabulary.

Coverage gaps are not an error. They are a signal to add a scenario label.
```

- [ ] **Step 5: Write the README.md generation template**

```markdown
## README.md Template

Every generated skill now ships with a README.md. Content only:

```markdown
# {skill-name}

Maintained by: agent-skill-creator  
Compatible with: Claude Code, Codex CLI, Cursor, Windsurf, Cline, Goose, Gemini CLI  

## Install

### Claude Code
```bash
cp -r ./{skill-name} ~/.claude/skills/{skill-name}
```

### Codex CLI
```bash
cp -r ./{skill-name} ~/.agents/skills/{skill-name}
```

### Cursor
```bash
cp -r ./{skill-name} .cursor/skills/{skill-name}
```

See [SKILL.md](SKILL.md) for usage.
```

No workflow description in README.md — that is SKILL.md's job. Only installation paths and platform compatibility.
```

---

### Task 2: Rewrite `references/phase4-detection.md`

**Files:**
- Replace: `references/phase4-detection.md`

- [ ] **Step 1: Write the new Phase 4 header**

Replace the entire file. New header:

```markdown
# Phase 4: Skill Description Generation

## Objective

Generate a structured description and Quick Profile for the skill, designed for optimal agent retrieval via lexical matching (Pathway A).
```

- [ ] **Step 2: Write Step 1 — Category assignment**

```markdown
### Step 1: Assign Category

Pick exactly one category from the taxonomy (see description-guide.md):

1. Check if the skill has a DAG/steps → pipeline categories
2. Check if the output is a report → report-generator
3. Check if it computes new metrics → analyzer or enricher
4. Otherwise → transformer, monitor, validator, or extractor based on primary action

The category determines the opening phrase of the description.
```

- [ ] **Step 3: Write Step 2 — Entity and scenario extraction**

```markdown
### Step 2: Extract Entities and Scenarios

From the Phase 2 use cases, extract:

**Entities**: All concrete nouns that a user would search by:
- Data types (CSV, SQLite, JSON)
- Table/field names (contacts, deals, region, rep, revenue)
- Domain terms (pipeline, forecast, dedup, normalization)

**Scenarios**: 4-6 concise labels for "When to use":
- Start with the use case name, compress to 2-4 words
- Mirror real user query vocabulary
- Examples: "weekly standup prep", "data cleanup", "pipeline review", "quarterly wrap"
```

- [ ] **Step 4: Write Step 3 — Render description from template**

```markdown
### Step 3: Render Description

Use the template from description-guide.md:

```
A {category} for {domain}. Use for {scenarios}. Input: {input}. Output: {output}. {supplement}.
```

Example:

```yaml
description: >-
  A cleaning pipeline for CRM data management. Use for weekly dedup,
  email validation, phone normalization, and pipeline reports by region
  and rep. Input: SQLite contacts, deals, activities. Output: deduplicated
  tables and regional summary JSON.
```
```

- [ ] **Step 5: Write Step 4 — Coverage verification**

```markdown
### Step 4: Verify Coverage

For each use case, identify 3-5 likely user queries. Check lexical coverage against the description. If coverage gaps exist, add missing scenario labels to the `Use for` clause.
```

- [ ] **Step 6: Write Step 5 — Generate Quick Profile**

```markdown
### Step 5: Generate Quick Profile Body Section

From the same data, generate the SKILL.md body section:

```markdown
## Quick Profile

**Category**: {category}
**Input**: {input-type}
**Output**: {output-type}
**When to use**: {≥2 scenarios}
**When not**: {≥1 anti-scenario}
```

The Quick Profile is the first section of the SKILL.md body.
```

- [ ] **Step 7: Remove all old keyword enumeration content**

Delete the sections about:
- 60+ keyword enumeration
- Keyword matrix per API metric
- Query variation testing
- Portuguese language variants
- Entity category expansion (move to description-guide.md if needed)

---

### Task 3: Update `references/pipeline-phases.md`

**Files:**
- Modify: `references/pipeline-phases.md`

- [ ] **Step 1: Update Phase 4 reference**

Find the line in pipeline-phases.md that references phase4-detection.md. Ensure it says:

```markdown
For detailed Phase 4 instructions (category assignment, description rendering, coverage verification): see `references/phase4-detection.md` and `references/description-guide.md`
```

- [ ] **Step 2: Update Phase 5 SKILL.md generation reference**

In the Phase 5 Implementation section, find where SKILL.md generation is described. Update to include:
- The Quick Profile section must be the first body section after `# /skill-name`
- Per-skill AGENTS.md is no longer generated
- README.md generation is now mandatory

- [ ] **Step 3: Update the generated skill directory listing**

Find the generated skill directory structure documentation. Remove `AGENTS.md` from the per-skill listing. Add a note: "per-skill AGENTS.md is not generated — selection information is in the SKILL.md Quick Profile section."

- [ ] **Step 4: Update the auto-install section**

Remove the AGENTS.md reference from the generated skill description table.

---

### Task 4: Update `scripts/validate.py`

**Files:**
- Modify: `scripts/validate.py`

- [ ] **Step 1: Add Quick Profile validation**

After existing validation code, add a `validate_quick_profile(skill_path, result)` function:

```python
def validate_quick_profile(skill_path: Path, result: dict) -> None:
    """Validate Quick Profile section in SKILL.md body."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        result["errors"].append("SKILL.md not found")
        return
    
    text = skill_md.read_text(encoding="utf-8")
    
    # Check Quick Profile section exists
    if "## Quick Profile" not in text:
        result["errors"].append("SKILL.md missing ## Quick Profile section")
        return
    
    # Extract the Quick Profile block (between ## Quick Profile and next ##)
    profile_match = re.search(
        r"## Quick Profile\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    if not profile_match:
        result["errors"].append("Could not parse Quick Profile section")
        return
    
    profile_text = profile_match.group(1)
    
    # Check required fields
    checks = [
        (r"\*\*Category\*\*", "Missing **Category** in Quick Profile"),
        (r"\*\*Input\*\*", "Missing **Input** in Quick Profile"),
        (r"\*\*Output\*\*", "Missing **Output** in Quick Profile"),
    ]
    for pattern, msg in checks:
        if not re.search(pattern, profile_text):
            result["errors"].append(msg)
    
    # Check When to use has at least 2 items (comma-separated)
    when_match = re.search(r"\*\*When to use\*\*\s*:\s*(.+)", profile_text)
    if when_match:
        items = [x.strip() for x in when_match.group(1).split(",") if x.strip()]
        if len(items) < 2:
            result["warnings"].append("Quick Profile When to use should have ≥ 2 items")
    else:
        result["errors"].append("Missing **When to use** in Quick Profile")
    
    # Check When not has at least 1 item
    when_not_match = re.search(r"\*\*When not\*\*\s*:\s*(.+)", profile_text)
    if when_not_match:
        items = [x.strip() for x in when_not_match.group(1).split(",") if x.strip()]
        if len(items) < 1:
            result["warnings"].append("Quick Profile When not should have ≥ 1 items")
    else:
        result["errors"].append("Missing **When not** in Quick Profile")
```

- [ ] **Step 2: Add description format validation**

```python
def validate_description_format(skill_path: Path, result: dict) -> None:
    """Validate description starts with A/An + noun."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return
    
    doc = SkillDoc(skill_md)
    desc = doc.metadata.get("description", "")
    
    if not re.match(r"^(A|An)\s+", desc):
        result["errors"].append(
            "description must start with 'A {category}' or 'An {category}'"
        )
    
    # Check description <= 80 words (soft warning over 60)
    word_count = len(desc.split())
    if word_count > 80:
        result["warnings"].append(
            f"description is {word_count} words (target: 40-60, warning: >80)"
        )
```

- [ ] **Step 3: Add per-skill AGENTS.md check**

```python
def check_no_agents_md(skill_path: Path, result: dict) -> None:
    """Warn if per-skill AGENTS.md exists (only factory root AGENTS.md is allowed)."""
    agents = skill_path / "AGENTS.md"
    if agents.exists():
        result["warnings"].append(
            "per-skill AGENTS.md found — selection info should be in SKILL.md Quick Profile"
        )
```

- [ ] **Step 4: Add README.md presence check**

```python
def check_readme_present(skill_path: Path, result: dict) -> None:
    """Warn if README.md is missing."""
    readme = skill_path / "README.md"
    if not readme.exists():
        result["warnings"].append("README.md not found — installation instructions are required")
```

- [ ] **Step 5: Wire the new functions into the main validation flow**

Add calls at the end of the main `validate_skill()` function:

```python
# Quick Profile validation
validate_quick_profile(skill_path, result)

# Description format  
validate_description_format(skill_path, result)

# No per-skill AGENTS.md
check_no_agents_md(skill_path, result)

# README.md
check_readme_present(skill_path, result)
```

Need to also add the import at the top:
```python
import re  # if not already imported
```

- [ ] **Step 6: Add test coverage for the new validation functions**

In `scripts/tests/`:

```python
def test_validate_quick_profile_present():
    # SKILL.md with Quick Profile → no error
    ...

def test_validate_quick_profile_missing():
    # SKILL.md without Quick Profile → error
    ...

def test_validate_description_format():
    # description starting "A pipeline for..." → no error
    # description starting "This skill does..." → error
    ...

def test_check_no_agents_md():
    # AGENTS.md present in skill dir → warning
    # AGENTS.md missing → ok
    ...
```

---

### Task 5: Update generated SKILL.md template

**Files:**
- Modify: `references/pipeline-phases.md` (SKILL.md generation section)

- [ ] **Step 1: Update the SKILL.md generation code in Phase 5**

In the phase5 SKILL.md generation instructions, add the Quick Profile as a mandatory body section:

```markdown
Generated SKILL.md body starts with:

```markdown
# /{skill-name}

## Quick Profile

**Category**: {category}
**Input**: {input details}
**Output**: {output details}
**When to use**: {scenarios}
**When not**: {anti-scenarios}

## Trigger

/{skill-name}

## Workflow
```
```

- [ ] **Step 2: Remove per-skill AGENTS.md generation from Phase 5**

In the Phase 5 file generation order, remove the AGENTS.md generation step. Add a note:

```
AGENTS.md is not generated per-skill. Selection information is in the 
SKILL.md Quick Profile section. The factory root AGENTS.md is unaffected.
```

- [ ] **Step 3: Add README.md as mandatory generation step**

In Phase 5 file generation order, add README.md after SKILL.md, using the template from description-guide.md.

---

### Task 6: Update the factory SKILL.md cross-references

**Files:**
- Modify: `SKILL.md` (factory root)

- [ ] **Step 1: Update the generated skill directory listing in Phase 5**

Find the directory listing in the factory SKILL.md (around line 316-325). Remove `AGENTS.md` from the generated skill structure. Change from:

```
skill-name/
├── SKILL.md
├── AGENTS.md
├── .claude-plugin/
├── scripts/
├── references/
├── assets/
├── evals/
├── install.sh
└── README.md
```

To:

```
skill-name/
├── SKILL.md           # Selection (description + Quick Profile) + execution (Workflow)
├── .claude-plugin/    # plugin.json + marketplace.json
├── scripts/           # Functional code + run_evals.py + evolve.py
├── references/        # Detail docs (loaded on demand)
├── assets/            # Templates, schemas, data files
├── evals/             # Eval spec + golden cases
├── README.md          # Installation instructions
└── install.sh         # Cross-platform installer
```

- [ ] **Step 2: Update the companion AGENTS.md description**

Find where the factory SKILL.md mentions "Every skill ships with: spec-compliant SKILL.md + AGENTS.md" — remove the AGENTS.md reference.

- [ ] **Step 3: Add cross-reference to description-guide.md**

In the "Reference Files" table at the bottom of the factory SKILL.md, add:

```
| `references/description-guide.md` | Quick Profile template + category taxonomy + description generation spec |
```
