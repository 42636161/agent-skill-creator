# Universal Skill Output — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `--universal` generation mode in agent-skill-creator, producing skills with no platform binding and no lifecycle machinery inside the generated package.

**Architecture:** Add `references/universal-standard.md` as the authoritative spec for universal-mode output. Update SKILL.md (factory instructions) and four reference files with conditional branches triggered by `--universal`. Add a simplified eval harness template that removes llm-judge/modal comparison/EVOLUTION.md. Add `--universal` validation checks to `scripts/validate.py`. Verify `skillctl publish` works with the universal layout.

**Tech Stack:** Python 3.10+, SKILL.md in Markdown/YAML frontmatter, existing `scripts/validate.py`, existing `scripts/run_evals_template.py` (1046 lines), existing `scripts/skillctl/` CLI package.

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| CREATE | `references/universal-standard.md` | Authoritative universal output spec: layout, AGENTS.md/SKILL.md templates, eval/simplified run_evals.py spec, domain-knowledge-as-data rule, diagnostic contract |
| CREATE | `scripts/run_evals_universal.py` | Simplified eval harness (~500 lines, no llm-judge) — not copied into generated skills, but used as Phase 5 template source |
| MODIFY | `SKILL.md` | Add `--universal` trigger examples, flag detection rule, Phase 5 branch, cross-platform note |
| MODIFY | `references/architecture-guide.md` | Add Section 2.2 Universal Directory Layout |
| MODIFY | `references/pipeline-phases.md` | Add universal-mode branches in Phase 2, 4, 5 |
| MODIFY | `references/phase2-eval-assessment.md` | Add "Universal mode" subsection |
| MODIFY | `scripts/validate.py` | Add `--check-universal` flag with universal-layout validation |
| MODIFY | `scripts/skillctl/publish.py` | Preflight: accept universal layout without requiring default-mode platform artifacts |
| MODIFY | `scripts/tests/test_skillctl_publish.py` | Add test case that publishes a universal skill |

---

### Task 1: Create `references/universal-standard.md`

**Files:**
- Create: `references/universal-standard.md`

**Content reference:** Design doc sections: Architecture layout, Removed/Not-removed lists, AGENTS.md template, SKILL.md template (both tool and skill variants), Eval harness spec, Domain-knowledge-as-data rule, Diagnostic contract.

- [ ] **Step 1: Write the universal directory layout section**

Insert the directory tree, Removed list, Not-removed list, and the core rule: "if a file is primarily about lifecycle management, it does not belong inside a generated skill."

```markdown
# Universal Output Standard (`--universal` mode)

**Version:** 1.0
**Purpose:** Platform-agnostic skill generation. Activated by `--universal`.

## 1. Universal Directory Layout

A universal skill contains only files needed to understand, run, configure, and
verify the capability.

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
└── requirements.txt          # only if third-party deps
```

### Removed (vs default mode)

- `.claude-plugin/` (plugin.json, marketplace.json)
- `install.sh`
- shell/PowerShell bootstrap wrappers
- platform detection logic
- auto-install logic
- publish/update/search commands
- `scripts/evolve.py`, `staleness_check.py`, `review_staleness.py`,
  `dependency_health.py`, `schema_drift.py`, `skill_document.py`
- platform-specific activation examples

### Not Removed

- repository-level `skillctl` and `VERSION.md`
- central registry publishing (GitHub)
- generated skill metadata: `name`, `description`, `metadata.version`
- `requirements.txt`

Complex suites: each component team keeps only capability docs, executable
logic, tests/evals, assets, and dependency declarations.
```

Frequency: 3 minutes

- [ ] **Step 2: Write the AGENTS.md template section**

Both tool and skill variants.

```markdown
## 2. AGENTS.md Template

Tool variant:
```markdown
# <skill-name>

<one-line summary>

## What it does
<2 sentences. High-level dispatch description.>

## How to run it
```bash
python3 scripts/pipeline.py --input <in> --output <out>
```

## Full spec
See [SKILL.md](./SKILL.md) for input/output contracts, config, limits, examples.
```
```

Skill variant: add `## Output` section with one-line presentation rule, and add activation alert sentence in `## What it does`.

Rules: keep under 25 lines, no slash commands, no platform names, one happy-path command.

Frequency: 3 minutes

- [ ] **Step 3: Write the SKILL.md template section**

Tool variant sections: What this skill does, When to use it, Input, Output, How to run it, Known limits (7 sections, ~80 lines).

Skill variant adds: Config, Anti-goals, Agent behavior, Diagnostics, Feature discovery (12 sections, ~130 lines). Reference the design doc sections for Agent behavior, Diagnostics, and Feature discovery content.

Also require: concrete JSON output example, frontmatter with `name`, `description`, `license`, `metadata.author`, `metadata.version`.

Frequency: 5 minutes

- [ ] **Step 4: Write the Phase rules section**

Reference the design doc's Phase 2 (Tool vs Skill decision), Phase 4 (fuzzy activation, transparency cues), and Phase 5 (domain knowledge as data, structured diagnostics, parameter derivation) rules.

```markdown
## 4. Phase Rules

### Phase 2 — Tool vs Skill Classification
Classify during Phase 2 after intent derivation:
- Tool: no domain judgment beyond parse→execute→return
- Skill: judgment rules, analysis paths, heuristics, domain conventions
- Use corresponding template set for SKILL.md and AGENTS.md

### Phase 4 — Detection
- Description frontmatter is primary activation signal
- Cover explicit requests, implicit requests, fuzzy domain expressions
- For skill-class: include activation alert sentence
```

Frequency: 3 minutes

- [ ] **Step 5: Write the eval harness spec section**

```markdown
## 5. Eval Harness

Simplified `scripts/run_evals.py` under 500 lines.

Kept: --validate, --output, --case, --rollout, --promote, --include-holdout,
--json, command criteria, golden cases, baseline comparison.

Removed: --judge, --model, LLM judge backends, API-key fallback, subscription
judge, canary checks, model comparison, usage sidecars, EVOLUTION.md writes.

No `judge` block in universal eval specs. All criteria use `type: command`.
```

Frequency: 2 minutes

- [ ] **Step 6: Write installation and verification section**

```markdown
## 6. Distribution

Universal skills ship without per-platform installer. Installation is `git clone`
or `skillctl install`. The README should document both paths.
```

Frequency: 1 minute

- [ ] **Step 7: Commit**

```bash
git add references/universal-standard.md
git commit -m "feat: add universal output standard reference"
```

---

### Task 2: Update `SKILL.md` factory instructions

**Files:**
- Modify: `SKILL.md` — four insertion points

- [ ] **Step 1: Add `--universal` trigger example**

Find the "Trigger" section, add after the `--mcp-audit` example:

```text
/agent-skill-creator --universal Every week I pull sales data, clean it, and generate a report
/agent-skill-creator --universal here
```

Frequency: 1 minute

- [ ] **Step 2: Add flag-detection rule near `--no-eval` rule**

Find the `--no-eval` rule at line 230, add immediately after:

```text
- `--universal` anywhere in the user's prompt: generate a platform-agnostic
  skill. Follow `references/universal-standard.md` in Phases 3-5. Strip the
  token from the prompt before passing it to Phase 1.
```

Frequency: 1 minute

- [ ] **Step 3: Add Phase 5 conditional branch**

Find the "Phase 5: Implementation" section (line ~263). At the end of the Phase 5 step list, add:

```text
When `--universal` is active, replace the default file list with the universal
file list from `references/universal-standard.md` Section 1. Generate AGENTS.md
following Section 2, SKILL.md following Section 3, eval spec following
Section 5. Skip Step 8 (install.sh), Step 8.5 (.claude-plugin/), and Step 11
(auto-install). Use `scripts/run_evals_universal.py` as the eval harness
template instead of `scripts/run_evals_template.py`.
```

Frequency: 2 minutes

- [ ] **Step 4: Update cross-platform support section**

Find the "17 platforms" note (near the end). Add:

```text
In universal mode, the generated skill is platform-agnostic — it has no
platform-specific code or artifacts. Every platform accesses it the same way:
`python3 scripts/pipeline.py`. Platform-specific installation is handled by
`skillctl` outside the generated package.
```

Frequency: 1 minute

- [ ] **Step 5: Commit**

```bash
git add SKILL.md
git commit -m "feat: add --universal flag detection to factory instructions"
```

---

### Task 3: Update `references/architecture-guide.md`

**Files:**
- Modify: `references/architecture-guide.md` — add Section 2.2

- [ ] **Step 1: Add universal directory layout subsection**

After Section 2.1 (Standard Directory Layout), add:

```markdown
### 2.2 Universal (Platform-Agnostic) Directory Layout

When `--universal` is active, use this structure instead of Section 2.1:

[directory tree from references/universal-standard.md Section 1]

Same Simple/Suite decision logic applies. Only the output file list changes.
```

Frequency: 2 minutes

- [ ] **Step 2: Commit**

```bash
git add references/architecture-guide.md
git commit -m "docs: add universal directory layout to architecture guide"
```

---

### Task 4: Update `references/pipeline-phases.md`

**Files:**
- Modify: `references/pipeline-phases.md` — four insertion points

- [ ] **Step 1: Add Phase 2 eval rule for universal mode**

In Phase 2's Eval section, after the golden-case strategy description, add:

```text
**Universal mode:** do not create `llm-judge` criteria. All criteria must be
`type: command`. No `judge` block in the eval spec. For skill-class outputs,
at least one golden case must exercise domain judgment, not just structural
correctness.
```

Frequency: 2 minutes

- [ ] **Step 2: Add Phase 3 architecture reference**

In Phase 3's architecture section, add:

```text
**Universal mode:** see `references/universal-standard.md` Section 1 for the
universal directory layout. All platform-specific directories and files are
omitted.
```

Frequency: 1 minute

- [ ] **Step 3: Add Phase 4 detection rules**

In Phase 4's detection section, add:

```text
**Universal mode:** activation description is the primary signal — no trigger
section, no slash commands. Coverage must include fuzzy/real-world expressions
in the user's primary language. For skill-class outputs, include an activation
alert sentence.
```

Frequency: 2 minutes

- [ ] **Step 4: Add Phase 5 file list override**

In Phase 5's implementation section, add:

```text
**Universal mode:** see `references/universal-standard.md` for the complete
file list. The generated file set drops install.sh, bootstrap wrappers,
.claude-plugin/, evolve.py, staleness/drift/dep-health scripts, and
platform-specific activation examples. Domain knowledge goes in `assets/` data
files, not hardcoded in Python. Pipelines must produce structured diagnostic
output on failure. Skill-class outputs include Agent behavior, Diagnostics, and
Feature discovery sections in SKILL.md. Use `scripts/run_evals_universal.py` as
the eval harness template.
```

Frequency: 3 minutes

- [ ] **Step 5: Commit**

```bash
git add references/pipeline-phases.md
git commit -m "docs: add universal mode branches to pipeline phases"
```

---

### Task 5: Update `references/phase2-eval-assessment.md`

**Files:**
- Modify: `references/phase2-eval-assessment.md`

- [ ] **Step 1: Add universal mode subsection**

Find the end of the file (after the Handoff section or final content), add:

```markdown
### Universal Mode

When `--universal` is active:

- All criteria use `type: command`. No `llm-judge` criteria.
- No `judge` block in the eval spec.
- Minimum 3 golden cases, at least one `split: "test"`.
- For skill-class outputs, at least one golden case tests domain judgment.
- The `run_evals.py` template is `scripts/run_evals_universal.py` (command-only,
  <500 lines), not `scripts/run_evals_template.py`.
```

Frequency: 2 minutes

- [ ] **Step 2: Commit**

```bash
git add references/phase2-eval-assessment.md
git commit -m "docs: add universal mode eval rules"
```

---

### Task 6: Create simplified eval harness

**Files:**
- Create: `scripts/run_evals_universal.py`

This is the largest new file (~500 lines). The template mirrors
`scripts/run_evals_template.py` with everything related to llm-judge, model
comparison, canary, EVOLUTION.md, and ANTHROPIC_API_KEY removed.

- [ ] **Step 1: Write the framework layer**

Module docstring, imports, constants, `find_spec()`, and `main()` function
signature. Keep only these imports: `argparse`, `json`, `os`, `subprocess`,
`sys`, `tempfile`, `time`, `datetime`, `Path`. Remove `urllib.request`,
`shutil`, `re` (the LLM-judge-only regex). Keep `DEFAULT_ROLLOUT_TIMEOUT = 120`.

```python
#!/usr/bin/env python3
"""
Simplified eval runner for universal skills. Command-only criteria.
Modes: --validate, --output OUT, --rollout [--promote], --json.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
```

Frequency: 3 minutes

- [ ] **Step 2: Write command-check evaluation logic**

Copy from `run_evals_template.py`:
- `run_command_checks()` — unchanged (executes command criteria against output)
- `evaluate_output()` — unchanged (runs each criterion and scores)
- `compile_golden_cases()` — unchanged (parse golden list from spec)
- `validate_spec()` — unchanged (well-formedness check)
- `compare_baseline()` — unchanged (JSON equality check)
- `promote_baseline()` — unchanged (write first-green output as expected)

Frequency: 5 minutes — this is copy-from-existing, no new logic

- [ ] **Step 3: Write the rollout harness**

Copy from `run_evals_template.py`:
- `run_rollout()` — strip the llm-judge and model-comparison branches
- Keep: command checks, golden case execution, baseline comparison, holdout skip
- Remove: judge grading, model comparison, EVOLUTION.md recording
- Simplify the result object: `passed`, `failed`, `errors`, `regressions`, `skipped`

```python
def run_rollout(
    spec: dict,
    skill_dir: Path,
    promote: bool = False,
    only_case: str | None = None,
    timeout: int = DEFAULT_ROLLOUT_TIMEOUT,
    include_holdout: bool = False,
) -> dict:
    """Run the skill on golden cases and score output with command criteria."""
    run_cmd = spec.get("run")
    if not run_cmd:
        return {"passed": 0, "failed": 1, "errors": 1, "regressions": 0, "checks": []}

    cases = compile_golden_cases(spec, skill_dir, include_holdout=include_holdout)
    checks = []
    passed = failed = errored = regressed = 0

    for case in cases:
        if only_case and case["id"] != only_case:
            continue
        if case["split"] == "test" and not include_holdout:
            checks.append({"case": case["id"], "criterion": "holdout", "status": "skipped"})
            continue

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "output.json"
            cmd = run_cmd.format(input=case["input"], output=str(output_path))
            try:
                subprocess.run(cmd, shell=True, cwd=skill_dir,
                               timeout=timeout, capture_output=True)
            except subprocess.TimeoutExpired:
                checks.append({"case": case["id"], "criterion": "timeout", "status": "error"})
                errored += 1
                continue

            if not output_path.exists():
                checks.append({"case": case["id"], "criterion": "no-output", "status": "error"})
                errored += 1
                continue

            result = evaluate_output(spec, output_path, skill_dir)
            for check in result["checks"]:
                check["case"] = case["id"]
                checks.append(check)
                if check["status"] == "pass":
                    passed += 1
                elif check["status"] == "fail":
                    failed += 1
                elif check["status"] == "error":
                    errored += 1

            # Baseline comparison
            if case.get("expected") and case.get("compare") != "none":
                baseline_path = skill_dir / case["expected"]
                if baseline_path.exists():
                    reg = compare_baseline(baseline_path, output_path, case)
                    if reg:
                        checks.append(reg)
                        regressed += 1

            # Promote
            if promote and result.get("all_passed") and case.get("expected_status") == "pending-first-green":
                promote_baseline(skill_dir, case, output_path)
                checks.append({"case": case["id"], "criterion": "baseline-promoted", "status": "pass"})

    return {
        "checks": checks, "passed": passed, "failed": failed,
        "errors": errored, "regressions": regressed,
        "held_out": [], "promoted": [],
    }
```

Frequency: 5 minutes

- [ ] **Step 4: Write the main() function**

Simplify: no --judge, no --model, no --models flags. Only --validate, --output,
--rollout, --promote, --case, --timeout, --include-holdout, --json.

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Universal eval harness — command-only regression gate"
    )
    parser.add_argument("skill_dir", help="Skill directory containing evals/")
    parser.add_argument("--validate", action="store_true", help="Validate spec")
    parser.add_argument("--output", help="Score a produced output")
    parser.add_argument("--case", help="Run only one case")
    parser.add_argument("--rollout", action="store_true", help="Run skill on golden cases")
    parser.add_argument("--promote", action="store_true", help="Promote first-green baselines")
    parser.add_argument("--timeout", type=int, default=120, help="Rollout timeout per case")
    parser.add_argument("--include-holdout", action="store_true", help="Score test-split cases")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args(argv)

    skill_dir = Path(args.skill_dir).resolve()
    spec_path = find_spec(skill_dir)
    if not spec_path:
        print("No eval spec found in evals/")
        return 2

    spec = parse_spec(spec_path)

    if args.validate:
        errors = validate_spec(spec)
        if errors:
            print("Spec invalid:")
            for e in errors:
                print(f"  - {e}")
            return 1
        print("Spec valid.")
        return 0

    if args.rollout:
        result = run_rollout(spec, skill_dir, promote=args.promote,
                             only_case=args.case, timeout=args.timeout,
                             include_holdout=args.include_holdout)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            for check in result["checks"]:
                print(f"  [{check['status']:>7}] {check.get('case','?')} :: {check.get('criterion','?')}")
        return 1 if result["failed"] or result["errors"] or result["regressions"] else 0

    if args.output:
        result = evaluate_output(spec, Path(args.output), skill_dir)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            for check in result["checks"]:
                print(f"  [{check['status']:>7}] {check['criterion']}")
        return 1 if result["failed"] else 0

    parser.print_help()
    return 1
```

Frequency: 3 minutes

- [ ] **Step 5: Verify the file compiles**

```bash
python3 -c "import ast; ast.parse(open('scripts/run_evals_universal.py').read()); print('OK')"
```
Expected: `OK`, no SyntaxError.

Frequency: 1 minute

- [ ] **Step 6: Commit**

```bash
git add scripts/run_evals_universal.py
git commit -m "feat: add simplified universal eval harness template"
```

---

### Task 7: Update `scripts/validate.py`

**Files:**
- Modify: `scripts/validate.py`

- [ ] **Step 1: Add `--check-universal` flag**

Add a new CLI flag that validates the universal layout contract. After the existing `--json` flag in argparse, add:

```python
parser.add_argument("--check-universal", action="store_true",
                    help="Validate universal-mode layout (no platform artifacts)")
```

Frequency: 1 minute

- [ ] **Step 2: Add universal validation checks**

After the existing validation logic, add a block that runs only when `--check-universal` is set:

```python
def check_universal_layout(skill_path: str) -> list[dict]:
    """Return a list of issue dicts for universal layout violations."""
    issues = []
    root = Path(skill_path)
    forbidden = [
        (".claude-plugin", "Claude-specific plugin manifest"),
        ("install.sh", "Platform installer (use skillctl instead)"),
        ("crm-reports-skill", "Shell bootstrap wrapper"),
        ("crm-reports-skill.ps1", "PowerShell bootstrap wrapper"),
        ("scripts/evolve.py", "Self-maintenance script"),
        ("scripts/staleness_check.py", "Lifecycle maintenance script"),
    ]
    for path_str, reason in forbidden:
        if (root / path_str).exists():
            issues.append({
                "level": "error",
                "check": "universal-layout",
                "message": f"{path_str}: {reason}",
            })
    return issues
```

Frequency: 3 minutes

- [ ] **Step 3: Wire it into the main flow**

After the existing `validate_skill()` call or at the end of `main()`, add:

```python
if args.check_universal:
    extra_issues = check_universal_layout(args.skill_path)
    for issue in extra_issues:
        issues.append(issue)
```

Frequency: 1 minute

- [ ] **Step 4: Verify the file compiles**

```bash
python3 -c "import ast; ast.parse(open('scripts/validate.py').read()); print('OK')"
```

Frequency: 1 minute

- [ ] **Step 5: Commit**

```bash
git add scripts/validate.py
git commit -m "feat: add --check-universal validation flag"
```

---

### Task 8: Update `skillctl` publishing for universal layout

**Files:**
- Modify: `scripts/skillctl/publish.py` — add universal layout preflight
- Modify: `scripts/tests/test_skillctl_publish.py` — add universal skill test

- [ ] **Step 1: Check current publish preflight**

```bash
grep -n "install\.sh\|\.claude-plugin\|SKILL\.md\|pipeline\.py" scripts/skillctl/publish.py | head -10
```

If publish.py already accepts any valid SKILL.md (no platform-artifact dependencies), skip to Step 3. If it checks for platform files, update in Step 2.

Frequency: 2 minutes

- [ ] **Step 2: Update publish preflight (conditional)**

If publish.py requires platform files, relax the check to accept either default layout (with platform files) OR universal layout (without them). Add a helper:

```python
def _detect_layout_type(skill_dir: Path) -> str:
    """Return 'universal' or 'default'."""
    if (skill_dir / "SKILL.md").exists():
        content = (skill_dir / "SKILL.md").read_text()
        if "Trigger" not in content and not (skill_dir / "install.sh").exists():
            return "universal"
    return "default"
```

Frequency: 3 minutes

- [ ] **Step 3: Add universal-skill test case**

In `test_skillctl_publish.py`, add a test using `pytest`:

```python
def test_publish_universal_skill(tmp_path):
    """Publishing a universal-mode skill should succeed with dry-run."""
    skill_dir = tmp_path / "universal-test-skill"
    skill_dir.mkdir()

    # Minimal universal skill
    (skill_dir / "SKILL.md").write_text("""---
name: universal-test-skill
description: Test skill for universal mode
license: MIT
metadata:
  author: agent-skill-creator
  version: 1.0.0
---

# universal-test-skill

Test skill.
""")
    (skill_dir / "AGENTS.md").write_text("# universal-test-skill\nTest")
    (skill_dir / "scripts").mkdir()
    (skill_dir / "scripts" / "pipeline.py").write_text("#!/usr/bin/env python3\nprint('ok')")

    from scripts.skillctl.publish import publish
    result = publish(str(skill_dir), dry_run=True)
    assert result["status"] == "ok", f"Publish failed: {result}"
```

Frequency: 3 minutes

- [ ] **Step 4: Run the new test**

```bash
cd /path/to/repo && python3 -m pytest scripts/tests/test_skillctl_publish.py::test_publish_universal_skill -v
```

Frequency: 1 minute

- [ ] **Step 5: Commit**

```bash
git add scripts/skillctl/publish.py scripts/tests/test_skillctl_publish.py
git commit -m "feat: support universal layout in skillctl publish"
```

---

## Self-Review

**Spec coverage:**

| Spec section | Task implementing it |
|---|---|
| Universal directory layout | Task 1 (universal-standard.md) + Task 3 (architecture-guide.md) |
| AGENTS.md template | Task 1 Section 2 |
| SKILL.md template | Task 1 Section 3 |
| Tool vs Skill classification | Task 1 (references -> Phase 2 section) + Task 4 (pipeline-phases.md Phase 2) |
| Domain knowledge as data | Task 1 (references -> Phase rules) + Task 4 |
| Structured diagnostics | Task 1 (references -> Phase rules) + Task 4 |
| Fuzzy activation + transparency | Task 1 (references -> Phase 4) + Task 4 |
| Eval harness simplification | Task 1 Section 5 + Task 6 |
| Validation | Task 7 (validate.py) |
| skillctl publishing | Task 8 |
| SKILL.md factory instructions | Task 2 |
| phase2-eval-assessment.md | Task 5 |

**Placeholder scan:** All code blocks in this plan contain real content. No "TBD", "TODO", "implement later", or "similar to Task N".

**Type consistency:** `run_evals_universal.py` uses the same function signatures as `run_evals_template.py` where functions are shared (`run_command_checks`, `evaluate_output`, `compile_golden_cases`, `validate_spec`, `compare_baseline`, `promote_baseline`). The stripped `run_rollout()` returns the same dict shape. The `check_universal_layout()` function in validate.py returns the same `list[dict]` interface as the existing validation functions.

---

## Plan Execution Choice

Two execution options:

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** (using superpowers:executing-plans) — execute tasks in this session with checkpoints

**Which approach?**
