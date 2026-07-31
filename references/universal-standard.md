# Universal Skill Output Standard

**Version:** 1.0
**Purpose:** Authoritative reference for what `--universal` mode generates. Read
by the factory LLM during Phase 2-5 when `--universal` is active. Defines the
universal directory layout, AGENTS.md and SKILL.md templates, phase-specific
rules, eval harness spec, and distribution model.

---

## 1. Universal Directory Layout

### 1.1 Simple Skill Layout

```
skill-name/
├── SKILL.md
├── AGENTS.md
├── README.md
├── scripts/
│   ├── pipeline.py
│   ├── <domain modules>.py
│   └── utils.py
├── evals/
│   ├── spec.md
│   └── golden/
├── assets/
│   └── <optional configs/templates>
└── requirements.txt
```

`requirements.txt` is emitted only when third-party dependencies are used.
`evals/` is omitted when `--no-eval` is active.

Complex suites use the same principle: each component keeps only capability
docs, executable logic, tests/evals, assets, and dependency declarations.

### 1.2 Removed (vs Default Mode)

- publish/update/search commands
- `scripts/evolve.py`
- `scripts/staleness_check.py`
- `scripts/review_staleness.py`
- `scripts/dependency_health.py`
- `scripts/schema_drift.py`
- `scripts/skill_document.py`
- platform-specific activation examples

### 1.3 Not Removed

- `skillctl` and `VERSION.md` (repo-level, owned by agent-skill-creator)
- central registry publishing through `skillctl publish`
- generated skill metadata needed by `skillctl`: `name`, `description`,
  `metadata.version`
- `requirements.txt` (generated skill runtime dependencies)

### 1.4 File Roles

| File | Role |
|---|---|
| `AGENTS.md` | Dispatch card |
| `SKILL.md` | Complete operating contract |
| `README.md` | Human onboarding |
| `scripts/pipeline.py` | Single happy-path entry point |
| Domain modules | Skill logic |
| `evals/spec.md` | Command-only regression contract |
| `evals/golden/` | Golden input cases |
| `assets/` | Optional configs/templates |
| `requirements.txt` | Third-party dependency declaration |

Lifecycle concerns (installation, publishing, updating, migration, regeneration,
platform placement, modification) belong to agent-skill-creator and `skillctl`,
not to the generated skill package.

### 1.5 Core Boundary Principle

This is the main AI-utilization improvement:

```
skill = capability package
agent-skill-creator + skillctl = lifecycle manager
```

The generated skill contains only the files needed to understand, run, configure,
and verify the capability. All lifecycle concerns — distribution, installation,
publishing, updating, migration, modification — belong to agent-skill-creator
and skillctl, not to the generated skill package.

## 2. AGENTS.md Template

AGENTS.md is a dispatch card, not the full manual. It stays under 25 lines.

### 2.1 Tool-Class Template

````markdown
# <skill-name>

<one-line summary>

## What it does

<2 sentences. Describe the high-level capability for dispatch.>

## How to run it

```bash
python3 scripts/pipeline.py --input <input> --output <output>
```

## Full spec

See [SKILL.md](./SKILL.md) for input/output contracts, configuration, known
limits, and examples.
````

### 2.2 Skill-Class Template

````markdown
# <skill-name>

<one-line summary>

## What it does

<2 sentences. Describe the high-level capability for dispatch.>

<Activation alert: one sentence the agent relays to the user when the skill is
invoked.>

## Output

<One-sentence presentation rule: what to lead with, what to offer next.>

## How to run it

```bash
python3 scripts/pipeline.py --input <input> --output <output>
```

## Full spec

See [SKILL.md](./SKILL.md) for input/output contracts, configuration,
diagnostics, known limits, and examples.
````

### 2.3 Rules

- Under 25 lines total.
- One happy-path command only.
- No slash-command activation examples.
- No platform names.
- Do not duplicate the full SKILL.md contract.
- Skill-class variant adds the activation alert sentence and the Output section;
  tool-class variant omits both.

## 3. SKILL.md Template

SKILL.md is the complete operating contract. Tool-class outputs use a subset of
the sections below; skill-class outputs use all sections. Under 150 lines.

### 3.1 Frontmatter

```yaml
---
name: <skill-name>
description: >-
  <Natural-language capability description for intent matching.>
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
---
```

The `description` field is the primary activation signal for intent matching.
`metadata.version` is required so `skillctl publish` can tag and index the
skill.

### 3.2 Tool-Class Sections

1. `# <skill-name>`
2. `## What this skill does`
3. `## When to use it`
4. `## Input`
5. `## Output` — include one concrete JSON example with realistic data
6. `## How to run it`
7. `## Known limits`

### 3.3 Skill-Class Sections

1. `# <skill-name>`
2. `## What this skill does`
3. `## When to use it` — include fuzzy activation examples and a transparency
   cue (activation alert)
4. `## Input`
5. `## Output` — include one concrete JSON example with realistic data
6. `## How to run it` — single happy-path command plus parameter derivation
   rules
7. `## Config` — list configurable parameters, their defaults, and when the
   agent should offer to adjust them
8. `## Known limits`
9. `## Anti-goals` — what this skill intentionally does not do
10. `## Agent behavior` — see Section 3.4
11. `## Diagnostics` — see Section 3.5
12. `## Feature discovery` — see Section 3.6; omit if the skill has only one
    workflow dimension

### 3.4 Agent Behavior Section (skill-class only)

Constrains the agent's output presentation so the user gets a consistent
experience. Required content:

- **Presentation order:** which metric to lead with, which to group together,
  when to use a table vs. a paragraph vs. a list.
- **Config transparency:** which config parameters exist, what their defaults
  are, and under what circumstances the agent should offer to adjust them.
- **Follow-up prompts:** what the agent should say after presenting results to
  invite deeper exploration.

Example:

```text
Start with the grand total and data quality summary. Then offer to show the
top region, product, or sales rep. Use a table for per-category breakdowns
with more than three items; use inline text for three or fewer.
If outliers are detected, mention the count and suggest the user adjust the
sensitivity threshold.
```

### 3.5 Diagnostics Section (skill-class only)

Documents the structured diagnostic output the pipeline produces on failure, and
how the agent should surface it. Required content:

- **Diagnostic schema:** what fields the diagnostic JSON contains.
- **Agent guidance:** what to tell the user when a specific diagnostic fires.
- **Resolution hints:** what the user can do to fix the issue.

Minimum diagnostic fields:

- `unrecognized_input` — which input data was unrecognized
- `closest_match` — what the closest valid alternative was
- `action` — what the agent or user can do to fix it

Example:

```text
When a column cannot be detected, the pipeline exits with a structured error:
{
  "unrecognized_input": ["区域", "金额"],
  "closest_match": {
    "区域": ["region", "area", "territory"],
    "金额": ["amount", "revenue", "value"]
  },
  "action": "Add '区域' to assets/column_aliases.json"
}
Surfacing guidance: tell the user the column wasn't recognized, show the
closest match, and explain what the fix looks like.
```

### 3.6 Feature Discovery Section (skill-class, multi-dimension only)

Lightweight hints the agent adds to its response after completing the user's
request. For each dimension or analysis mode the skill supports, provide one
sentence summarizing what it reveals and when it is useful. The agent varies
which hint it shows across interactions.

Example:

```text
Related capabilities:
- Breakdown by region — see which area contributed the most revenue
- Breakdown by product — identify top and bottom performers
- Data quality report — detect duplicates, outliers, and missing values
```

### 3.7 Rules

- Under 150 lines total.
- No `Trigger` section.
- No slash-command invocation examples.
- No platform names.
- Include one concrete JSON output example with realistic data.
- For skill-class outputs: include Agent behavior, Diagnostics, and Feature
  discovery sections (Feature discovery optional when single-dimension).
- Parameter derivation rules go in the How to run it section for skill-class:
  tell the agent where each command parameter should come from — user input,
  data inspection, or default — and how to resolve ambiguity.

## 4. Phase Rules

### 4.1 Phase 2: Tool vs Skill Classification

During Phase 2, after intent derivation is complete, the factory must classify
the output as tool or skill. This decision drives all subsequent phases.

**Tool** — a deterministic pipeline where the agent's role is caller: parse user
input into command parameters, run, read output, relay to user. No domain
judgment required. Example: CSV dedup, SQL formatter, JSON validator.

**Skill** — a domain-aware plan with judgment rules, edge-case heuristics,
default interpretations, and presentation conventions. The agent's role is
domain doer: interpret user intent, decide which analysis path to take, surface
diagnostics, guide the conversation. Example: CRM report generator with data
quality checks, compliance reviewer.

Classification rules:

- If no domain interpretation is required beyond "parse params -> execute ->
  return output", classify as tool.
- If the creator material includes judgment rules, multiple analysis paths,
  heuristics, or domain conventions, classify as skill.
- When uncertain, prefer tool (under-spec): too little guidance is easier for an
  agent to compensate for than incorrect guidance.

### 4.2 Phase 4: Fuzzy Activation and Transparency Cues

Universal mode uses semantic capability matching instead of platform trigger
syntax.

Rules:

- The `description` frontmatter is the primary activation signal.
- Do not write slash-command trigger grammar into generated docs.
- Do not mention platform names as part of activation.
- Generate natural-language activation examples covering:
  - Explicit user requests (task name).
  - Implicit requests (user shows data without saying what to do).
  - Domain verbs without domain nouns, in the user's primary language.
  - English and the user's primary language as appropriate.
- For skill-class outputs, generate a transparency cue: a one-sentence
  activation alert the agent relays to the user when the skill is invoked.

Tool-class activation example:

```text
Use this tool when the user asks to deduplicate a CSV file, remove exact
duplicate rows, or clean up a messy export. If the user is not sure what
kind of dedup they need, this tool validates exact-match deduplication only.
```

Skill-class activation example:

```text
Activate this skill when: the user provides a CRM export and asks to clean
it, generate a weekly summary, check data quality, or break down sales by
dimension. This skill handles common CRM export formats and multiple column
name languages.

If the user drops a file without saying what they want, start by running the
full pipeline and presenting the summary — then offer to drill into specific
dimensions.

Activation alert: "Running CRM data check — detecting columns and preparing
report."

Anticipate fuzzy requests in the user's spoken language: e.g. "帮我看看这个
表格" (user shows a CRM export), "整理一下这周的数" (weekly report), "the
data from our Salesforce export looks off" (data quality check).
```

### 4.3 Phase 5: Implementation Rules

**Domain knowledge as data.** If the skill needs column-name aliases, threshold
values, default behaviors, type mappings, or language-specific translations,
store them as a structured data file under `assets/` (JSON or YAML), not as
hardcoded constants in Python scripts. Processing code reads from the data file.

**Structured diagnostic output on failure.** The pipeline must produce
structured diagnostic information when it cannot process input, not silent
defaults or empty JSON. At minimum the diagnostic must contain: which input data
was unrecognized, what the closest valid alternative was, and what the agent or
user can do to fix it.

**One entry point with parameter derivation rules.** The happy-path command
stays. For skill-class outputs, the SKILL.md also includes a structured
parameter derivation section that tells the agent where each command parameter
should come from — user input, data inspection, or default — and how to resolve
ambiguity.

## 5. Eval Harness

### 5.1 Simplified run_evals.py

Universal mode uses a simplified `scripts/run_evals.py` under 500 lines.

**Kept:**

- `--validate`
- `--output <path>`
- `--case <id>`
- `--rollout`
- `--promote`
- `--include-holdout`
- `--json`
- command criteria
- golden cases
- baseline comparison

**Removed:**

- `--judge`
- `--model`
- LLM judge backends
- API-key judge fallback
- subscription-runtime judge fallback
- canary checks
- model comparison tables
- usage sidecars
- `EVOLUTION.md` writes

### 5.2 Eval Spec Shape

```json
{
  "skill": "skill-name",
  "run": "python3 scripts/pipeline.py --input {input} --output {output}",
  "criteria": [
    {
      "id": "valid-output",
      "text": "Produced output has the expected structure",
      "type": "command",
      "cmd": "python3 -c \"import json,sys; json.load(open(sys.argv[1]))\" {output}"
    }
  ],
  "golden": [
    {
      "id": "case-1",
      "input": "golden/case-1/input.ext",
      "expected": null,
      "split": "val",
      "expected_status": "pending-first-green"
    },
    {
      "id": "case-2",
      "input": "golden/case-2/input.ext",
      "expected": null,
      "split": "test",
      "expected_status": "pending-first-green"
    }
  ]
}
```

### 5.3 Eval Spec Rules

- Generate `command` criteria only.
- Do not generate `llm-judge` criteria.
- Do not generate a `judge` block.
- Keep the golden-case strategy: at least three golden cases, with one
  `"split": "test"` holdout unless `--no-eval` is active.
- For skill-class outputs, at least one golden case must exercise a chain of
  inputs that tests domain judgment — not just structural correctness.

## 6. Distribution

### 6.1 No Per-Platform Installer

Universal skills do not ship their own per-platform installer, updater, or
modifier. Copying or cloning the skill directory is sufficient for direct use.
Every platform can use it by reading the files and running the same command:

```bash
python3 scripts/pipeline.py --input <input> --output <output>
```

### 6.2 Installation Paths

**Direct use:**

```bash
git clone <repo-url>
cd <skill-name>
python3 scripts/pipeline.py --input data.csv --output results.json
```

**Registry install (when available):**

```bash
python3 scripts/skillctl/__main__.py install <skill-name>
```

`skillctl` may copy the skill into platform-specific locations as an external
installer concern. The skill package itself does not contain platform adapters.

### 6.3 README.md Template

````markdown
# <skill-name>

<one sentence>

## Install

Use this directory directly, clone it from source, or install it from a registry
with `skillctl install <skill-name>` when the registry is available. Use
agent-skill-creator to modify, migrate, or regenerate the skill.

## Run

```bash
python3 scripts/pipeline.py --input <input> --output <output>
```

## Verify

```bash
python3 scripts/run_evals.py --rollout
```
````
