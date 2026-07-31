#!/usr/bin/env python3
"""
Spec Compliance Validator for the Agent Skills Open Standard.

Validates a skill directory against the Agent Skills Open Standard by checking
SKILL.md existence, frontmatter structure, naming conventions, and best practices.

Usage:
    python3 scripts/validate.py path/to/skill/
    python3 scripts/validate.py path/to/skill/ --json

Exit codes:
    0 - Valid (no errors, may have warnings)
    1 - Invalid (one or more errors found)
"""

import json
import builtins
import re
import sys
import ast
from pathlib import Path

from skill_document import SkillDoc


# --- Constants ---

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_BODY_LINES_WARNING = 500

# Pattern for valid skill names: lowercase letters, numbers, hyphens
NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"--")

# Pattern for YYYY-MM-DD date format
DATE_FORMAT_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Pattern for local file references in markdown: [text](path) excluding http/https/mailto/#
LOCAL_LINK_PATTERN = re.compile(
    r"\[([^\]]*)\]\(([^)]+)\)"
)


def _extract_local_links(body: str) -> list[str]:
    """
    Extract local file paths referenced in markdown links within the body.

    Filters out URLs (http, https, mailto) and anchor links (#).

    Args:
        body: The markdown body text.

    Returns:
        List of relative file paths referenced in the body.
    """
    paths: list[str] = []
    for match in LOCAL_LINK_PATTERN.finditer(body):
        target = match.group(2).strip()
        # Skip external URLs and anchors
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # Strip any anchor fragment from the path
        if "#" in target:
            target = target.split("#")[0]
        if target:
            paths.append(target)
    return paths


def validate_skill(skill_path: str) -> dict:
    """
    Validate a skill directory against the Agent Skills Open Standard.

    Performs both required checks (errors) and recommended checks (warnings).

    Args:
        skill_path: Path to the skill directory to validate.

    Returns:
        Dictionary with keys:
            - ``valid`` (bool): True if no errors were found.
            - ``errors`` (list[str]): List of error messages (must fix).
            - ``warnings`` (list[str]): List of warning messages (should fix).
    """
    errors: list[str] = []
    warnings: list[str] = []

    skill_dir = Path(skill_path).resolve()

    # --- Check: directory exists ---
    if not skill_dir.exists():
        errors.append(f"Path does not exist: {skill_dir}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    if not skill_dir.is_dir():
        errors.append(f"Path is not a directory: {skill_dir}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # --- Check: SKILL.md exists ---
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append("SKILL.md not found in skill directory")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # --- Read SKILL.md ---
    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception as exc:
        errors.append(f"Could not read SKILL.md: {exc}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # --- Check: frontmatter exists ---
    if not content.startswith("---"):
        errors.append("SKILL.md must start with '---' frontmatter delimiter")
        return {"valid": False, "errors": errors, "warnings": warnings}

    doc = SkillDoc.from_text(content)
    body = doc.body

    if doc.frontmatter is None:
        errors.append("SKILL.md frontmatter is not properly closed (missing closing '---')")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # --- Check: name field ---
    name_value = doc.name
    if name_value is None:
        errors.append("'name' field is missing from frontmatter")
    else:
        name_value = name_value.strip()
        if len(name_value) == 0:
            errors.append("'name' field is empty")
        elif len(name_value) > MAX_NAME_LENGTH:
            errors.append(
                f"'name' field exceeds {MAX_NAME_LENGTH} characters "
                f"(found {len(name_value)})"
            )
        else:
            # Validate name format
            if not NAME_PATTERN.match(name_value):
                errors.append(
                    f"'name' field must contain only lowercase letters, numbers, "
                    f"and hyphens (found: '{name_value}')"
                )
            if name_value.startswith("-"):
                errors.append(f"'name' must not start with a hyphen (found: '{name_value}')")
            if name_value.endswith("-"):
                errors.append(f"'name' must not end with a hyphen (found: '{name_value}')")
            if CONSECUTIVE_HYPHENS_PATTERN.search(name_value):
                errors.append(
                    f"'name' must not contain consecutive hyphens (found: '{name_value}')"
                )

            # --- Check: directory name matches name field ---
            dir_name = skill_dir.name
            if dir_name != name_value:
                errors.append(
                    f"Directory name '{dir_name}' does not match 'name' field "
                    f"'{name_value}' in frontmatter"
                )

    # --- Check: description field ---
    description_value = doc.description
    if description_value is None:
        errors.append("'description' field is missing from frontmatter")
    else:
        description_value = description_value.strip()
        if len(description_value) == 0:
            errors.append("'description' field is empty")
        elif len(description_value) > MAX_DESCRIPTION_LENGTH:
            errors.append(
                f"'description' field exceeds {MAX_DESCRIPTION_LENGTH} characters "
                f"(found {len(description_value)})"
            )

    # --- Check: -cskill suffix is deprecated ---
    if name_value is not None and name_value.endswith("-cskill"):
        errors.append(
            f"'name' uses the deprecated '-cskill' suffix. "
            f"Use '-skill' instead (found: '{name_value}')"
        )

    # --- Warnings ---

    # Naming convention: -skill suffix (or -suite for suites)
    if name_value is not None and len(name_value) > 0:
        if not name_value.endswith("-skill") and not name_value.endswith("-suite"):
            warnings.append(
                f"'name' should end with '-skill' for discoverability "
                f"(found: '{name_value}')"
            )

    # Body line count
    if body is not None:
        body_lines = body.split("\n")
        body_line_count = len(body_lines)
        if body_line_count > MAX_BODY_LINES_WARNING:
            warnings.append(
                f"SKILL.md body exceeds {MAX_BODY_LINES_WARNING} lines "
                f"({body_line_count} lines). Consider moving content to references/."
            )

    # license field
    if not doc.has_field("license"):
        warnings.append("'license' field is missing from frontmatter")

    # metadata field
    if not doc.has_field("metadata"):
        warnings.append("'metadata' field is missing from frontmatter")
    else:
        if not doc.has_subfield("metadata", "author"):
            warnings.append("'metadata.author' sub-field is missing")
        if not doc.has_subfield("metadata", "version"):
            warnings.append("'metadata.version' sub-field is missing")

        # Temporal metadata validation (optional, warnings only)
        created_val = doc.subfield("metadata", "created")
        reviewed_val = doc.subfield("metadata", "last_reviewed")
        interval_val = doc.subfield("metadata", "review_interval_days")

        if created_val and not DATE_FORMAT_PATTERN.match(created_val.strip()):
            warnings.append(
                f"'metadata.created' should be YYYY-MM-DD format (found: '{created_val}')"
            )
        if reviewed_val and not DATE_FORMAT_PATTERN.match(reviewed_val.strip()):
            warnings.append(
                f"'metadata.last_reviewed' should be YYYY-MM-DD format (found: '{reviewed_val}')"
            )
        if interval_val:
            try:
                int(interval_val.strip())
            except ValueError:
                warnings.append(
                    f"'metadata.review_interval_days' should be an integer (found: '{interval_val}')"
                )

        has_temporal = bool(created_val or reviewed_val or interval_val)
        if not has_temporal:
            warnings.append(
                "Consider adding temporal metadata (metadata.created, metadata.last_reviewed, "
                "metadata.review_interval_days) for staleness tracking"
            )

    # AGENTS.md companion file
    agents_md = skill_dir / "AGENTS.md"
    if not agents_md.exists():
        warnings.append(
            "AGENTS.md not found. Adding an AGENTS.md companion file maximizes "
            "cross-tool discoverability (read by 15+ tools including Codex CLI, "
            "Cursor, Roo Code, Kilo Code, Kiro, Goose, and others)."
        )

    # activation field (harness factory v1.1)
    if not doc.has_field("activation"):
        warnings.append(
            "'activation' field is missing from frontmatter. "
            "Add 'activation: /{skill-name}' for namespace enforcement."
        )

    # provenance field (harness factory v1.1)
    if not doc.has_field("provenance"):
        warnings.append(
            "'provenance' field is missing from frontmatter. "
            "Add provenance metadata (maintainer, version, created, source_references)."
        )

    # Referenced local files
    if body is not None:
        local_links = _extract_local_links(body)
        for link_path in local_links:
            resolved = skill_dir / link_path
            if not resolved.exists():
                warnings.append(
                    f"Referenced file does not exist: '{link_path}'"
                )

        # --- Quick Profile validation ---
        _validate_quick_profile(skill_dir, errors, warnings)

        # --- Description format validation ---
        _validate_description_format(doc, errors)

        # --- Check for per-skill AGENTS.md ---
        ag = skill_dir / "AGENTS.md"
        if ag.exists():
            warnings.append(
                "per-skill AGENTS.md found — selection info should be in SKILL.md Quick Profile"
            )

        # --- README.md presence check ---
        readme = skill_dir / "README.md"
        if not readme.exists():
            warnings.append("README.md not found — installation instructions are required")


    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def check_universal_layout(skill_path: str) -> list[dict]:
    """Return a list of issue dicts for universal layout violations."""
    issues = []
    root = Path(skill_path)
    forbidden = [
        (".claude-plugin", "Claude-specific plugin manifest"),
        ("install.sh", "Platform installer (use skillctl instead)"),
        ("scripts/evolve.py", "Self-maintenance script"),
        ("scripts/staleness_check.py", "Lifecycle maintenance script"),
        ("scripts/review_staleness.py", "Lifecycle maintenance script"),
        ("scripts/dependency_health.py", "Lifecycle maintenance script"),
        ("scripts/schema_drift.py", "Lifecycle maintenance script"),
        ("scripts/skill_document.py", "Lifecycle maintenance script"),
    ]
    for path_str, reason in forbidden:
        if (root / path_str).exists():
            issues.append({
                "level": "error",
                "check": "universal-layout",
                "message": f"{path_str}: {reason}",
            })
    return issues


def _print_human_readable(result: dict, skill_path: str) -> None:
    """
    Print validation results in a human-readable format.

    Args:
        result: The validation result dictionary.
        skill_path: The path that was validated (for display).
    """
    print(f"Validating: {skill_path}")
    print(f"{'=' * 60}")

    if result["valid"]:
        print("Status: VALID")
    else:
        print("Status: INVALID")

    if result["errors"]:
        print(f"\nErrors ({len(result['errors'])}):")
        for error in result["errors"]:
            print(f"  [ERROR] {error}")

    if result["warnings"]:
        print(f"\nWarnings ({len(result['warnings'])}):")
        for warning in result["warnings"]:
            print(f"  [WARN]  {warning}")

    if not result["errors"] and not result["warnings"]:
        print("\nNo issues found.")

    print(f"{'=' * 60}")



def _validate_quick_profile(skill_dir: Path, errors: list, warnings: list) -> None:
    """Validate Quick Profile section in SKILL.md body."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return

    text = skill_md.read_text(encoding="utf-8")

    if "## Quick Profile" not in text:
        errors.append("SKILL.md missing ## Quick Profile section")
        return

    profile_match = re.search(
        r"## Quick Profile\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    if not profile_match:
        errors.append("Could not parse Quick Profile section")
        return

    profile_text = profile_match.group(1)

    for pattern, msg in [
        (r"\*\*Category\*\*", "Missing **Category** in Quick Profile"),
        (r"\*\*Input\*\*", "Missing **Input** in Quick Profile"),
        (r"\*\*Output\*\*", "Missing **Output** in Quick Profile"),
    ]:
        if not re.search(pattern, profile_text):
            errors.append(msg)

    when_match = re.search(r"\*\*When to use\*\*\s*:\s*(.+)", profile_text)
    if when_match:
        items = [x.strip() for x in when_match.group(1).split(",") if x.strip()]
        if len(items) < 2:
            warnings.append("Quick Profile When to use should have >= 2 items")
    else:
        errors.append("Missing **When to use** in Quick Profile")

    when_not_match = re.search(r"\*\*When not\*\*\s*:\s*(.+)", profile_text)
    if when_not_match:
        items = [x.strip() for x in when_not_match.group(1).split(",") if x.strip()]
        if len(items) < 1:
            warnings.append("Quick Profile When not should have >= 1 items")
    else:
        errors.append("Missing **When not** in Quick Profile")



def _validate_description_format(doc, errors: list) -> None:
    """Validate description starts with A/An + noun."""
    desc = doc.description
    if desc is None:
        return
    desc = desc.strip()
    if not re.match(r"^(A|An)\s+", desc):
        errors.append(
            "description must start with 'A {category}' or 'An {category}'" +             " (found: '" + desc[:40] + "...')"
        )
    word_count = len(desc.split())
    if word_count > 80:
        errors.append(
            f"description is {word_count} words (target: 40-60, max: 80)"
        )

def main() -> None:
    """CLI entry point for the spec compliance validator."""
    if len(sys.argv) < 2:
        print(
            "Usage: python3 scripts/validate.py <skill-path> [--json] [--check-contract]"
            " [--check-universal] [--check-ast] [--rollout] [--static-analysis]\n"
            "\n"
            "Arguments:\n"
            "  skill-path    Path to the skill directory to validate\n"
            "\n"
            "Options:\n"
            "  --json            Output results as JSON to stdout\n"
            "  --check-contract  Validate contract.json against code implementation\n"
            "  --check-universal Check for platform-specific files (universal mode)\n"
            "  --check-ast       Run AST-level static analysis (dead code, magic numbers)\n"
            "  --rollout         Upgrade dead-function warnings to errors\n"
            "  --static-analysis Run full static analysis (import chain, refs, types)\n"
            "\n"
            "Exit codes:\n"
            "  0  Valid (no errors)\n"
            "  1  Invalid (one or more errors)\n",
            file=sys.stderr,
        )
        sys.exit(1)

    skill_path = sys.argv[1]
    use_json = "--json" in sys.argv
    check_universal = "--check-universal" in sys.argv
    check_contract_flag = "--check-contract" in sys.argv
    check_ast_flag = "--check-ast" in sys.argv
    rollout = "--rollout" in sys.argv
    static_analysis_flag = "--static-analysis" in sys.argv

    result = validate_skill(skill_path)
    contract_issues: list[dict] = []
    ast_issues: list[dict] = []
    static_analysis_issues: list[dict] = []

    # Universal layout check
    if check_universal:
        extra_issues = check_universal_layout(skill_path)
        for issue in extra_issues:
            result["errors"].append(issue["message"])
        result["valid"] = len(result["errors"]) == 0

    # Contract consistency check
    if check_contract_flag:
        contract_issues = check_contract(skill_path, universal=check_universal)
        for issue in contract_issues:
            if issue["level"] == "error":
                result["errors"].append(issue["message"])
            else:
                result["warnings"].append(issue["message"])
        result["valid"] = len(result["errors"]) == 0

    # AST-level static analysis
    if check_ast_flag:
        ast_issues = check_ast(skill_path, rollout=rollout)
        for issue in ast_issues:
            if issue["level"] == "error":
                result["errors"].append(issue["message"])
            else:
                result["warnings"].append(issue["message"])
        result["valid"] = len(result["errors"]) == 0

    # Full static analysis (import chain, undefined refs, type conflicts)
    if static_analysis_flag:
        static_analysis_issues = check_static_analysis(skill_path)
        for issue in static_analysis_issues:
            if issue["level"] == "error":
                result["errors"].append(issue["message"])
            else:
                result["warnings"].append(issue["message"])
        result["valid"] = len(result["errors"]) == 0

    if use_json:
        print(json.dumps(result, indent=2))
    else:
        _print_human_readable(result, skill_path)
        if check_contract_flag and contract_issues:
            print("\nContract checks (%d):" % len(contract_issues))
            for issue in contract_issues:
                label = "ERROR" if issue["level"] == "error" else "WARN"
                print("  [%s]  %s" % (label, issue["message"]))
            print("=" * 60)
        if check_ast_flag and ast_issues:
            print("\nAST checks (%d):" % len(ast_issues))
            for issue in ast_issues:
                label = "ERROR" if issue["level"] == "error" else "WARN"
                print("  [%s]  %s" % (label, issue["message"]))
            print("=" * 60)
        if static_analysis_flag and static_analysis_issues:
            print("\nStatic analysis (%d):" % len(static_analysis_issues))
            for issue in static_analysis_issues:
                label = "ERROR" if issue["level"] == "error" else "WARN"
                print("  [%s]  %s" % (label, issue["message"]))
            print("=" * 60)

    sys.exit(0 if result["valid"] else 1)


def check_contract(skill_path: str, universal: bool = False) -> list[dict]:
    """
    Validate contract.json against the actual skill implementation.

    Reads the generated skill's contract.json (if present) and cross-references
    its declarations against the code and filesystem. In default mode, violations
    produce warnings; in universal mode, missing mandatory sections become errors.

    Checks performed:
      1. All declared output files exist under skill_path.
      2. All declared column names appear in I/O code (scripts/ directory).
      3. Declared step count roughly matches pipeline.py function count.
      4. If contract.json is absent, a single warning (or error in universal mode).

    Args:
        skill_path: Path to the skill directory to check.
        universal: If True, upgrade missing mandatory sections to errors.

    Returns:
        List of issue dicts with keys:
            - ``level``: ``"warn"`` or ``"error"``
            - ``check``: ``"contract"``
            - ``message``: human-readable description
    """
    issues: list[dict] = []
    root = Path(skill_path).resolve()
    contract_path = root / "contract.json"

    if not contract_path.exists():
        level = "error" if universal else "warn"
        msg = "contract.json not found — skill lacks a machine-readable assumption declaration."
        if universal:
            msg += " contract.json is mandatory in universal mode."
        issues.append({"level": level, "check": "contract", "message": msg})
        return issues

    # Parse contract.json
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append({
            "level": "error",
            "check": "contract",
            "message": f"contract.json is not valid JSON: {exc}",
        })
        return issues

    if not isinstance(contract, dict):
        issues.append({"level": "error", "check": "contract", "message": "contract.json must be a JSON object."})
        return issues

    # --- Check 1: declared output files exist ---
    output_section = contract.get("output")
    if isinstance(output_section, dict):
        for artifact_name, artifact_info in output_section.items():
            path_val = artifact_info.get("path") if isinstance(artifact_info, dict) else None
            if path_val and isinstance(path_val, str):
                resolved = root / path_val
                if not resolved.exists():
                    issues.append({
                        "level": "warn",
                        "check": "contract",
                        "message": f"Contract declares output '{artifact_name}' at '{path_val}' but file does not exist.",
                    })

    # --- Check 2: declared columns appear in scripts/ I/O code ---
    input_section = contract.get("input")
    if isinstance(input_section, dict):
        columns = input_section.get("columns")
        if isinstance(columns, dict) and columns:
            scripts_dir = root / "scripts"
            if scripts_dir.is_dir():
                script_texts: list[str] = []
                for py_file in scripts_dir.rglob("*.py"):
                    try:
                        script_texts.append(py_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                combined = "\n".join(script_texts)
                for col_name in columns:
                    if col_name not in combined:
                        issues.append({
                            "level": "warn",
                            "check": "contract",
                            "message": f"Contract declares input column '{col_name}' but it was not found in scripts/ code.",
                        })

    # --- Check 3: DAG step count vs pipeline.py function count ---
    dag_section = contract.get("dag")
    pipeline_script = root / "scripts" / "run_pipeline.py"
    if isinstance(dag_section, dict):
        dag_steps = dag_section.get("steps")
        if isinstance(dag_steps, list) and dag_steps:
            declared_count = len(dag_steps)
            if pipeline_script.exists():
                try:
                    pipeline_text = pipeline_script.read_text(encoding="utf-8")
                    # Rough heuristic: count `def ` lines, skip main() and helpers
                    func_lines = [ln for ln in pipeline_text.splitlines() if ln.strip().startswith("def ")]
                    # Exclude common entry-points
                    func_count = sum(1 for f in func_lines if "def main(" not in f and "def run(" not in f)
                    diff = abs(declared_count - func_count)
                    if diff > 2:
                        issues.append({
                            "level": "warn",
                            "check": "contract",
                            "message": (
                                f"Contract declares {declared_count} DAG steps but pipeline.py has roughly "
                                f"{func_count} pipeline functions (diff={diff})."
                            ),
                        })
                except Exception:
                    pass

    # --- Universal mode: upgrade mandatory checks ---
    if universal:
        for section_name in ("input", "output", "dag"):
            if section_name not in contract or not isinstance(contract.get(section_name), dict):
                issues.append({
                    "level": "error",
                    "check": "contract",
                    "message": f"Mandatory section '{section_name}' is missing from contract.json in universal mode.",
                })

    return issues


MIN_AGENT_CONSTRAINTS = 3


def check_agent_constraints(skill_path: str) -> list[dict]:
    """
    Verify AGENTS.md contains:
    - A section header "## Agent Constraints"
    - At least MIN_AGENT_CONSTRAINTS bullet points with "Must" or "Must NOT"

    Returns empty list if passing, error list if failing (this is a blocking check).
    """
    issues: list[dict] = []
    root = Path(skill_path).resolve()
    agents_md = root / "AGENTS.md"

    if not agents_md.exists():
        issues.append({
            "level": "error",
            "check": "agent-constraints",
            "message": "AGENTS.md not found. Cannot verify agent constraints.",
        })
        return issues

    try:
        content = agents_md.read_text(encoding="utf-8")
    except Exception as exc:
        issues.append({
            "level": "error",
            "check": "agent-constraints",
            "message": f"Could not read AGENTS.md: {exc}",
        })
        return issues

    # Check for "## Agent Constraints" section header
    if "## Agent Constraints" not in content:
        issues.append({
            "level": "error",
            "check": "agent-constraints",
            "message": "AGENTS.md is missing a '## Agent Constraints' section header.",
        })
        return issues

    # Count "Must" or "Must NOT" bullet points (case-insensitive)
    lines = content.splitlines()
    in_constraints_section = False
    must_bullets = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Agent Constraints"):
            in_constraints_section = True
            continue
        if in_constraints_section:
            # Stop counting at the next top-level heading
            if stripped.startswith("## ") and not stripped.startswith("## Agent Constraints"):
                break
            # Count bullet points with "Must" or "Must NOT"
            if stripped.startswith(("- ", "1. ", "2. ", "3. ", "4. ", "5. ")):
                upper = stripped.upper()
                if " MUST " in upper or stripped.upper().startswith("- MUST ") or \
                   stripped.upper().startswith("1. MUST ") or stripped.upper().startswith("2. MUST ") or \
                   stripped.upper().startswith("3. MUST ") or stripped.upper().startswith("4. MUST ") or \
                   stripped.upper().startswith("5. MUST "):
                    must_bullets += 1

    if must_bullets < MIN_AGENT_CONSTRAINTS:
        issues.append({
            "level": "error",
            "check": "agent-constraints",
            "message": (
                f"AGENTS.md '## Agent Constraints' section has only {must_bullets} 'Must'/'Must NOT' "
                f"bullet points (minimum {MIN_AGENT_CONSTRAINTS} required)."
            ),
        })

    return issues


# ── AST-level static analysis ─────────────────────────────────────────────────


def _find_dead_functions(tree: ast.AST, module_name: str = "pipeline") -> list[str]:
    """Return names of functions defined but never called.

    Performs cross-file analysis: a function is "live" if its name appears as
    a Call target anywhere in the module. Callers supply cross-file call-site
    tracking externally.

    Skip: main(), run(), functions starting with test_, imported names.
    """
    defined: set[str] = set()
    called: set[str] = set()
    imports: set[str] = set()

    for node in ast.walk(tree):
        # Collect function definitions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.add(node.name)

        # Collect import aliases
        elif isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split(".")[0]
                imports.add(local_name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                local_name = alias.asname or alias.name
                imports.add(local_name)

        # Collect call targets — only simple names (not method calls like obj.method)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)

    dead: list[str] = []
    skip = {"main", "run"}
    for fn in sorted(defined):
        fn_lower = fn.lower()
        if fn_lower.startswith("test_"):
            continue
        if fn in skip:
            continue
        if fn in imports:
            continue
        if fn not in called:
            dead.append(fn)

    return dead


def _find_dead_variables(tree: ast.AST) -> list[str]:
    """Find variables assigned but never read within each function body.

    Tracks ``ast.Name`` nodes in *Store* context vs *Load* context per
    function.  Ignores ``__name__``, module-level *ALL_CAPS* constants,
    dunder variables (``__xxx__``), and ``_``.
    """
    dead: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        stores: set[str] = set()
        loads: set[str] = set()

        for child in ast.walk(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip nested function scopes — not tracked for dead vars
                continue

            if isinstance(child, ast.Name):
                kind = child.ctx.__class__.__name__
                name = child.id

                # Skip ignored names
                if name == "_":
                    continue
                if name == "__name__":
                    continue
                if name.startswith("__") and name.endswith("__"):
                    continue
                if name.isupper() and len(name) > 1:
                    continue

                if kind == "Store":
                    stores.add(name)
                elif kind == "Load":
                    loads.add(name)

        for name in sorted(stores):
            if name not in loads:
                dead.add(name)

    return sorted(dead)


def _find_magic_numbers(tree: ast.AST) -> list[dict]:
    """Find bare numeric literals that aren't assigned to named constants.

    Suppressed values: ``0``, ``1``, ``-1``, ``0.0``, ``1.0``, ``100``.

    Returns ``[{line, value, context_string}]`` where *context_string* is a
    short snippet of the source line around the literal.
    """
    numeric_skip: set = {0, 1, -1, 0.0, 1.0, 100}

    # Collect names that are assigned constants (simple Name = Constant)
    const_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                    const_names.add(target.id)

    magic: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            val = node.value
            if not isinstance(val, (int, float)):
                continue
            if val in numeric_skip:
                continue
            # Skip if this Constant is the value of an assignment to a named constant
            if isinstance(node, ast.Constant) and any(
                isinstance(parent, ast.Assign) and
                any(isinstance(t, ast.Name) and t.id in const_names for t in parent.targets)
                for parent in _get_parents(tree, node)
            ):
                continue
            # Derive a short context snippet (value repr)
            magic.append({
                "line": node.lineno,
                "value": val,
                "context_string": repr(val),
            })

    return magic


def _get_parents(tree: ast.AST, target: ast.AST) -> list[ast.AST]:
    """Walk tree to find all parent nodes of *target*. Utility for magic-number
    detection."""
    parents: list[ast.AST] = []

    class _Finder(ast.NodeVisitor):
        def visit(self, node: ast.AST) -> None:
            for child in ast.iter_child_nodes(node):
                if child is target:
                    parents.append(node)
                self.visit(child)

    _Finder().visit(tree)
    return parents


def check_ast(skill_path: str, rollout: bool = False) -> list[dict]:
    """Run all three AST checks across ``scripts/*.py``.

    Args:
        skill_path: Root directory of the skill.
        rollout: When True, dead-function warnings are upgraded to errors.

    Returns:
        List of issue dicts with keys ``level``, ``check``, ``message``.
    """
    issues: list[dict] = []
    root = Path(skill_path).resolve()
    script_dir = root / "scripts"

    if not script_dir.is_dir():
        issues.append({
            "level": "warn",
            "check": "ast",
            "message": "No scripts/ directory found — skipping AST checks.",
        })
        return issues

    # Phase 1: collect all function definitions and call targets across files
    all_defs: dict[str, list[str]] = {}  # fn_name → [file1, file2, ...]
    all_calls: dict[str, list[str]] = {}

    py_files = sorted(script_dir.rglob("*.py"))
    if not py_files:
        issues.append({
            "level": "warn",
            "check": "ast",
            "message": "No .py files found under scripts/ — skipping AST checks.",
        })
        return issues

    for py_file in py_files:
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            issues.append({
                "level": "warn",
                "check": "ast",
                "message": f"Syntax error in {py_file.relative_to(root)}: {exc}",
            })
            continue

        _gather_names(tree, all_defs, all_calls, str(py_file.relative_to(root)))

    # Dead function detection: function defined but never called
    for fn_name, files in sorted(all_defs.items()):
        fn_lower = fn_name.lower()
        if fn_lower.startswith("test_"):
            continue
        if fn_name in {"main", "run"}:
            continue
        if fn_name not in all_calls:
            for f in files:
                level = "error" if rollout else "warn"
                issues.append({
                    "level": level,
                    "check": "ast",
                    "message": (
                        f"Dead function '{fn_name}' defined in {f} "
                        f"is never called anywhere in scripts/."
                    ),
                })

    # Phase 2: per-file checks (dead vars, magic numbers)
    for py_file in py_files:
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        rel = str(py_file.relative_to(root))

        # Dead variable check
        for var in _find_dead_variables(tree):
            issues.append({
                "level": "warn",
                "check": "ast",
                "message": f"Dead variable '{var}' in {rel} — assigned but never read.",
            })

        # Magic number check
        for item in _find_magic_numbers(tree):
            issues.append({
                "level": "warn",
                "check": "ast",
                "message": (
                    f"Magic number {item['context_string']} on line {item['line']} "
                    f"of {rel} — consider assigning to a named constant."
                ),
            })

    return issues


def _gather_names(
    tree: ast.AST,
    defs: dict[str, list[str]],
    calls: dict[str, list[str]],
    rel_path: str,
) -> None:
    """Populate *defs* and *calls* dicts with function-level definitions and
    simple-name call targets from a single AST."""
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defs.setdefault(node.name, []).append(rel_path)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                imports.add(name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                imports.add(name)

    # Second pass: collect calls (excluding imported names)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id not in imports:
                calls.setdefault(node.func.id, []).append(rel_path)

# ---------------------------------------------------------------------------
# Static analysis: import chain, undefined references, type conflicts
# ---------------------------------------------------------------------------


def _resolve_relative_target(
    importing_file: Path, level: int, module_name: str
) -> Path | None:
    """Resolve a relative import to an existing .py file.
    
    *level* is the number of dots (1 for ., 2 for .., etc.).
    *module_name* is the module part after the dots, or empty.
    """
    base = importing_file.parent
    for _ in range(1, level):
        base = base.parent

    if module_name:
        candidates = [
            base / f"{module_name}.py",
            base / module_name / "__init__.py",
        ]
    else:
        candidates = [base / "__init__.py"]

    for c in candidates:
        if c.is_file():
            return c
    return None


def _resolve_scripts_target(
    script_dir_path: Path, module_name: str
) -> Path | None:
    """Resolve a ``scripts.xxx.yyy`` import to an existing .py file under
    *script_dir_path*."""
    parts = module_name.split(".")
    if parts[0] != "scripts" or len(parts) < 2:
        return None

    target = script_dir_path
    for p in parts[1:]:
        target = target / p

    candidates = [
        target.with_name(target.name + ".py"),
        target / "__init__.py",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def _collect_module_level_names(tree: ast.AST) -> set[str]:
    """Collect all names defined at the top level of a module AST."""
    names: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
                elif isinstance(target, (ast.Tuple, ast.List)):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            names.add(elt.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _collect_imports(tree: ast.AST) -> list[dict]:
    """Collect import statements from a module AST."""
    imports: list[dict] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "lineno": node.lineno,
                    "module": alias.name,
                    "names": [alias.asname or alias.name],
                    "is_relative": False,
                    "level": 0,
                    "is_from": False,
                })
        elif isinstance(node, ast.ImportFrom):
            imports.append({
                "lineno": node.lineno,
                "module": node.module or "",
                "names": [a.asname or a.name for a in node.names],
                "is_relative": node.level > 0,
                "level": node.level,
                "is_from": True,
            })
    return imports


def _check_import_chain(script_dir: str, skill_path: str) -> list[dict]:
    """Analyze import chains within a skill's ``scripts/`` directory.
    
    Checks:
    
    1.  Local imports (absolute ``scripts.xxx`` and relative ``.xxx``)
        resolve to existing files, and imported names exist in the target
        module.
    2.  No circular imports between local modules.
    3.  Third-party imports are declared in ``requirements.txt`` (warning
        if missing).
    
    Returns issues with ``check="static_analysis"``.
    """
    issues: list[dict] = []
    script_dir_path = Path(script_dir).resolve()
    skill_dir = Path(skill_path).resolve()

    if not script_dir_path.is_dir():
        return issues  # reported by check_ast if needed

    py_files = sorted(script_dir_path.rglob("*.py"))
    if not py_files:
        return issues

    # ---- Phase 1: parse all files ----
    module_names: dict[str, set[str]] = {}        # rel_path -> names
    module_imports: dict[str, list[dict]] = {}     # rel_path -> imports
    all_trees: dict[str, ast.AST] = {}             # rel_path -> tree

    for py_file in py_files:
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        rel = str(py_file.relative_to(skill_dir))
        module_names[rel] = _collect_module_level_names(tree)
        module_imports[rel] = _collect_imports(tree)
        all_trees[rel] = tree

    # ---- Phase 2: resolve imports, check names, build dependency graph ----
    dep_graph: dict[str, set[str]] = {}  # rel -> {imported rel paths}

    for rel_path, imports in module_imports.items():
        importing_file = (skill_dir / rel_path).resolve()
        imported_modules: set[str] = set()

        for imp in imports:
            if imp["is_relative"]:
                target = _resolve_relative_target(
                    importing_file, imp["level"], imp["module"]
                )
                if target is not None:
                    target_rel = str(target.relative_to(skill_dir))
                    imported_modules.add(target_rel)
                    tgt_names = module_names.get(target_rel, set())
                    for name in imp["names"]:
                        if name != "*" and name not in tgt_names:
                            issues.append({
                                "level": "error",
                                "check": "static_analysis",
                                "message": (
                                    f"Import '{name}' in {rel_path}:{imp['lineno']} "
                                    f"does not exist in target "
                                    f"module '{imp['module']}'."
                                ),
                            })
                elif imp["module"]:
                    issues.append({
                        "level": "error",
                        "check": "static_analysis",
                        "message": (
                            f"Relative import target '{imp['module']}' not found "
                            f"(resolved from {rel_path}:{imp['lineno']})."
                        ),
                    })
                # else: from . import X with no __init__.py — skip
            else:
                parts = imp["module"].split(".")

                if parts[0] == "scripts" and len(parts) > 1:
                    # Local absolute import
                    target = _resolve_scripts_target(script_dir_path, imp["module"])
                    if target is not None:
                        target_rel = str(target.relative_to(skill_dir))
                        if target_rel in all_trees:
                            imported_modules.add(target_rel)

                        tgt_names = module_names.get(target_rel, set())
                        if imp.get("is_from", False):
                            for name in imp["names"]:
                                if name != "*" and name not in tgt_names:
                                    issues.append({
                                        "level": "error",
                                        "check": "static_analysis",
                                        "message": (
                                            f"Import '{name}' in {rel_path}:{imp['lineno']} "
                                            f"does not exist in target "
                                            f"module '{imp['module']}'."
                                        ),
                                    })
                    else:
                        issues.append({
                            "level": "error",
                            "check": "static_analysis",
                            "message": (
                                f"Local import '{imp['module']}' in "
                                f"{rel_path}:{imp['lineno']} not found."
                            ),
                        })
                elif parts[0] not in _STDLIB_MODULES and not imp["is_relative"]:
                    # Third-party — check requirements.txt
                    req_path = skill_dir / "requirements.txt"
                    if not req_path.is_file():
                        issues.append({
                            "level": "warn",
                            "check": "static_analysis",
                            "message": (
                                f"Third-party import '{imp['module']}' in "
                                f"{rel_path}:{imp['lineno']} — "
                                f"no requirements.txt found."
                            ),
                        })
                    else:
                        req_text = req_path.read_text(encoding="utf-8")
                        # Split on newlines and take the package name (before any version spec)
                        req_pkgs = set()
                        for line in req_text.splitlines():
                            line = line.strip()
                            if line and not line.startswith("#"):
                                # Handle -r, -e, etc.
                                if line.startswith("-e ") or line.startswith("--editable "):
                                    line = line.split()[-1].split("#egg=")[-1] if "#egg=" in line else ""
                                # Take package name from requirement spec
                                pkg_name = re.split(r"[<>=!~\[]", line)[0].strip()
                                if pkg_name and not pkg_name.startswith(("-", "#", "git", "svn", "hg")):
                                    req_pkgs.add(pkg_name.lower().replace("_", "-"))

                        top_level = parts[0].lower().replace("_", "-")
                        if top_level not in req_pkgs:
                            issues.append({
                                "level": "warn",
                                "check": "static_analysis",
                                "message": (
                                    f"Third-party import '{imp['module']}' in "
                                    f"{rel_path}:{imp['lineno']} — "
                                    f"package '{top_level}' not found in "
                                    f"requirements.txt."
                                ),
                            })

        dep_graph[rel_path] = imported_modules

    # ---- Phase 3: circular import detection ----
    def _find_cycle(
        node: str,
        visited: set[str],
        stack: set[str],
        graph: dict[str, set[str]],
    ) -> bool:
        visited.add(node)
        stack.add(node)
        for neighbour in graph.get(node, set()):
            if neighbour not in visited:
                if _find_cycle(neighbour, visited, stack, graph):
                    return True
            elif neighbour in stack:
                return True
        stack.discard(node)
        return False

    visited: set[str] = set()
    for node in dep_graph:
        if node not in visited:
            if _find_cycle(node, visited, set(), dep_graph):
                # Collect the cycle path for a better message
                issues.append({
                    "level": "error",
                    "check": "static_analysis",
                    "message": (
                        f"Circular import detected involving '{node}' — "
                        f"module imports a module that imports back to it."
                    ),
                })

    return issues


_STDLIB_MODULES: frozenset[str] = frozenset({
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncore",
    "atexit", "audioop", "base64", "bdb", "binascii", "binhex", "bisect",
    "builtins", "bz2", "calendar", "cgi", "cgitb", "chunk", "cmath",
    "cmd", "code", "codecs", "codeop", "collections", "colorsys",
    "compileall", "concurrent", "configparser", "contextlib", "contextvars",
    "copy", "copyreg", "cProfile", "crypt", "csv", "ctypes", "curses",
    "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis",
    "distutils", "doctest", "email", "encodings", "enum", "errno",
    "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch", "fractions",
    "ftplib", "functools", "gc", "getopt", "getpass", "gettext", "glob",
    "grp", "gzip", "hashlib", "heapq", "hmac", "html", "http", "idlelib",
    "imaplib", "imghdr", "imp", "importlib", "inspect", "io", "ipaddress",
    "itertools", "json", "keyword", "lib2to3", "linecache", "locale",
    "logging", "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes",
    "mmap", "modulefinder", "multiprocessing", "netrc", "nis", "nntplib",
    "numbers", "operator", "optparse", "os", "ossaudiodev", "parser",
    "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil",
    "platform", "plistlib", "poplib", "posix", "posixpath", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr",
    "pydoc", "queue", "quopri", "random", "re", "readline", "reprlib",
    "resource", "rlcompleter", "runpy", "sched", "secrets", "select",
    "selectors", "shelve", "shlex", "shutil", "signal", "site", "smtpd",
    "smtplib", "sndhdr", "socket", "socketserver", "spwd", "sqlite3",
    "ssl", "stat", "statistics", "string", "stringprep", "struct",
    "subprocess", "sunau", "symtable", "sys", "sysconfig", "tabnanny",
    "tarfile", "telnetlib", "tempfile", "termios", "test", "textwrap",
    "threading", "time", "timeit", "tkinter", "token", "tokenize",
    "tomllib", "trace", "traceback", "tracemalloc", "tty", "turtle",
    "turtledemo", "types", "typing", "unicodedata", "unittest", "urllib",
    "uu", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser",
    "winreg", "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc",
    "zipapp", "zipfile", "zipimport", "zlib",
})


def _check_undefined_references(
    tree: ast.AST, all_names: set[str]
) -> list[dict]:
    """Check every ``Name`` node in a Load context within function bodies.
    
    Reports errors for names that are not:
    
    * a function parameter
    * a local assignment in the same function
    * a module-level name (in *all_names*)
    * a Python builtin
    
    Simple scope tracking — does not handle closures or comprehensions fully.
    """
    issues: list[dict] = []
    builtins_set: set[str] = set(dir(builtins))

    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # Parameters
        param_names: set[str] = set()
        for arg in node.args.args + node.args.kwonlyargs + node.args.posonlyargs:
            param_names.add(arg.arg)
        if node.args.vararg:
            param_names.add(node.args.vararg.arg)
        if node.args.kwarg:
            param_names.add(node.args.kwarg.arg)

        # Local Store names (assigned within the function)
        local_names: set[str] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                # Exclude the function's own name from being marked "stored"
                if child is not node:
                    local_names.add(child.id)

        known = param_names | local_names | all_names | builtins_set

        # Check every Name node in Load context
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                if child.id not in known:
                    issues.append({
                        "level": "error",
                        "check": "static_analysis",
                        "message": (
                            f"Undefined reference '{child.id}' "
                            f"at line {child.lineno}."
                        ),
                    })

    return issues


def _infer_literal_type(node: ast.AST) -> str | None:
    """Return a short type name for literal AST nodes, or ``None``."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return "str"
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            return "int"
        if isinstance(node.value, float):
            return "float"
        if isinstance(node.value, bool):
            return "bool"
        if node.value is None:
            return "NoneType"
    elif isinstance(node, ast.List):
        return "list"
    elif isinstance(node, ast.Dict):
        return "dict"
    elif isinstance(node, ast.Tuple):
        return "tuple"
    elif isinstance(node, ast.Set):
        return "set"
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return _infer_literal_type(node.operand)
    return None


_CONFLICTING_OPS: frozenset = frozenset({
    ast.Add, ast.Sub, ast.Div, ast.FloorDiv, ast.Mod,
})


def _check_type_conflicts(tree: ast.AST) -> list[dict]:
    """Flag clear type contradictions detectable from literals.
    
    Identifies:
    
    * Binary operations between incompatible literal types (e.g. ``"str" + 42``)
    * Comparisons between incompatible literal types (e.g. ``"str" == 42``)
    
    This is intentionally limited — it only catches literal-level contradictions
    and does not attempt full type inference.
    """
    issues: list[dict] = []

    for node in ast.walk(tree):
        # -- BinOp: literal-type conflicts --
        if isinstance(node, ast.BinOp):
            left_t = _infer_literal_type(node.left)
            right_t = _infer_literal_type(node.right)

            if left_t and right_t and left_t != right_t:
                # str * int is valid (repetition)
                if isinstance(node.op, ast.Mult) and {left_t, right_t} == {"str", "int"}:
                    continue
                # str % str is valid (formatting)
                if isinstance(node.op, ast.Mod) and left_t == "str" and right_t == "str":
                    continue

                op_name = type(node.op).__name__
                issues.append({
                    "level": "warn",
                    "check": "static_analysis",
                    "message": (
                        f"Type conflict: {left_t} {op_name} {right_t} "
                        f"at line {node.lineno} — incompatible operand types."
                    ),
                })

        # -- Compare: literal-type conflicts --
        if isinstance(node, ast.Compare):
            left_t = _infer_literal_type(node.left)
            for op_node, comparator in zip(node.ops, node.comparators):
                right_t = _infer_literal_type(comparator)
                if left_t and right_t and left_t != right_t:
                    op_name = type(op_node).__name__
                    issues.append({
                        "level": "warn",
                        "check": "static_analysis",
                        "message": (
                            f"Type conflict: comparing {left_t} {op_name} {right_t} "
                            f"at line {node.lineno}."
                        ),
                    })

    return issues


def check_static_analysis(skill_path: str) -> list[dict]:
    """Run all three static analysis checks across ``scripts/*.py``.
    
    Checks performed:
    
    * **Import chain** — local import resolution, name existence, circular
      imports, third-party requirements coverage.
    * **Undefined references** — names used in function bodies that are not
      parameters, locals, module-level names, or builtins.
    * **Type conflicts** — literal-level contradictions in binary operations
      and comparisons.
    
    Args:
        skill_path: Root directory of the skill.
    
    Returns:
        List of issue dicts with keys ``level``, ``check``, ``message``.
    """
    issues: list[dict] = []
    root = Path(skill_path).resolve()
    script_dir = root / "scripts"

    if not script_dir.is_dir():
        issues.append({
            "level": "warn",
            "check": "static_analysis",
            "message": "No scripts/ directory found — skipping static analysis.",
        })
        return issues

    py_files = sorted(script_dir.rglob("*.py"))
    if not py_files:
        issues.append({
            "level": "warn",
            "check": "static_analysis",
            "message": "No .py files found under scripts/ — skipping static analysis.",
        })
        return issues

    # 1. Import chain (global across all files)
    issues.extend(_check_import_chain(str(script_dir), skill_path))

    # 2. Undefined references + 3. Type conflicts (per file)
    for py_file in py_files:
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            issues.append({
                "level": "warn",
                "check": "static_analysis",
                "message": (
                    f"Syntax error in {py_file.relative_to(root)}: {exc}"
                ),
            })
            continue

        rel = str(py_file.relative_to(root))
        all_names: set[str] = _collect_module_level_names(tree)
        # Also include imported names so they aren't flagged as undefined
        for imp in _collect_imports(tree):
            if imp.get("is_from", False):
                # "from X import Y" adds Y to the local namespace
                for name in imp["names"]:
                    if name != "*":
                        all_names.add(name)
            else:
                # "import X" or "import X.Y" adds the top-level module name
                top = imp["module"].split(".")[0]
                all_names.add(top)
        issues.extend(_check_undefined_references(tree, all_names))
        issues.extend(_check_type_conflicts(tree))

    return issues



if __name__ == "__main__":
    main()
