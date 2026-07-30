# Universal Skill Output Design

## Context

agent-skill-creator currently produces skills with a broad distribution layer:
SKILL.md, AGENTS.md, platform manifests, install scripts, bootstrap wrappers,
maintenance scripts, eval harnesses, references, assets, and cross-platform
export metadata.

The repository also now includes a GitHub-backed distribution path documented in
`VERSION.md`: `skillctl`, a central registry, semantic search, publish/install
commands, and registry-driven discovery. That layer is different from the
per-skill platform adapters this design removes. `skillctl` is an external
distribution mechanism; universal mode controls what is generated inside each
skill package.

That default is useful when the goal is broad platform distribution. It is less
ideal when the goal is maximum agent usability: generated skills carry platform
artifacts, platform-specific invocation patterns, and maintenance machinery that
agents must read past before finding the actual capability contract.

This design adds an opt-in universal output mode for users who want generated
skills to be platform-agnostic, compact, and directly usable by any agent
runtime that can read files and run scripts.

## Design Sources

This design incorporates findings from `2026-07-29-user-quality-evaluation-design.md`,
which evaluates generated skills from the agent perspective and the end-user
perspective. The following universal findings (abstracted from CRM-sample
observations) drive changes below:

| Finding ID | Summary | Impact |
|---|---|---|
| B-1 | Tool vs Skill boundary: factory treats all inputs the same; some are deterministic automation, others carry domain judgment | Phase 2 Design, Phase 3, Phase 5 templates |
| A-a-4 | Agent execution guidance is implicit: SKILL.md has CLI reference but no structured behavior map | SKILL.md Design — new sections |
| B-3 | Domain knowledge (aliases, thresholds) hardcoded in Python instead of separate data files | Phase 5 Implementation rules |
| A-a-2 | Error paths produce silent defaults instead of structured diagnostics | Phase 5 Implementation rules |
| A-a-1 | Trigger examples only cover author-language speech, not fuzzy user expressions | Phase 4 Detection |
| A-b-1 | Output presentation depends on agent guesswork rather than skill guidance | SKILL.md Design — Agent behavior |
| A-b-2 | Configurable parameters invisible to users in conversation | SKILL.md Design — Config section |
| A-b-6 | Feature discovery is fully passive; users never learn unrequested capabilities | SKILL.md Design — Feature discovery |

## Goal

Add a `--universal` generation mode that produces skills with no agent-platform
binding inside the generated package and no per-platform install assumptions in
the skill itself.

The generated skill should be usable on every platform the same way:

```bash
python3 scripts/pipeline.py --input <input> --output <output>
```

The mode should improve AI utilization by reducing noise, making capability
matching semantic instead of slash-command based, and providing a concrete I/O
contract that an agent can reason about before running the skill.

Universal output must remain compatible with GitHub-based CLI distribution:
`skillctl publish <skill-dir>` should be able to register a universal skill, and
`skillctl install <name>` should be able to retrieve it. The installed package
still exposes the same platform-neutral runtime command.

## Non-Goals

- Do not remove the existing default cross-platform distribution mode.
- Do not modify generated domain logic behavior.
- Do not remove validation or security scanning from the factory.
- Do not make universal mode the default in this change.
- Do not create platform-specific adapters for universal mode.
- Do not remove or weaken `skillctl`, the central registry, or the GitHub CLI
  distribution path.

## Recommended Approach

Use an opt-in reference-driven mode.

When the user includes `--universal` anywhere in the prompt, the factory strips
that flag before discovery and follows a new reference document:

```text
references/universal-standard.md
```

This keeps existing behavior stable while giving users a clean path for
platform-neutral skills.

## Core Boundary Principle

Universal mode draws a hard boundary between the generated skill and the skill
lifecycle system:

```text
skill = capability package
agent-skill-creator + skillctl = lifecycle manager
```

The generated skill contains only the files needed to understand, run, configure,
and verify the capability. It does not contain installation logic, platform
adapters, lifecycle automation, distribution commands, upgrade logic, or
modification workflows.

All distribution, installation, publishing, updating, migration, and
regeneration belongs to agent-skill-creator and its `skillctl` tooling. If a
platform-specific copy, symlink, conversion, registry write, or upgrade is
needed, that work happens outside the generated skill package.

This boundary is the main AI-utilization improvement: when an agent reads a
generated skill, every file it sees is about capability use, not package
lifecycle.

## Flag Behavior

The `--universal` flag is parsed during input triage, alongside existing flags
such as `--no-eval`, `--no-artifact`, and `--artifact <name>`.

Examples:

```text
/agent-skill-creator --universal Every week I clean exported reports
/agent-skill-creator --universal here
/agent-skill-creator --universal --no-eval Process these invoices
```

Interactions:

| Flags | Behavior |
|---|---|
| `--universal` | Generate the universal file layout and docs |
| `--universal --no-eval` | Generate universal output without eval files |
| `--universal --artifact <name>` | Keep artifact assessment behavior, but preserve universal docs and file layout |
| `--universal --mcp-audit` | Invalid combination; MCP audit produces feasibility reports, not a skill package |

## Phase Changes

### Phase 1: Discovery

No behavioral change. Discovery still reads user material, derives intent,
checks for existing data sources, and decides the data/API strategy.

### Phase 2: Tool vs Skill Decision

Before any eval or architecture work, the factory must classify what it is
building. This decision drives every subsequent phase.

**Tool** — a deterministic pipeline that runs a script when the user mentions a
specific task. The agent's role is caller: parse user input into command
parameters, run, read output, relay to user. No domain judgment required.

- Example: CSV dedup, SQL formatter, JSON validator
- Agent role: caller
- Output: thin SKILL.md with command reference, no conversation guidance

**Skill** — a domain-aware plan that embodies judgment rules, edge-case
heuristics, default interpretations, and presentation conventions. The agent's
role is domain doer: interpret user intent, decide which analysis path to take,
surface diagnostics, guide the conversation.

- Example: CRM report generator with data quality checks, compliance reviewer
- Agent role: domain doer
- Output: full SKILL.md with agent behavior mapping, diagnostics, config
  transparency, and feature discovery

The factory previously treated all created outputs as "skill" but produced the
"tool" template (command reference only), leaving the agent to guess the domain
intent. Universal mode should produce the correct template for each class.

Rules:

- Classify during Phase 2 after intent derivation is complete.
- If no domain interpretation required beyond "parse params → execute → return
  output", classify as tool.
- If the creator material includes judgment rules, multiple analysis paths,
  heuristics, or domain conventions, classify as skill.
- Use the corresponding template set for SKILL.md and AGENTS.md in Phase 5.

### Phase 2: Design

Universal mode keeps binary eval design but restricts eval criteria to
deterministic command checks.

Both tool and skill use command-only eval criteria, but skill evaluation adds
golden cases that test domain judgment (e.g. correctly flagging suspicious
data vs. silent passthrough).

Rules:

- Generate `command` criteria only.
- Do not generate `llm-judge` criteria.
- Do not generate a `judge` block.
- Keep the golden-case strategy: at least three golden cases, with one
  `split: "test"` holdout unless `--no-eval` is active.
- For skill-class generated outputs, at least one golden case should exercise a
  chain of inputs that tests domain judgment — not just structural correctness.

Rationale: command checks are platform-neutral. Embedded judge backends,
subscription-based grading, API-key fallbacks, and model-comparison flows create
runtime assumptions that do not belong in universal output.

### Phase 3: Architecture

Use the universal directory layout from `references/universal-standard.md`.

The simple skill layout is:

```text
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

Removed from universal output:

- `.claude-plugin/`
- platform marketplace files
- `install.sh`
- shell bootstrap wrappers
- PowerShell bootstrap wrappers
- platform detection logic
- auto-install logic
- publish/update/search commands
- `scripts/evolve.py`
- staleness, dependency-health, schema-drift, and skill-document scripts
- platform-specific activation examples

Not removed:

- repository-level `skillctl`
- repository-level `VERSION.md`
- central registry publishing/installing through GitHub
- generated skill metadata needed by `skillctl`, including `name`,
  `description`, and `metadata.version`
- generated skill runtime requirements, such as `requirements.txt`

Complex suites use the same principle: each component keeps only capability
docs, executable logic, tests/evals, assets, and dependency declarations.

### Phase 4: Detection

Universal mode uses semantic capability matching instead of platform trigger
syntax, and covers fuzzy/real-world user expressions beyond the skill author's
own phrasing.

Rules:

- The `description` frontmatter is the primary activation signal.
- Do not write slash-command trigger grammar into generated docs.
- Do not mention platform names as part of activation.
- Generate natural-language activation examples that cover:
  * explicit user requests (task name)
  * implicit requests (user shows data without saying what to do)
  * domain verbs without domain nouns, in the user's primary language
  * English and the user's primary language as appropriate
- For skill-class outputs, also generate a transparency cue: a one-sentence
  activation alert that the agent can relay to the user so the user knows a
  skill was invoked.

Tool example:

```text
Use this tool when the user asks to deduplicate a CSV file, remove exact
duplicate rows, or clean up a messy export. If the user is not sure what
kind of dedup they need, this tool validates exact-match deduplication only.
```

Skill example:

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

### Phase 5: Implementation

Universal mode replaces the default file list with the universal file list.
Tool and skill outputs share the same file layout but differ in section
coverage. All normal quality requirements still apply: complete code, no
placeholders, type hints where useful, focused error handling, validation,
security scanning, and pipeline checks. All
normal quality requirements still apply: complete code, no placeholders, type
hints where useful, focused error handling, validation, security scanning, and
pipeline checks.

The implementation rule is strict: if a generated file is primarily about
installing, publishing, updating, modifying, migrating, adapting to an agent
platform, or managing skill lifecycle state, it does not belong inside the
generated universal skill.

Generated files follow these roles:

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

Generated files must not include lifecycle managers. Those remain in
agent-skill-creator:

| Lifecycle concern | Owner |
|---|---|
| Search/discovery | `skillctl` |
| Publishing | `skillctl publish` |
| Installation | `skillctl install` or creator-side copy logic |
| Updating | `skillctl update` |
| Migration/regeneration | agent-skill-creator |
| Platform placement | creator/installer side |
| Skill modification | agent-skill-creator regenerates or migrates the package |

Additional rules for both tool and skill:

- **Domain knowledge as data.** If the skill needs column-name aliases,
  threshold values, default behaviors, type mappings, or language-specific
  translations, store them as a structured data file under `assets/` (JSON or
  YAML), not as hardcoded constants in Python scripts. Processing code reads
  from the data file. This makes knowledge independently verifiable,
  extendable, and auditable without touching code.

- **Structured diagnostic output on failure.** The pipeline must produce
  structured diagnostic information when it cannot process input, not silent
  defaults or empty JSON. At minimum the diagnostic must contain: which input
  data was unrecognized, what the closest valid alternative was, and what the
  agent or user can do to fix it. This allows the agent to relay useful
  guidance rather than guessing why the output is empty.

- **One entry point, but parameter derivation rules in prose.** The happy-path
  command stays. For skill-class outputs, the SKILL.md also includes a
  structured parameter derivation section that tells the agent where each
  command parameter should come from — user input, data inspection, or default
  — and how to resolve ambiguity.

## AGENTS.md Design

In universal mode, AGENTS.md should be compact and intentionally
non-duplicative. It is a dispatch card, not the full manual.

For tool-class outputs, the tool sections below suffice. For skill-class
outputs, add the activation alert sentence from Phase 4 and the output
presentation rule (one sentence about what the agent should lead with).

Required shape:

````markdown
# <skill-name>

<one-line summary>

## What it does

<2 sentences. Describe the high-level capability for dispatch.>
<For skill-class: one sentence activation alert.>

## Output

<For skill-class: one sentence on how to present results.
"Lead with the summary figures, then offer to drill into any dimension.">

## How to run it

```bash
python3 scripts/pipeline.py --input <input> --output <output>
```

## Full spec

See [SKILL.md](./SKILL.md) for input/output contracts, configuration, known
limits, and examples.
````

Rules:

- Keep under 25 lines.
- Do not duplicate the full SKILL.md contract.
- Do not include platform names.
- Do not include slash-command activation examples.
- Include exactly one happy-path command.

## SKILL.md Design

In universal mode, SKILL.md is the complete operating contract. Tool-class
outputs use a subset of these sections; skill-class outputs use all sections.

Required frontmatter:

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

Required body sections:

For tool-class outputs:

1. `# <skill-name>`
2. `## What this skill does`
3. `## When to use it`
4. `## Input`
5. `## Output`
6. `## How to run it`
7. `## Known limits`

For skill-class outputs:

1. `# <skill-name>`
2. `## What this skill does`
3. `## When to use it`
4. `## Input`
5. `## Output`
6. `## How to run it`
7. `## Config` if configurable
8. `## Known limits`
9. `## Anti-goals`
10. `## Agent behavior`
11. `## Diagnostics`
12. `## Feature discovery` if the skill has multiple dimensions

### Agent behavior section (skill-class only)

Constrains the agent's output presentation so the user gets a consistent
experience regardless of platform. Required content:

- **Presentation order:** which metric to lead with, which to group together,
  when to use a table vs. a paragraph vs. a list.
- **Config transparency:** which config parameters exist, what their defaults
  are, and under what circumstances the agent should offer to adjust them
  ("If the outlier count seems high, suggest increasing the threshold").
- **Follow-up prompts:** what the agent should say after presenting results to
  invite deeper exploration ("I can break this down by product, region, or
  sales rep — want to dive into any of those?").

Example:

```text
Start with the grand total and data quality summary. Then offer to show the
top region, product, or sales rep. Use a table for per-category breakdowns
with more than three items; use inline text for three or fewer.
If outliers are detected, mention the count and suggest the user adjust the
sensitivity threshold.
```

### Diagnostics section (skill-class only)

Documents what structured diagnostic output the pipeline produces on failure
and how the agent should surface it. Required content:

- **Diagnostic schema:** what fields the diagnostic JSON contains
- **Agent guidance:** what to tell the user when a specific diagnostic fires
- **Resolution hints:** what the user can do to fix the issue

Example:

```text
When a column cannot be detected, the pipeline exits with a structured error:
{
  "unrecognized_columns": ["区域", "金额"],
  "closest_known_roles": {
    "区域": ["region", "area", "territory"],
    "金额": ["amount", "revenue", "value"]
  },
  "action": "Add '区域' to assets/column_aliases.json"
}
Surfacing guidance: tell the user the column wasn't recognized, show the
closest match, and explain what the fix looks like.
```

### Feature discovery section (skill-class, multi-dimension only)

Lightweight hints the agent adds to its response after completing the user's
request. This lets users discover capabilities they didn't know to ask for.

Content: for each dimension or analysis mode the skill supports, one sentence
summarizing what it reveals and when it is useful. The agent should add one
of these hints at the end of its response, varying which one across
interactions so the user gradually builds a mental model of the skill.

Example:

```text
Related capabilities:
- Breakdown by region — see which area contributed the most revenue
- Breakdown by product — identify top and bottom performers
- Data quality report — detect duplicates, outliers, and missing values
```

Rules:

- Keep under 150 lines.
- Do not include a `Trigger` section.
- Do not use slash-command invocation examples.
- Do not mention agent platforms.
- Include one concrete output example with realistic data.
- Prefer JSON examples over prose-only output descriptions.
- For skill-class outputs, include Agent behavior, Diagnostics, and Feature
  discovery sections.

The output example is mandatory because it lets an agent infer the output shape
before running the skill.

## Eval Harness Design

Universal mode should use a simplified `scripts/run_evals.py`.

Kept:

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

Removed:

- `--judge`
- `--model`
- LLM judge backends
- API-key judge fallback
- subscription-runtime judge fallback
- canary checks
- model comparison tables
- usage sidecars
- EVOLUTION.md writes

Expected size: under 500 lines.

Eval spec shape:

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

## Distribution, Installation, And Modification Model

Universal skills do not ship their own per-platform installer, updater, or
modifier.

A universal skill is a directory with a stable runtime contract. Copying or
cloning that directory is sufficient for direct use. Every platform can use it
by reading the files and running the same command.

The GitHub-backed `skillctl` distribution path remains supported and is the
preferred discovery/install/update path when a registry is available:

```bash
python3 scripts/skillctl/__main__.py search <query>
python3 scripts/skillctl/__main__.py install <skill-name>
python3 scripts/skillctl/__main__.py update <skill-name>
python3 scripts/skillctl/__main__.py publish <skill-dir>
```

`skillctl` may copy the skill into platform-specific locations as an external
installer concern. That does not make the generated skill platform-bound,
because the skill package itself does not contain platform adapters, shell
wrappers, marketplace manifests, or platform-specific activation syntax.

Skill modification also happens outside the generated package. The user returns
to agent-skill-creator with new materials, changed requirements, or an existing
skill directory. The creator then regenerates, migrates, or rewrites the skill
package. A universal generated skill should not ship `evolve.py`, self-modifying
scripts, or long-running maintenance loops.

README.md should be brief:

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

## Validation

Universal mode still uses the factory's normal validation and security checks.
Additional validation for skill-class outputs:

- SKILL.md has `## Agent behavior` section
- SKILL.md has `## Diagnostics` section
- SKILL.md's `## Output` includes a concrete JSON example
- Column aliases, thresholds, and domain knowledge are stored in `assets/` as
  data files, not hardcoded in Python

Validation should confirm:

- `SKILL.md` has valid frontmatter.
- `metadata.version` exists so `skillctl publish` can tag and index the skill.
- `SKILL.md` has no `Trigger` section.
- `SKILL.md` includes an output example.
- `AGENTS.md` stays under 25 lines.
- no `.claude-plugin/` directory exists.
- no `install.sh` exists.
- no shell/PowerShell bootstrap wrappers exist at the skill root.
- no publish/install/update/search CLI files exist inside the generated skill.
- no self-modification or lifecycle-maintenance scripts exist inside the
  generated skill.
- no generated eval criterion has `type: "llm-judge"`.
- no eval spec has a `judge` block.
- `scripts/pipeline.py` exists for deterministic multi-step skills.
- `skillctl publish <skill-dir> --dry-run` can validate a universal skill
  without requiring platform-specific files.

Security scan remains unchanged.

## Implementation Files To Update

Add:

- `references/universal-standard.md`

Modify:

- `SKILL.md`
- `references/architecture-guide.md`
- `references/pipeline-phases.md`
- `references/phase2-eval-assessment.md`
- `scripts/skillctl/publish.py` if its preflight currently assumes default-mode
  files such as `install.sh`, `.claude-plugin/`, or slash-command triggers.
- `scripts/tests/test_skillctl_publish.py` to cover publishing a universal
  skill.

The implementation plan should confirm whether `skillctl` already accepts the
universal layout. If it does, no `skillctl` code change is needed. If not, update
publish preflight to validate the universal contract instead of default-mode
platform artifacts.

## Acceptance Criteria

The design is complete when:

1. The factory documents `--universal` as an opt-in generation mode.
2. Universal mode has one authoritative reference file.
3. AGENTS.md and SKILL.md have distinct responsibilities.
4. Generated universal skills contain no platform-specific artifacts.
5. Generated universal skills remain usable across platforms via the same
   Python entry point.
6. Eval coverage remains available through command-only regression checks.
7. Universal skills can be published and installed through `skillctl` without
   adding platform-specific files to the generated skill.
8. Skill modification, migration, upgrade, and distribution are owned by
   agent-skill-creator and `skillctl`, not by generated skill packages.
9. The factory classifies each generated output as tool or skill during Phase 2
   and uses the correct template set.
10. Generated skill-class outputs include an Agent behavior section that
   constrains presentation order, config transparency, and follow-up prompts.
11. Generated skill-class outputs include a Diagnostics section with
   structured failure schema and agent guidance.
12. Generated skill-class outputs include a Feature discovery section for
   skills with multiple dimensions.
13. Domain knowledge is always stored as data files, never hardcoded in
   processing scripts.
14. Existing default generation behavior is unchanged.

## Risks

The Tool vs Skill classification is a binary decision the factory LLM must
make during Phase 2. If misclassified, the generated output will either
under-spec (skill cast as tool, missing domain guidance) or over-spec (tool
cast as skill, generating unnecessary conversation rules). The factory should
prefer under-spec when uncertain: too little guidance is easier for an agent
to compensate for than incorrect guidance.

Universal mode trades away per-skill turnkey platform installers. This is
intentional, but the README must make both direct use and registry-based
`skillctl install` obvious.

Removing embedded LLM judge support from universal evals reduces semantic
grading power for some writing-heavy skills. For those cases, command checks can
still call external graders explicitly, but the universal harness should not
ship with a platform-specific judge backend.

Agent behavior, Diagnostics, and Feature discovery sections in SKILL.md require
the factory to generate structured guidance for the agent's presentation layer.
This is not a simple prose exercise: parameters, failure modes, and related
capabilities must be extracted during Phase 1-2 design and encoded during
Phase 5. The factory must treat these as first-class outputs, not optional
niceties.

## Open Questions For Implementation

- Should universal mode be exposed only as a prompt flag, or also as a config
  value in future releases?
- Should `scripts/validate.py` gain explicit universal-mode checks, or should
  the generator self-police the universal file layout first?
- Should the simplified eval harness be stored as a template file or generated
  inline from instructions?
