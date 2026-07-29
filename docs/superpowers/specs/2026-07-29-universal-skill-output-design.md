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

### Phase 2: Design

Universal mode keeps binary eval design but restricts eval criteria to
deterministic command checks.

Rules:

- Generate `command` criteria only.
- Do not generate `llm-judge` criteria.
- Do not generate a `judge` block.
- Keep the golden-case strategy: at least three golden cases, with one
  `split: "test"` holdout unless `--no-eval` is active.

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
syntax.

Rules:

- The `description` frontmatter is the primary activation signal.
- Do not write slash-command trigger grammar into generated docs.
- Do not mention platform names as part of activation.
- Use natural-language "when to use this" examples that map to user intent.

Example style:

```text
Use this skill when the user asks to clean exported CRM data, produce a weekly
sales summary, group records by business dimensions, or verify data quality.
```

### Phase 5: Implementation

Universal mode replaces the default file list with the universal file list. All
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

## AGENTS.md Design

In universal mode, AGENTS.md should be compact and intentionally non-duplicative.
It is a dispatch card, not the full manual.

Required shape:

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

Rules:

- Keep under 25 lines.
- Do not duplicate the full SKILL.md contract.
- Do not include platform names.
- Do not include slash-command activation examples.
- Include exactly one happy-path command.

## SKILL.md Design

In universal mode, SKILL.md is the complete operating contract.

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

1. `# <skill-name>`
2. `## What this skill does`
3. `## When to use it`
4. `## Input`
5. `## Output`
6. `## How to run it`
7. `## Config` if configurable
8. `## Known limits`
9. `## Anti-goals`

Rules:

- Keep under 150 lines.
- Do not include a `Trigger` section.
- Do not use slash-command invocation examples.
- Do not mention agent platforms.
- Include one concrete output example.
- Prefer JSON examples over prose-only output descriptions.

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
9. Existing default generation behavior is unchanged.

## Risks

Universal mode trades away per-skill turnkey platform installers. This is
intentional, but the README must make both direct use and registry-based
`skillctl install` obvious.

Removing embedded LLM judge support from universal evals reduces semantic
grading power for some writing-heavy skills. For those cases, command checks can
still call external graders explicitly, but the universal harness should not
ship with a platform-specific judge backend.

Some platforms may prefer `AGENTS.md` as the primary instruction file. Keeping
AGENTS.md as a compact dispatch card means those platforms must follow the link
to SKILL.md for the full contract. This is acceptable because it prevents two
large, divergent specs from drifting apart.

## Open Questions For Implementation

- Should universal mode be exposed only as a prompt flag, or also as a config
  value in future releases?
- Should `scripts/validate.py` gain explicit universal-mode checks, or should
  the generator self-police the universal file layout first?
- Should the simplified eval harness be stored as a template file or generated
  inline from instructions?
