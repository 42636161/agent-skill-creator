"""Tests for scripts.validate — agent constraints + contract checks."""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate import check_agent_constraints, check_contract  # noqa: E402
from validate import validate_skill  # noqa: E402


class TestAgentConstraints(unittest.TestCase):
    """Tests for check_agent_constraints()."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _make_agents_md(self, content: str) -> Path:
        agents_md = self.tmp / "AGENTS.md"
        agents_md.write_text(content, encoding="utf-8")
        return agents_md

    def test_agent_constraints_present(self):
        """Valid AGENTS.md with constraints should pass."""
        content = """\
# test-skill

> A test skill.

## Purpose

Test purpose.

## Agent Constraints

1. Must NOT modify data in-place
2. Must validate all inputs before processing
3. Must NOT access external APIs without user consent
4. Must log all errors to stderr
"""
        self._make_agents_md(content)
        issues = check_agent_constraints(str(self.tmp))
        self.assertEqual(issues, [])

    def test_agent_constraints_missing(self):
        """AGENTS.md without constraints should fail."""
        content = """\
# test-skill

> A test skill.

## Purpose

Test purpose.

## Activation

This skill activates on test queries.
"""
        self._make_agents_md(content)
        issues = check_agent_constraints(str(self.tmp))
        self.assertGreater(len(issues), 0)
        self.assertIn("## Agent Constraints", issues[0]["message"])

    def test_agent_constraints_too_few(self):
        """AGENTS.md with only 1 constraint should fail."""
        content = """\
# test-skill

> A test skill.

## Agent Constraints

1. Must NOT modify data in-place
"""
        self._make_agents_md(content)
        issues = check_agent_constraints(str(self.tmp))
        self.assertGreater(len(issues), 0)
        self.assertIn("minimum 3 required", issues[0]["message"])

    def tearDown(self):
        import shutil
        shutil.rmtree(str(self.tmp), ignore_errors=True)


# ── Helpers for contract tests ────────────────────────────────────────────────


def make_skill_with_contract(
    base: Path,
    contract: dict,
    scripts_content: str | None = None,
    output_files: list[str] | None = None,
    pipeline_content: str | None = None,
) -> Path:
    """Create a minimal skill directory with contract.json and optional code."""
    skill = base / "test-contract-skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: test-contract-skill\ndescription: test\n---\n# test\n",
        encoding="utf-8",
    )
    (skill / "contract.json").write_text(
        json.dumps(contract, indent=2), encoding="utf-8"
    )
    if scripts_content:
        (skill / "scripts" / "main.py").write_text(scripts_content, encoding="utf-8")
    if pipeline_content:
        (skill / "scripts" / "run_pipeline.py").write_text(
            pipeline_content, encoding="utf-8"
        )
    for fpath in output_files or []:
        full = skill / fpath
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("placeholder", encoding="utf-8")
    return skill


# ── Contract check tests ──────────────────────────────────────────────────────


class TestCheckContractGolden(unittest.TestCase):
    """A contract that accurately describes its skill should produce zero issues."""

    def test_golden_contract(self):
        contract = {
            "input": {
                "encoding": "utf-8",
                "columns": {"name": "string", "amount": "float"},
                "file_patterns": ["*.csv"],
            },
            "output": {
                "report": {
                    "path": "output/report.json",
                    "fields": {"region": "string", "total": "float"},
                }
            },
            "dag": {
                "steps": [
                    {"name": "clean", "depends_on": [], "description": "Clean input data"},
                    {"name": "report", "depends_on": ["clean"], "description": "Generate report"},
                ]
            },
        }
        scripts_code = (
            'def clean_data(path):\n'
            '    name = ""\n'
            '    amount = 0.0\n'
            '    return {"name": name, "amount": amount}\n'
            '\n'
            'def generate_report(data):\n'
            '    region = ""\n'
            '    total = 0.0\n'
            '    return {"region": region, "total": total}\n'
        )
        pipeline_code = 'def clean(path): pass\ndef report(data): pass\ndef main(): pass\n'
        with tempfile.TemporaryDirectory() as tmp:
            skill = make_skill_with_contract(
                Path(tmp),
                contract,
                scripts_content=scripts_code,
                output_files=["output/report.json"],
                pipeline_content=pipeline_code,
            )
            issues = check_contract(str(skill))
            errors = [i for i in issues if i["level"] == "error"]
            warnings = [i for i in issues if i["level"] == "warn"]
            self.assertEqual(
                0, len(errors),
                f"Expected 0 errors in golden case, got {len(errors)}: {errors}",
            )
            self.assertEqual(
                0, len(warnings),
                f"Expected 0 warnings in golden case, got {len(warnings)}: {warnings}",
            )


class TestCheckContractMismatch(unittest.TestCase):
    """A contract that declares outputs that do not exist should produce warnings."""

    def test_missing_output_file(self):
        contract = {
            "input": {
                "encoding": "utf-8",
                "columns": {"missing_col": "string"},
            },
            "output": {
                "nonexistent_report": {
                    "path": "output/i_do_not_exist.json",
                }
            },
            "dag": {
                "steps": [
                    {"name": "process", "depends_on": [], "description": "Process data"},
                ]
            },
        }
        scripts_code = 'def process_data(): pass\n'
        with tempfile.TemporaryDirectory() as tmp:
            skill = make_skill_with_contract(
                Path(tmp), contract, scripts_content=scripts_code
            )
            issues = check_contract(str(skill))
            errors = [i for i in issues if i["level"] == "error"]
            warnings = [i for i in issues if i["level"] == "warn"]

            missing_output_warnings = [
                w for w in warnings
                if "does not exist" in w["message"] and "i_do_not_exist" in w["message"]
            ]
            self.assertGreater(
                len(missing_output_warnings), 0,
                f"Expected a warning about missing output file. Warnings: {warnings}",
            )
            missing_col_warnings = [
                w for w in warnings if "missing_col" in w["message"]
            ]
            self.assertGreater(
                len(missing_col_warnings), 0,
                f"Expected a warning about undeclared column 'missing_col'. Warnings: {warnings}",
            )
            self.assertEqual(0, len(errors), f"Expected 0 errors, got {len(errors)}: {errors}")




# -- AST check tests --------------------------------------------------------------------


class TestAstChecks(unittest.TestCase):
    """Tests for check_ast -- dead functions, dead variables, magic numbers."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "scripts").mkdir(parents=True)

    def _make_py(self, name: str, code: str) -> Path:
        py_file = self.tmp / "scripts" / name
        py_file.write_text(code, encoding="utf-8")
        return py_file

    def test_ast_dead_function(self):
        self._make_py("pipeline.py", """def helper():
    return 42

def main():
    return 1
""")
        from validate import check_ast
        issues = check_ast(str(self.tmp))
        dead_fn_issues = [i for i in issues if "Dead function" in i["message"] and "helper" in i["message"]]
        self.assertGreater(len(dead_fn_issues), 0,
                           f"Expected a dead-function warning for 'helper'. Issues: {issues}")

    def test_ast_dead_variable(self):
        self._make_py("pipeline.py", """def process():
    unused = 42
    result = 1
    return result
""")
        from validate import check_ast
        issues = check_ast(str(self.tmp))
        dead_var_issues = [i for i in issues if "Dead variable" in i["message"] and "unused" in i["message"]]
        self.assertGreater(len(dead_var_issues), 0,
                           f"Expected a dead-variable warning for 'unused'. Issues: {issues}")

    def test_ast_magic_number(self):
        self._make_py("pipeline.py", """def process():
    return 86400
""")
        from validate import check_ast
        issues = check_ast(str(self.tmp))
        magic_issues = [i for i in issues if "Magic number" in i["message"] and "86400" in i["message"]]
        self.assertGreater(len(magic_issues), 0,
                           f"Expected a magic-number warning for 86400. Issues: {issues}")

    def test_ast_clean_code_passes(self):
        self._make_py("pipeline.py", """SECONDS_IN_DAY = 86400

def helper():
    return SECONDS_IN_DAY

def main():
    x = helper()
    return x
""")
        from validate import check_ast
        issues = check_ast(str(self.tmp))
        self.assertEqual(0, len(issues), f"Expected no AST issues for clean code. Got: {issues}")

    def tearDown(self):
        import shutil
        shutil.rmtree(str(self.tmp), ignore_errors=True)


class TestStaticAnalysis(unittest.TestCase):
    """Tests for check_static_analysis -- import chain, undefined refs, type conflicts."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "scripts").mkdir(parents=True)

    def _make_py(self, name: str, code: str) -> Path:
        py_file = self.tmp / "scripts" / name
        py_file.write_text(code, encoding="utf-8")
        return py_file

    def _make_init(self, code: str = "") -> Path:
        init_file = self.tmp / "scripts" / "__init__.py"
        init_file.write_text(code, encoding="utf-8")
        return init_file

    # -- Import chain tests --

    def test_import_chain_valid(self):
        """Working local import (from scripts.utils import helper) should pass."""
        self._make_py("utils.py", "def helper():\n    return 42\n")
        self._make_py("pipeline.py", "from scripts.utils import helper\n\ndef main():\n    return helper()\n")
        from validate import check_static_analysis
        issues = check_static_analysis(str(self.tmp))
        errors = [i for i in issues if i["level"] == "error"]
        self.assertEqual(
            0, len(errors),
            f"Expected 0 errors for valid import chain, got {len(errors)}: {errors}",
        )

    def test_import_chain_broken(self):
        """Importing a nonexistent name should produce an error."""
        self._make_py("utils.py", "def helper():\n    return 42\n")
        self._make_py("pipeline.py", "from scripts.utils import nonexistent\n\ndef main():\n    return nonexistent()\n")
        from validate import check_static_analysis
        issues = check_static_analysis(str(self.tmp))
        import_errors = [i for i in issues if "does not exist" in i["message"] or "not found" in i["message"]]
        self.assertGreater(
            len(import_errors), 0,
            f"Expected an error for broken import. Issues: {issues}",
        )

    def test_import_chain_local_not_found(self):
        """Importing a module that does not exist should produce an error."""
        self._make_py("pipeline.py", "import scripts.missing_module\n\ndef main():\n    pass\n")
        from validate import check_static_analysis
        issues = check_static_analysis(str(self.tmp))
        not_found = [i for i in issues if "not found" in i["message"]]
        self.assertGreater(
            len(not_found), 0,
            f"Expected error for missing module. Issues: {issues}",
        )

    def test_import_chain_third_party_no_req(self):
        """Third-party import with no requirements.txt should warn."""
        self._make_py("pipeline.py", "import pandas\n\ndef main():\n    pass\n")
        from validate import check_static_analysis
        issues = check_static_analysis(str(self.tmp))
        req_warnings = [i for i in issues if "requirements.txt" in i["message"] and i["level"] == "warn"]
        self.assertGreater(
            len(req_warnings), 0,
            f"Expected warning about missing requirements.txt. Issues: {issues}",
        )

    def test_import_chain_third_party_not_listed(self):
        """Third-party import that is not in requirements.txt should warn."""
        self._make_py("pipeline.py", "import pandas\n\ndef main():\n    pass\n")
        (self.tmp / "requirements.txt").write_text("numpy==1.24.0\n", encoding="utf-8")
        from validate import check_static_analysis
        issues = check_static_analysis(str(self.tmp))
        req_warnings = [i for i in issues if "pandas" in i["message"] and i["level"] == "warn"]
        self.assertGreater(
            len(req_warnings), 0,
            f"Expected warning about pandas not in requirements.txt. Issues: {issues}",
        )

    def test_import_chain_third_party_listed(self):
        """Third-party import that IS listed in requirements.txt should NOT warn."""
        self._make_py("pipeline.py", "import pandas\n\ndef main():\n    pass\n")
        (self.tmp / "requirements.txt").write_text("pandas==2.0.0\n", encoding="utf-8")
        from validate import check_static_analysis
        issues = check_static_analysis(str(self.tmp))
        req_warnings = [i for i in issues if "pandas" in i["message"]]
        self.assertEqual(
            0, len(req_warnings),
            f"Expected 0 warnings about pandas, got {len(req_warnings)}: {req_warnings}",
        )

    # -- Undefined reference tests --

    def test_undefined_reference(self):
        """Using an undefined variable inside a function should error."""
        self._make_py("pipeline.py", "def process():\n    return undefined_var + 1\n")
        from validate import check_static_analysis
        issues = check_static_analysis(str(self.tmp))
        undef_errors = [i for i in issues if "Undefined reference" in i["message"] and "undefined_var" in i["message"]]
        self.assertGreater(
            len(undef_errors), 0,
            f"Expected error about undefined reference. Issues: {issues}",
        )

    def test_undefined_reference_defined_local(self):
        """A name defined locally should NOT be flagged."""
        self._make_py("pipeline.py", "def process():\n    x = 42\n    return x\n")
        from validate import check_static_analysis
        issues = check_static_analysis(str(self.tmp))
        undef_errors = [i for i in issues if "Undefined reference" in i["message"]]
        self.assertEqual(
            0, len(undef_errors),
            f"Expected 0 undefined-reference errors for local var. Issues: {issues}",
        )

    # -- Type conflict tests --

    def test_type_conflict(self):
        """str + int binary operation should produce a warning."""
        self._make_py("pipeline.py", "def merge():\n    return 'count: ' + 42\n")
        from validate import check_static_analysis
        issues = check_static_analysis(str(self.tmp))
        type_warnings = [i for i in issues if "Type conflict" in i["message"] and i["level"] == "warn"]
        self.assertGreater(
            len(type_warnings), 0,
            f"Expected type conflict warning for str + int. Issues: {issues}",
        )

    def test_type_conflict_comparison(self):
        """str == int comparison should produce a warning."""
        self._make_py("pipeline.py", "def check():\n    return 'hello' == 42\n")
        from validate import check_static_analysis
        issues = check_static_analysis(str(self.tmp))
        type_warnings = [i for i in issues if "Type conflict" in i["message"] and i["level"] == "warn"]
        self.assertGreater(
            len(type_warnings), 0,
            f"Expected type conflict warning for str == int. Issues: {issues}",
        )

    def test_type_conflict_clean_passes(self):
        """Compatible types should NOT produce type conflict warnings."""
        self._make_py("pipeline.py", "def add():\n    return 1 + 2\n")
        from validate import check_static_analysis
        issues = check_static_analysis(str(self.tmp))
        type_warnings = [i for i in issues if "Type conflict" in i["message"]]
        self.assertEqual(
            0, len(type_warnings),
            f"Expected 0 type conflict warnings for int + int. Issues: {issues}",
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(str(self.tmp), ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

class TestDescriptionFormat(unittest.TestCase):
    """Tests for _validate_description_format()."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _make_skill(self, description: str) -> Path:
        skill_dir = self.tmp / "desc-test-skill"
        skill_dir.mkdir()
        (skill_dir / "README.md").write_text("# test\n")
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            f"name: desc-test-skill\ndescription: >-\n  {description}\n"
            "license: MIT\nmetadata:\n  author: test\n  version: 1.0.0\n"
            "activation: /desc-test-skill\n"
            "---\n"
            "# /desc-test-skill\n\n"
            "## Quick Profile\n\n"
            "**Category**: transformer\n"
            "**Input**: text\n"
            "**Output**: text\n"
            "**When to use**: testing, validation\n"
            "**When not**: production\n",
            encoding="utf-8",
        )
        return skill_dir

    def _desc_error_in(self, description: str) -> bool:
        result = validate_skill(str(self._make_skill(description)))
        return any(
            "description must start with" in e for e in result.get("errors", [])
        )

    def test_a_prefix_passes(self):
        """Descriptions starting with 'A ' should pass."""
        self.assertFalse(
            self._desc_error_in("A cleaning pipeline for CRM data management."),
            "Valid 'A ...' description rejected",
        )

    def test_an_prefix_passes(self):
        """Descriptions starting with 'An ' should pass."""
        self.assertFalse(
            self._desc_error_in("An analyzer of stock price data for traders."),
            "Valid 'An ...' description rejected",
        )

    def test_no_prefix_fails(self):
        """Descriptions NOT starting with 'A ' or 'An ' should fail."""
        self.assertTrue(
            self._desc_error_in("Cleaning pipeline without article."),
            "Description without A/An should have been rejected",
        )

    def test_wrong_prefix_fails(self):
        """Descriptions starting with 'The ' should fail."""
        self.assertTrue(
            self._desc_error_in("The analyzer of stocks and trends."),
            "Description with 'The' should have been rejected",
        )
