# Quality Framework — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the 8 quality improvements defined in EVALUATION.md v2.0 (P0/P1/P2), closing the gap between generated skills and reliable, AI-optimized, platform-agnostic capability packages.

**Architecture:** The work spans three layers:
- **Pipeline layer** (Phase 2 design decisions → Phase 5 code generation): DAG as code, contract.json emission, golden case boundary templates, defensive I/O templates, Agent Constraints in AGENTS.md
- **Validation layer** (validate.py): AST-level static analysis, contract-code consistency check, default CI wiring for `--check-universal`
- **Static analysis layer** (extended validate.py or standalone module): import chain, undefined references, type conflicts

**Tech Stack:** Python 3.10+ standard library (`ast`, `json`, `json-schema`), existing `scripts/validate.py` (extend), existing `scripts/pipeline_template.py` (modify for DAG), no new third-party dependencies.

---

## File Map

| Action | File | Responsibility | Task |
|---|---|---|---|
| CREATE | `references/contract-schema.json` | JSON Schema for contract.json — defines input assumptions, output fields, DAG, field semantics | T1 |
| MODIFY | `SKILL.md` | Add Phase 5 step for contract.json emission and CI integration | T1, T6 |
| MODIFY | `scripts/validate.py` | Add `--check-contract` module + `--check-ast` module + Agent Constraints check | T1, T3, T4, T8 |
| MODIFY | `scripts/pipeline_template.py` | Add DAG resolver + contract.json emission + defensive I/O | T1, T2, T5 |
| MODIFY | `references/pipeline-phases.md` | Document new Phase 5 substeps for contract.json, DAG, Constraints | T1, T2, T3 |
| MODIFY | `SKILL.md` (AGENTS.md template) | Add `## Agent Constraints` section generator | T3 |
| CREATE | `scripts/validate_ast.py` | (Optional extraction from validate.py) AST-level dead code + magic number checker | T4, T8 |
| MODIFY | `references/phase2-eval-assessment.md` | Add golden case boundary template rules | T7 |
| MODIFY | `.github/workflows/ci.yml` | Wire `--check-universal` into default CI as non-blocking lint | T6 |
| MODIFY | `scripts/tests/test_validate.py` | Add tests for each new check | T1, T3, T4, T6, T7, T8 |

---

### Task 1: Add `contract.json` to Phase 5 generation (P0-1)

**Effort:** 2-3 days  
**Dependencies:** none  
**Target status:** Phase 5 generates `contract.json` alongside all other files; `validate.py --check-contract` verifies code-contract consistency.

- [ ] **Step 1: Define contract schema**

Create `references/contract-schema.json` — the authoritative JSON Schema. The contract covers four sections:

| Section | Content | Example |
|---|---|---|
| `input` | Assumed encoding, column names + types, file path patterns | `{"encoding": "utf-8", "columns": {"name": "string", "amount": "float"}}` |
| `output` | Produced files, field schemas | `{"report": {"fields": {"region": "string", "total": "float"}}}` |
| `dag` | Step names, dependencies, execution order | `{"steps": [{"name": "clean", "depends_on": []}, {"name": "report", "depends_on": ["clean"]}]}` |
| `semantics` | Business rules per field | `{"is_active": {"meaning": "record valid + pipeline active", "allowed": [0, 1]}}` |

Key design rules:
- All fields optional in default mode; only `semantics` optional in universal mode
- Schema itself must be flat enough that agents can parse it without a schema resolver
- One JSON file, no nesting deeper than 3 levels

*Frequency: 1 hour*

- [ ] **Step 2: Modify Phase 5 to emit `contract.json`**

In `SKILL.md` (the factory instructions), add a new Phase 5 substep between the existing file-creation steps. The generated contract.json is populated from decisions already made in Phase 2 (design) and Phase 3 (architecture):

1. Input columns + types → Phase 2 design doc / Phase 3 `--columns` flag
2. Output fields → Phase 2 use cases
3. Step DAG → Phase 3 architecture (if missing, derive from SKILL.md step order)
4. Semantics → Phase 2 discussions (the agent has this context)

Target: the LLM writes contract.json during Phase 5, not a Python script. The SKILL.md instruction tells the model *what* to include and *where* to derive each section.

*Frequency: 2 hours*

- [ ] **Step 3: Add `--check-contract` to `validate.py`**

New function in `scripts/validate.py`:

```python
def check_contract(skill_path: str) -> list[dict]:
    """
    contract.json <-> code consistency checks:
    1. All declared output files exist under skill_path
    2. All declared columns appear in I/O code (grep column names in scripts/)
    3. Declared step count matches pipeline.py function count
    4. Input encoding matches any # -*- coding: -*- directives
    Returns list of issues: {"level": "warn"|"error", "check": "contract", "message": str}
    """
```

Wire as `validate.py --check-contract <skill-path>`. Emits warnings not errors (contract is informative, not gate-keeping). In universal mode, upgrade to errors for missing mandatory sections.

*Frequency: 3 hours*

- [ ] **Step 4: Add test**

Add to `scripts/tests/test_validate.py`:

```python
def test_check_contract_golden(tmp_path):
    """A contract that matches its code should pass with 0 errors."""
    ...

def test_check_contract_mismatch(tmp_path):
    """A contract declaring missing output should produce warnings."""
    ...
```

*Frequency: 1 hour*

---

### Task 2: DAG dependencies as code (P0-2)

**Effort:** 0.5 day  
**Dependencies:** none  
**Target status:** pipeline.py accepts only final goal (e.g. `--report`), engine auto-resolves step order. Existing `--clean --report` flags remain for backward compat but are documented as deprecated.

- [ ] **Step 1: Define DAG data structure in template**

Modify `scripts/pipeline_template.py` to add a minimal DAG resolver:

```python
# Dependency graph
STEPS = {
    "clean": [],
    "report": ["clean"],
}

def resolve_steps(target: str) -> list[str]:
    """Return ordered step list for target, including all dependencies."""
    visited = set()
    order = []

    def dfs(step):
        if step in visited:
            return
        visited.add(step)
        for dep in STEPS.get(step, []):
            dfs(dep)
        order.append(step)

    dfs(target)
    return order
```

*Frequency: 30 minutes*

- [ ] **Step 2: Update entry point**

Wrap `argparse` to accept `--report` (final goal) as the primary flag. If `--report` is given, call `resolve_steps("report")` to get the execution list, then run each step in order. Keep `--clean` flag for backward compat but set `deprecated=True` in help text.

*Frequency: 1 hour*

- [ ] **Step 3: Update SKILL.md template**

Replace the current step-invocation examples in the generated SKILL.md with the simplified interface:

```markdown
## How to run it

Generate a complete report (includes clean + process + report):
    python3 scripts/pipeline.py --report
```

*Frequency: 30 minutes*

- [ ] **Step 4: Update references/pipeline-phases.md**

Add note in Phase 3 (architecture) that the agent must define dependency graph alongside step functions.

*Frequency: 15 minutes*

---

### Task 3: Agent Constraints in AGENTS.md (P0-3)

**Effort:** 0.5 day  
**Dependencies:** none  
**Target status:** every generated AGENTS.md includes `## Agent Constraints` with ≥3 Do NOT / Must clauses; `validate.py --check-agents` verifies existence.

- [ ] **Step 1: Add Agent Constraints section to AGENTS.md template**

In `SKILL.md` (the factory instructions), add a rule to the AGENTS.md generation instruction:

```
After the existing sections, append:

## Agent Constraints

1. Must NOT <first constraint derived from Phase 2 business rules>
2. Must <second constraint derived from Phase 2 use cases>
3. Must NOT <third constraint derived from Phase 2 or Phase 4> 
4. Must <fourth constraint — at least one positive "Must" clause>
```

Instruction to the LLM: derive constraints from Phase 2 discussions, not from generic best practices. Each constraint must be verifiable (agent either followed it or didn't).

*Frequency: 1 hour*

- [ ] **Step 2: Add check to validate.py**

```python
def check_agent_constraints(skill_path: str) -> list[dict]:
    """
    Verify AGENTS.md contains:
    - A section header "## Agent Constraints"
    - At least 3 bullet points with "Must" or "Must NOT"
    Returns empty list if passing, error list if failing.
    """
```

Wire as part of the default validation pipeline (always runs, errors block). Add `--skip-agent-constraints` flag for manual override.

*Frequency: 1.5 hours*

- [ ] **Step 3: Add test**

In `scripts/tests/test_validate.py`:

```python
def test_agent_constraints_present(tmp_path):
    """Valid AGENTS.md with constraints should pass."""
    ...

def test_agent_constraints_missing(tmp_path):
    """AGENTS.md without constraints should fail."""
    ...

def test_agent_constraints_too_few(tmp_path):
    """AGENTS.md with only 1 constraint should fail."""
    ...
```

*Frequency: 1 hour*

---

### Task 4: AST-level validation (P1-1)

**Effort:** 1-2 days  
**Dependencies:** none  
**Target status:** `validate.py --check-ast` detects dead functions, dead variables, and magic numbers in generated Python code.

- [ ] **Step 1: Add dead function detection**

```python
def _find_dead_functions(tree: ast.AST, module_name: str = "pipeline") -> list[str]:
    """
    Parse the AST, collect all function definitions and all calls/names.
    Return list of function names that are defined but never called (except
    entry points and __main__ guards).
    Skip: main(), run(), functions starting with test_
    """
```

The checker walks the AST of all `.py` files under `scripts/`. A function is "live" if it's called anywhere in the scripts/ directory (cross-file analysis via `pipeline` imports).

*Frequency: 3 hours*

- [ ] **Step 2: Add dead variable detection**

```python
def _find_dead_variables(tree: ast.AST) -> list[str]:
    """
    Find variables that are assigned but never read.
    Ignore: __name__, module-level constants (ALL_CAPS), dunder vars.
    """
```

Simple analysis within each function body: track `ast.Name` targets in assignments and lookups. Complaints about `_` are suppressed.

*Frequency: 2 hours*

- [ ] **Step 3: Add magic number detection**

```python
def _find_magic_numbers(tree: ast.AST) -> list[dict]:
    """
    Find bare numeric literals that are not:
    - Assigned to a named constant
    - 0, 1, -1 (commonly acceptable)
    - Inside test files
    Returns: list of {line, value, context}
    """
```

Threshold: any integer literal ≥ 2 and any float literal not assigned to a named constant. Suppress common constants (0, 1, -1, 0.0, 1.0, 100).

*Frequency: 2 hours*

- [ ] **Step 4: Wire into validate.py**

```python
def check_ast(skill_path: str) -> list[dict]:
    """Run all three AST checks across scripts/*.py."""
    issues = []
    for py_file in Path(skill_path).glob("scripts/**/*.py"):
        tree = ast.parse(py_file.read_text())
        for func in [_find_dead_functions, _find_dead_variables, _find_magic_numbers]:
            result = func(tree)
            issues.extend(result)
    return issues
```

Wire as `validate.py --check-ast <skill-path>`. Output warnings. In rollout mode (`--rollout`), upgrade dead functions to errors.

*Frequency: 1 hour*

- [ ] **Step 5: Add tests**

```python
def test_ast_dead_function(tmp_path):
def test_ast_dead_variable(tmp_path):
def test_ast_magic_number(tmp_path):
def test_ast_clean_code_passes(tmp_path):
```

Each test creates a minimal `.py` file, runs check_ast, asserts correct detection.

*Frequency: 1.5 hours*

---

### Task 5: Defensive I/O templates (P1-2)

**Effort:** 1-2 days  
**Dependencies:** none  
**Target status:** generated I/O code handles encoding mismatch, column name drift, missing directories, and NULL values without crashing.

- [ ] **Step 1: Encoding auto-detection**

Add to I/O template in `scripts/pipeline_template.py`:

```python
import codecs

def _detect_encoding(path: str) -> str:
    """Try utf-8 first, then common fallbacks. Returns encoding name."""
    for enc in ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1", "cp1252"]:
        try:
            with codecs.open(path, "r", encoding=enc) as f:
                f.read(1024)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"  # last resort
```

*Frequency: 1 hour*

- [ ] **Step 2: Column name fuzzy matching**

```python
def _normalize_column(name: str) -> str:
    """Lowercase, strip whitespace, replace spaces/special chars with underscore."""
    import re
    name = name.strip().lower()
    name = re.sub(r"[^\w]", "_", name)
    return name

def _match_columns(expected: list[str], actual: list[str]) -> dict[str, str]:
    """
    Map expected column names to actual column names via normalized matching.
    Logs fuzzy matches as warnings.
    Returns: {expected_name: actual_name}
    """
```

The generated CSV reader uses `_match_columns` instead of assuming exact match.

*Frequency: 1.5 hours*

- [ ] **Step 3: Auto-create output directories**

In all file-writing templates, wrap `open()` with `os.makedirs(os.path.dirname(path), exist_ok=True)`.

*Frequency: 30 minutes*

- [ ] **Step 4: NULL-safe handling**

Add utility function:

```python
def _safe(value, default=None, coerce=None):
    """Return value if not None/empty/NaN, else default. Optionally coerce type."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return default
    if coerce:
        try:
            return coerce(value)
        except (ValueError, TypeError):
            return default
    return value
```

In GROUP BY and comparison code, replace bare `value` references with `_safe(value)` or explicit null filtering.

*Frequency: 1 hour*

- [ ] **Step 6: Update tests**

Modify existing pipeline template tests to cover edge cases: GBK CSV, column name drift, missing output dir, NULL values in key fields.

*Frequency: 1 hour*

---

### Task 6: `--check-universal` in default CI (P1-3)

**Effort:** 0.5 day  
**Dependencies:** `--check-universal` already implemented in validate.py  
**Target status:** universal-mode generated skills have `--check-universal` run as non-blocking lint in the default pipeline.

- [ ] **Step 1: Wire into SKILL.md Phase 5**

In `SKILL.md`, after the existing validation step in Phase 5, add:

```
If --universal mode: run validate.py --check-universal <skill-path> after the
main validation. Treat output as lint (no gate failure for warnings), but
require 0 errors before publish.
```

*Frequency: 15 minutes*

- [ ] **Step 2: Wire into CI config**

Add a step in `.github/workflows/ci.yml` (or equivalent CI config) that runs `python3 scripts/validate.py --check-universal <skill-path>` on universal-mode outputs during the CI matrix. Warning-level, not blocking.

*Frequency: 30 minutes*

- [ ] **Step 3: Update references/pipeline-phases.md**

Add a Phase 5 substep note: "universal layout check (lint)" after the main validation substep.

*Frequency: 15 minutes*

---

### Task 7: Golden case boundary template (P2-1)

**Effort:** 1 day  
**Dependencies:** none  
**Target status:** golden case synthesis in Phase 2 uses a boundary template that generates edge-case inputs per field.

- [ ] **Step 1: Define boundary template per type**

In `references/phase2-eval-assessment.md`, add a subsection documenting the boundary template:

| Type | NULL variant | Empty variant | Max variant | Special variant |
|---|---|---|---|---|
| string | `null` | `""` | length=256 | Unicode + control chars |
| integer | `null` | `0` | `999999` | negative |
| float | `null` | `0.0` | `1e10` | negative, NaN |
| date | `null` | `""` | `9999-12-31` | `0001-01-01`, invalid format |
| boolean | `null` | `false` | — | — |

Each generated golden case set includes exactly one boundary case per field, combined with one normal-case row. The template is a data-driven expansion, not a random generator.

*Frequency: 1.5 hours*

- [ ] **Step 2: Add template instruction to SKILL.md Phase 2**

In the Phase 2 eval criteria section, add:

```
When synthesizing golden case data, include one boundary edge per field
using the template in references/phase2-eval-assessment.md §Boundary Template.
Mark the regular case as "split": "train" and the added boundary cases as
"split": "test" (holdout, scored only in CI).
```

*Frequency: 30 minutes*

- [ ] **Step 3: Validate with example**

Verify against stock-analyzer: run the current golden case synthesis, note which boundaries are missing, then confirm the new template would cover them. (Analysis only, no code change to the example.)

*Frequency: 1 hour*

---

### Task 8: Full static analysis pipeline (P2-2)

**Effort:** 3-5 days  
**Dependencies:** Task 4 (AST validation framework)  
**Target status:** validate.py `--static-analysis` checks import chain validity, undefined references, and type conflicts across the generated skill.

- [ ] **Step 1: Import chain analysis**

```python
def _check_import_chain(script_dir: str, skill_path: str) -> list[dict]:
    """
    1. Resolve all local imports (from . import X, import scripts.utils)
    2. Check each imported name actually exists in the target module
    3. Check for circular imports
    4. For third-party imports in requirements.txt, verify the package is listed
    Returns errors for broken imports, warnings for missing requirements entries.
    """
```

This is the most valuable static check: failing imports are the #1 runtime crash for generated skills.

*Frequency: 3 hours*

- [ ] **Step 2: Undefined reference detection**

```python
def _check_undefined_references(tree: ast.AST, all_names: set[str]) -> list[dict]:
    """
    Within each function, check that every Name node in a Load context
    references either:
    - A parameter of the enclosing function
    - A local assignment in the same function
    - A module-level name (function, class, constant)
    - A builtin
    Report undefined names as errors.
    """
```

Scope tracking: simple (doesn't handle closures or comprehensions fully), but catches 90% of bugs.

*Frequency: 3 hours*

- [ ] **Step 3: Type conflict detection**

```python
def _check_type_conflicts(tree: ast.AST) -> list[dict]:
    """
    Simple type inference for generated pipeline code:
    1. If a function signature has type hints, check call sites match
    2. If a variable is used as both str and int in the same scope, flag
    3. If a comparison mixes incompatible types (e.g. str == int), flag
    """
```

Limited scope: only flag clear contradictions. No inference engine. Only works on code that has type hints (which generated code should have by Phase 5 convention).

*Frequency: 2 hours*

- [ ] **Step 4: Wire into validate.py**

Add `validate.py --static-analysis <skill-path>` which runs all three checks. Requires `--check-ast` to have run first (deps on Task 4). If `--check-ast` found dead code, import/ref/type analysis includes dead functions in its exclusion set.

*Frequency: 30 minutes*

- [ ] **Step 5: Add tests**

```python
def test_import_chain_valid(tmp_path):
def test_import_chain_broken(tmp_path):
def test_undefined_reference(tmp_path):
def test_type_conflict(tmp_path):
```

*Frequency: 2 hours*

---

## Self-Review

**Spec coverage:**

| EVALUATION v2.0 item | Task | AI utilization gain |
|---|---|---|
| P0-1: contract.json (可解读性) | T1 | Agent reads contract → understands assumptions without guessing |
| P0-2: DAG as code (执行可靠性) | T2 | Agent gets step order right automatically |
| P0-3: Agent Constraints (可解读性) | T3 | Agent has explicit behavior boundaries |
| P1-1: AST validation (验证完备性) | T4 | Dead code caught before agent wastes context on it |
| P1-2: Defensive I/O (执行可靠性) | T5 | Edge cases don't crash agent mid-workflow |
| P1-3: --check-universal CI (验证完备性) | T6 | Universal purity maintained without human review |
| P2-1: Golden case boundary (测试有效性) | T7 | Optimization loop has regression signal for edge cases |
| P2-2: Full static analysis (验证完备性) | T8 | Deep defects caught before skill ships |

**Dependency chain:**
- T1–T3 are independent (can run in parallel)
- T4–T6 are independent (can run in parallel)
- T7 is independent
- T8 depends on T4 (AST framework)

**Cross-platform compatibility:** All tasks use Python standard library only. No platform-specific tooling. Validated in both default and `--universal` modes.

---

## Plan Execution Choice

Two execution options:

**1. Subagent-Driven (recommended)** — dispatch one subagent per parallel group:
- Group A (T1, T2, T3): P0 items, independent, run in parallel
- Group B (T4, T5, T6, T7): P1 + P2-1, independent, run after Group A or in parallel
- Group C (T8): depends on T4, run last

**2. Inline Execution** — execute tasks sequentially in this session

**Which approach?**
