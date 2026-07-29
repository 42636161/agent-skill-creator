import unittest
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

if __name__ == "__main__":
    unittest.main()
