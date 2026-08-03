#!/usr/bin/env python3
"""
Post-generation skill evaluator. Scores a generated skill against the test_spec.json
criteria for its test case. Designed to be run AFTER the creator has generated a skill.

Usage:
    python3 tests/retail_skills/score_skill.py <case_id> <path/to/generated/skill/>
    python3 tests/retail_skills/score_skill.py a1 outputs/store-daily-report-skill/
    python3 tests/retail_skills/score_skill.py --all outputs/   # scores all generated skills

Output: JSON scorecard + human-readable summary.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CREATOR_ROOT = SCRIPT_DIR.parent.parent  # agent-skill-creator repo root


def load_spec():
    with open(SCRIPT_DIR / "test_spec.json") as f:
        return json.load(f)


def run_validate(skill_path: str) -> dict:
    """Run creator's validate.py and return results."""
    validate_py = CREATOR_ROOT / "scripts" / "validate.py"
    result = subprocess.run(
        ["python3", str(validate_py), skill_path, "--json"],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"errors": [], "warnings": [], "_raw": result.stdout[:500]}


def run_security(skill_path: str) -> dict:
    """Run creator's security_scan.py and return results."""
    sec_py = CREATOR_ROOT / "scripts" / "security_scan.py"
    result = subprocess.run(
        ["python3", str(sec_py), skill_path, "--json"],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"findings": [], "_raw": result.stdout[:500]}


def run_check_pipeline(skill_path: str) -> dict:
    """Run check_pipeline.py if it exists."""
    cp = CREATOR_ROOT / "scripts" / "check_pipeline.py"
    if not cp.exists():
        return {"status": "skipped", "reason": "check_pipeline.py not found"}
    result = subprocess.run(
        ["python3", str(cp), skill_path],
        capture_output=True, text=True, timeout=60
    )
    return {"exit_code": result.returncode, "stderr": result.stderr[:500]}


def scan_file_structure(skill_path: str) -> dict:
    """Check file inventory for known anti-patterns."""
    p = Path(skill_path)
    all_files = list(p.rglob("*"))
    rel_files = [str(f.relative_to(p)) for f in all_files if f.is_file()]

    has_api_guide = any("api-guide" in f.lower() for f in rel_files)
    has_wrappers = any(f.endswith((".sh", ".ps1", ".bat")) for f in rel_files if not f.startswith("scripts/"))
    has_evolution = "EVOLUTION.md" in rel_files
    markdown_count = len([f for f in rel_files if f.endswith(".md")])

    # Check for references proliferation
    refs_md = [f for f in rel_files if f.startswith("references/") and f.endswith(".md")]

    # Check SKILL.md line count
    skill_md = p / "SKILL.md"
    skill_lines = 0
    if skill_md.exists():
        skill_lines = len(skill_md.read_text(encoding="utf-8").splitlines())

    return {
        "total_files": len(rel_files),
        "has_api_guide": has_api_guide,
        "has_bash_wrappers": has_wrappers,
        "has_evolution_md": has_evolution,
        "markdown_count": markdown_count,
        "reference_md_files": refs_md,
        "skill_md_lines": skill_lines,
    }


def check_output_quality(skill_path: str, case_spec: dict) -> dict:
    """Heuristic checks on generated output quality."""
    p = Path(skill_path)
    checks = {}

    # Check SKILL.md for Runtime Contract or reading rules
    skill_md = p / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8")
        checks["has_runtime_contract"] = bool(re.search(
            r"(?i)(runtime.contract|reading.rules|how to run|不读.scripts|don't read.scripts)", content))
        checks["has_executive_summary_section"] = bool(re.search(
            r"(?i)(本周结论|executive.summary|摘要)", content))

    # Check AGENTS.md for dispatch card pattern (≤25 lines ideal)
    agents_md = p / "AGENTS.md"
    if agents_md.exists():
        agents_lines = len(agents_md.read_text(encoding="utf-8").splitlines())
        checks["agents_md_lines"] = agents_lines
        checks["agents_is_dispatch_card"] = agents_lines <= 30
    else:
        checks["agents_md_lines"] = 0
        checks["agents_is_dispatch_card"] = None  # no AGENTS.md at all

    # Check if report output is human-readable (not raw JSON-only)
    pipeline_py = p / "scripts" / "pipeline.py"
    run_pipeline_py = p / "scripts" / "run_pipeline.py"
    main_py = pipeline_py if pipeline_py.exists() else run_pipeline_py
    if main_py.exists():
        code = main_py.read_text(encoding="utf-8")
        checks["has_json_output_option"] = "--json" in code
        checks["has_human_readable_stdout"] = bool(re.search(
            r"(print.*summary|print.*摘要|print.*结论|📊|✓.*report|report.*generated)", code, re.I))

    # Check SKILL.md description for Chinese keywords (if case involves Chinese)
    if skill_md.exists():
        fm = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if fm:
            desc = fm.group(1)
            checks["description_has_chinese"] = bool(re.search(r"[\u4e00-\u9fff]", desc))

    return checks


def check_architecture(skill_path: str, expected: str) -> dict:
    """Check if architecture matches expectation (simple vs complex_suite)."""
    p = Path(skill_path)
    is_suite = False
    sub_skills = []

    # Suites have subdirectories each with their own SKILL.md
    # Check up to 3 levels deep (e.g., components/sales-achievement/SKILL.md)
    for d in p.iterdir():
        if d.is_dir() and (d / "SKILL.md").exists():
            sub_skills.append(d.name)
        elif d.is_dir() and d.name in ("components", "sub_skills", "skills"):
            for sd in d.iterdir():
                if sd.is_dir() and (sd / "SKILL.md").exists():
                    sub_skills.append(sd.name)

    if len(sub_skills) > 1:
        is_suite = True
    elif len(sub_skills) == 1 and sub_skills[0] != ".":
        # Might be a suite with one sub-skill
        is_suite = True

    correct = (expected == "complex_suite" and is_suite) or (expected == "simple" and not is_suite)

    return {
        "detected_architecture": "complex_suite" if is_suite else "simple",
        "expected_architecture": expected,
        "correct": correct,
        "sub_skills_found": sub_skills,
    }


def check_anti_patterns(skill_path: str, anti_patterns: list, case_spec: dict) -> list:
    """Check for specific anti-patterns."""
    p = Path(skill_path)
    findings = []

    all_text = ""
    for f in p.rglob("*"):
        if f.is_file() and f.suffix in (".py", ".md", ".json", ".csv", ".txt"):
            try:
                all_text += f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass

    # API guide anti-pattern
    if any("api-guide" in ap.lower() for ap in anti_patterns):
        api_guide = p / "references" / "api-guide.md"
        if api_guide.exists():
            findings.append("ANTI: generated references/api-guide.md when no API needed")

    # Raw data dump anti-pattern
    if any("outputs raw" in ap.lower() or "data table" in ap.lower() for ap in anti_patterns):
        report_md = p / "report.md"
        if report_md.exists():
            first_lines = "\n".join(report_md.read_text(encoding="utf-8").splitlines()[:5])
            # Check if report starts with a table (markdown table has |---| pattern early)
            if re.search(r"\|.*\|.*\n\|[-\s|]+\|", first_lines):
                findings.append("ANTI: report.md starts with data table instead of summary")

    # No baseline logic — check for baseline, pre/during pairs, before/after patterns
    if any("without baseline" in ap.lower() for ap in anti_patterns):
        pipeline_files = list(p.rglob("pipeline.py")) + list(p.rglob("analyze.py")) + list(p.rglob("main.py"))
        has_baseline = False
        for pf in pipeline_files:
            code = pf.read_text(encoding="utf-8", errors="ignore")
            code_lower = code.lower()
            if "baseline" in code_lower:
                has_baseline = True
                break
            # Also check for pre/during comparison patterns
            if ("pre" in code_lower and "during" in code_lower and
                any(op in code_lower for op in ["/ pre", "/pre", "- pre", "-pre"])):
                has_baseline = True
                break
            if ("before" in code_lower and "after" in code_lower and
                any(op in code_lower for op in ["/ before", "/before", "- before", "-before"])):
                has_baseline = True
                break
        if not has_baseline:
            findings.append("ANTI: no baseline computation logic found in code")

    # Hardcoded commission rules — exclude parser functions
    if any("hardcodes" in ap.lower() and "commission" in ap.lower() for ap in anti_patterns):
        pipeline_files = list(p.rglob("*.py"))
        for pf in pipeline_files:
            code = pf.read_text(encoding="utf-8", errors="ignore")
            hardcoded_found = False
            for line in code.splitlines():
                if re.search(r"(店长.*0\.\d+%|commission.*=\s*0\.\d+)", line):
                    # Exclude lines that are part of a rule parser or zero-value initialization
                    if not re.search(r"(parse_rules|re\.search|re\.finditer|re\.match|re\.compile|read_text|open\(.*rules)", line):
                        # Skip pure initialization: "commission = 0.0" (not a hardcoded rule)
                        if not re.search(r"commission\s*=\s*0\.?0*\s*$", line):
                            hardcoded_found = True
                            break
            if hardcoded_found:
                findings.append("ANTI: commission rules appear hardcoded in Python instead of read from file")
                break

    return findings


def score_case(case_spec: dict, skill_path: str) -> dict:
    """Full evaluation of one generated skill against its test case."""
    print(f"\n{'='*60}")
    print(f"Scoring [{case_spec['id']}] {case_spec['name']}")
    print(f"  Skill path: {skill_path}")

    scorecard = {
        "case_id": case_spec["id"],
        "skill_path": skill_path,
        "scores": {},
        "findings": [],
        "overall_grade": "pending",
    }

    # 1. Validate
    print("  [1/6] validate.py ...", end=" ")
    v = run_validate(skill_path)
    errors = v.get("errors", [])
    warnings = v.get("warnings", [])
    scorecard["validate"] = {
        "pass": len(errors) == 0,
        "errors_count": len(errors),
        "warnings_count": len(warnings),
        "errors": errors[:5],
        "warnings": warnings[:5],
    }
    print(f"{'PASS' if len(errors)==0 else 'FAIL'} ({len(errors)} errors, {len(warnings)} warnings)")

    # 2. Security
    print("  [2/6] security_scan.py ...", end=" ")
    s = run_security(skill_path)
    findings_s = s.get("findings", [])
    scorecard["security"] = {
        "pass": len(findings_s) == 0,
        "findings_count": len(findings_s),
        "high_severity": [f for f in findings_s if f.get("severity") == "high"],
    }
    print(f"{'PASS' if len(findings_s)==0 else 'FAIL'} ({len(findings_s)} findings)")

    # 3. File structure
    print("  [3/6] File structure ...", end=" ")
    fs = scan_file_structure(skill_path)
    scorecard["file_structure"] = fs
    issues = []
    if fs["has_api_guide"]:
        issues.append("api-guide exists")
    if fs["has_bash_wrappers"]:
        issues.append("bash wrappers present")
    if fs["has_evolution_md"]:
        issues.append("EVOLUTION.md in delivery")
    if fs["skill_md_lines"] > 500:
        issues.append(f"SKILL.md is {fs['skill_md_lines']} lines (>500)")
    print(f"{len(issues)} issues" if issues else "clean")
    scorecard["file_structure"]["issues"] = issues

    # 4. Architecture
    print("  [4/6] Architecture check ...", end=" ")
    arch = check_architecture(skill_path, case_spec["expected_architecture"])
    scorecard["architecture"] = arch
    print(f"{'CORRECT' if arch['correct'] else 'WRONG'} (expected {arch['expected_architecture']}, got {arch['detected_architecture']})")

    # 5. Output quality heuristics
    print("  [5/6] Output quality ...", end=" ")
    oq = check_output_quality(skill_path, case_spec)
    scorecard["output_quality"] = oq
    q_issues = []
    if oq.get("has_runtime_contract") is False:
        q_issues.append("no runtime contract")
    if oq.get("has_executive_summary_section") is False and "report" in case_spec.get("name", "").lower():
        q_issues.append("no executive summary pattern")
    if oq.get("agents_is_dispatch_card") is False and oq.get("agents_md_lines", 0) > 30:
        q_issues.append(f"AGENTS.md too long ({oq['agents_md_lines']} lines)")
    print(f"{len(q_issues)} issues" if q_issues else "good")
    scorecard["output_quality"]["issues"] = q_issues

    # 6. Anti-pattern check
    print("  [6/6] Anti-pattern scan ...", end=" ")
    ap_findings = check_anti_patterns(skill_path, case_spec.get("anti_patterns", []), case_spec)
    scorecard["anti_patterns"] = ap_findings
    print(f"{len(ap_findings)} found" if ap_findings else "clean")

    # Compute overall grade
    total_checks = 6
    passed = 0
    if scorecard["validate"]["pass"]: passed += 1
    if scorecard["security"]["pass"]: passed += 1
    if not scorecard["file_structure"]["issues"]: passed += 1
    if scorecard["architecture"]["correct"]: passed += 1
    if not scorecard["output_quality"]["issues"]: passed += 1
    if not scorecard["anti_patterns"]: passed += 1

    grades = {6: "A", 5: "B", 4: "C", 3: "D", 2: "E", 1: "F", 0: "F"}
    scorecard["overall_grade"] = grades.get(passed, "F")
    scorecard["checks_passed"] = f"{passed}/{total_checks}"

    return scorecard


def print_scorecard(sc: dict):
    """Pretty-print a scorecard."""
    print(f"\n{'─'*60}")
    print(f"SCORECARD: [{sc['case_id']}] Grade: {sc['overall_grade']} ({sc['checks_passed']})")
    print(f"{'─'*60}")
    print(f"  Validate:    {'✓' if sc['validate']['pass'] else '✗'} ({sc['validate']['errors_count']}E, {sc['validate']['warnings_count']}W)")
    print(f"  Security:    {'✓' if sc['security']['pass'] else '✗'} ({sc['security']['findings_count']} findings)")
    print(f"  Files:       {'✓' if not sc['file_structure']['issues'] else '✗'} {sc['file_structure']['issues']}")
    print(f"  Architecture:{'✓' if sc['architecture']['correct'] else '✗'} (expected {sc['architecture']['expected_architecture']}, got {sc['architecture']['detected_architecture']})")
    print(f"  Output Qual: {'✓' if not sc['output_quality'].get('issues') else '✗'} {sc['output_quality'].get('issues', [])}")
    print(f"  Anti-patterns: {'✓' if not sc['anti_patterns'] else '✗'} {sc['anti_patterns']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 score_skill.py <case_id> <skill_path>")
        print("       python3 score_skill.py --all <outputs_dir/>")
        print("\nCases: a1 a2 a3 b4 b5 b6 c7 c8 d9 d10 e11 e12")
        sys.exit(1)

    spec = load_spec()

    if sys.argv[1] == "--all":
        outputs_dir = Path(sys.argv[2])
        all_scorecards = []
        for case in spec["cases"]:
            cid = case["id"]
            # Try to find matching skill dir
            matches = list(outputs_dir.glob(f"*{cid}*"))
            if not matches:
                # Try by expected name
                matches = list(outputs_dir.glob(case["expected_skill_name"] + "*"))
            if not matches:
                print(f"  ⚠ No skill found for {cid}, skipping")
                continue
            sc = score_case(case, str(matches[0]))
            all_scorecards.append(sc)

        # Summary
        print(f"\n{'='*60}")
        print("AGGREGATE RESULTS")
        print(f"{'='*60}")
        grades = [s["overall_grade"] for s in all_scorecards]
        print(f"  Total scored: {len(all_scorecards)}")
        print(f"  A: {grades.count('A')}  B: {grades.count('B')}  C: {grades.count('C')}  D-F: {grades.count('D')+grades.count('E')+grades.count('F')}")
        for sc in all_scorecards:
            print(f"  [{sc['case_id']}] {sc['overall_grade']}  {sc['case_id']}")

        # Save full results
        out_json = outputs_dir / "score_results.json"
        with open(out_json, "w") as f:
            json.dump(all_scorecards, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nFull results saved to {out_json}")

    else:
        case_id = sys.argv[1]
        skill_path = sys.argv[2]
        case_spec = next((c for c in spec["cases"] if c["id"] == case_id), None)
        if not case_spec:
            print(f"Unknown case: {case_id}")
            sys.exit(1)
        sc = score_case(case_spec, skill_path)
        print_scorecard(sc)

# ── Step 7: Holdout data test (NEW) ─────────────────────────────────────

HOLDOUT_DIR = SCRIPT_DIR / "data_test"

HOLDOUT_MAP = {
    "a1": {"file": "门店销售_202608.xlsx", "edges": ["门店销售_仅销售sheet.xlsx", "门店销售_空退货sheet.xlsx"]},
    "a3": {"file": "金蝶_导出_202608.csv", "edges": ["金蝶_缺列.csv", "金蝶_混合日期格式.csv"]},
    "b4": {"file": "promo_events_august.csv", "edges": []},
    "b5": {"file": "product_performance_august.csv", "edges": []},
    "b6": {"file": "transactions_august.csv", "edges": []},
    "c7": {"file": "sales_target_august.csv", "edges": ["sales_target_缺门店.csv"]},
    "c8": {"file": "foot_traffic_august.csv", "edges": ["foot_traffic_仅周末.csv"]},
    "d9": {"file": "sku_sales_august.csv", "edges": []},
    "e11": {"file": "employees_august.csv", "edges": []},
    "e12": {"file": "store_sales_august.csv", "edges": []},
}

def run_skill_on_holdout(skill_path: str, case_id: str) -> dict:
    """Run the generated skill's pipeline on holdout data and check results."""
    if case_id not in HOLDOUT_MAP:
        return {"status": "skipped", "reason": f"no holdout data for {case_id}"}

    info = HOLDOUT_MAP[case_id]
    holdout_file = HOLDOUT_DIR / case_id / info["file"]
    edge_files = [HOLDOUT_DIR / case_id / e for e in info.get("edges", [])]

    if not holdout_file.exists():
        return {"status": "skipped", "reason": f"holdout file missing: {holdout_file}"}

    result = {
        "status": "pending",
        "holdout_file": str(holdout_file),
        "clean_run": None,
        "edge_runs": [],
        "output_files": [],
        "errors": [],
    }

    skill_p = Path(skill_path)

    # Find the pipeline entry point
    pipeline_candidates = [
        skill_p / "scripts" / "pipeline.py",
        skill_p / "scripts" / "run_pipeline.py",
        skill_p / "scripts" / "main.py",
        skill_p / "run.py",
    ]
    pipeline = None
    for pc in pipeline_candidates:
        if pc.exists():
            pipeline = pc
            break

    if not pipeline:
        # Look for any .py with pipeline in the name
        for pf in skill_p.rglob("*.py"):
            if "pipeline" in pf.name.lower():
                pipeline = pf
                break

    if not pipeline:
        result["status"] = "no_pipeline_found"
        result["errors"].append("No pipeline.py or run_pipeline.py found in skill")
        return result

    # Try to run the skill with the holdout file
    out_dir = Path(skill_path) / "_test_output"
    out_dir.mkdir(exist_ok=True)

    cmd = ["python3", str(pipeline), "--input", str(holdout_file),
           "--output", str(out_dir)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        result["clean_run"] = {
            "exit_code": proc.returncode,
            "stdout_tail": proc.stdout[-500:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-500:] if proc.stderr else "",
        }
        if proc.returncode == 0:
            result["status"] = "clean_run_ok"
        else:
            result["status"] = "clean_run_failed"
            result["errors"].append(f"Pipeline exit code {proc.returncode}")

        # Check what output files were produced
        if out_dir.exists():
            result["output_files"] = [str(f.relative_to(out_dir)) for f in out_dir.rglob("*") if f.is_file()]
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["errors"].append("Pipeline timed out (60s)")
    except Exception as e:
        result["status"] = "exception"
        result["errors"].append(str(e))

    # Check output quality heuristics
    result["output_checks"] = {}
    if result.get("output_files"):
        # Check if report has executive summary
        report_candidates = [f for f in result["output_files"] if "report" in f.lower() and f.endswith(".md")]
        for rc in report_candidates:
            rp = out_dir / rc
            if rp.exists():
                first_lines = rp.read_text(encoding="utf-8", errors="ignore")[:300]
                result["output_checks"]["report_starts_with_summary"] = not re.search(
                    r"^\s*\|.*\|", first_lines)  # not starting with a table
                result["output_checks"]["report_has_chinese"] = bool(re.search(r"[\u4e00-\u9fff]", first_lines))

        # Check JSON output has summary fields
        json_candidates = [f for f in result["output_files"] if f.endswith(".json")]
        for jc in json_candidates:
            jp = out_dir / jc
            if jp.exists():
                try:
                    data = json.loads(jp.read_text())
                    result["output_checks"]["json_has_summary"] = "summary" in data or "highlights" in data
                except Exception:
                    pass

        # Check if stdout is human-readable (not just JSON dump)
        if result["clean_run"] and result["clean_run"]["stdout_tail"]:
            stdout = result["clean_run"]["stdout_tail"]
            result["output_checks"]["stdout_not_raw_json"] = not (
                stdout.strip().startswith("{") or stdout.strip().startswith("["))

    # Cleanup
    import shutil
    if out_dir.exists():
        shutil.rmtree(out_dir)

    return result

# Patch score_case to include step 7
_original_score_case = score_case

def score_case_with_holdout(case_spec: dict, skill_path: str) -> dict:
    sc = _original_score_case(case_spec, skill_path)

    # Step 7: Holdout test
    print("  [7/7] Holdout data test ...", end=" ")
    ho = run_skill_on_holdout(skill_path, case_spec["id"])
    sc["holdout_test"] = ho

    if ho["status"] == "clean_run_ok":
        # Check output quality
        oq = ho.get("output_checks", {})
        issues = []
        if oq.get("report_starts_with_summary") is False:
            issues.append("report starts with data table, not summary")
        if oq.get("stdout_not_raw_json") is False:
            issues.append("stdout is raw JSON dump")
        if issues:
            sc["holdout_test"]["output_issues"] = issues
            print(f"run OK but {len(issues)} output issues")
        else:
            print("run OK, output quality good")
    elif ho["status"] == "clean_run_failed":
        print(f"FAIL (exit {ho['clean_run']['exit_code']})")
    else:
        print(f"{ho['status']}")

    # Recalculate grade with 7 dimensions
    total_checks = 7
    passed = 0
    if sc["validate"]["pass"]: passed += 1
    if sc["security"]["pass"]: passed += 1
    if not sc["file_structure"]["issues"]: passed += 1
    if sc["architecture"]["correct"]: passed += 1
    if not sc["output_quality"].get("issues"): passed += 1
    if not sc["anti_patterns"]: passed += 1
    if ho["status"] == "clean_run_ok" and not ho.get("output_issues"): passed += 1

    grades = {7:"A+", 6:"A", 5:"B", 4:"C", 3:"D", 2:"E", 1:"F", 0:"F"}
    sc["overall_grade"] = grades.get(passed, "F")
    sc["checks_passed"] = f"{passed}/{total_checks}"

    return sc

# Override
score_case = score_case_with_holdout
