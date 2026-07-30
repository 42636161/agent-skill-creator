import unittest
import argparse
from scripts.skillctl.publish import _parse_frontmatter

class TestParseFrontmatter(unittest.TestCase):
    def test_parse_simple(self):
        content = """---
name: test-skill
description: 一个测试技能
---

# 正文
"""
        result = _parse_frontmatter(content)
        self.assertEqual(result.get("name"), "test-skill")

    def test_no_frontmatter(self):
        result = _parse_frontmatter("没有 frontmatter")
        self.assertEqual(result, {})

    def test_parse_stockanalyzer_format(self):
        content = """---
name: stock-analyzer
description: >-
  Provides comprehensive technical analysis for stocks and ETFs
metadata:
  author: Alice Investor
  version: 1.2.0
---
# stock-analyzer
"""
        result = _parse_frontmatter(content)
        self.assertEqual(result.get("name"), "stock-analyzer")
        self.assertEqual(result.get("metadata", {}).get("version"), "1.2.0")
        self.assertEqual(result.get("metadata", {}).get("author"), "Alice Investor")


def test_publish_universal_skill(tmp_path):
    """Publishing a universal-mode skill should succeed with dry-run."""
    from scripts.skillctl.publish import cmd_publish

    skill_dir = tmp_path / "universal-test-skill"
    skill_dir.mkdir()
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
    (skill_dir / "scripts" / "pipeline.py").write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n")

    args = argparse.Namespace(
        skill_dir=str(skill_dir),
        org=None,
        dry_run=True,
    )
    result = cmd_publish(args)
    assert result == 0, f"Publish failed with code {result}"

if __name__ == "__main__":
    unittest.main()
