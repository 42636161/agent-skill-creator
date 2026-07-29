import unittest
from scripts.skillctl.models import SkillEntry, SemanticMetadata, Author

class TestSkillEntry(unittest.TestCase):
    def test_minimal_skill_entry(self):
        s = SkillEntry("test", "Test Skill", "1.0.0", "A test", "https://github.com/agent-skills/test")
        self.assertEqual(s.name, "test")
        self.assertEqual(s.version, "1.0.0")

    def test_skill_entry_with_semantic(self):
        sm = SemanticMetadata(intents=["分析数据"])
        s = SkillEntry("ds", "数据技能", "1.0.0", "数据处理", "repo", semantic=sm)
        self.assertIn("分析数据", s.semantic.intents)

    def test_author_fields(self):
        a = Author("Alice", "https://github.com/alice")
        self.assertEqual(a.name, "Alice")

if __name__ == "__main__":
    unittest.main()
