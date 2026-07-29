import unittest
from scripts.skillctl.models import Registry, SkillEntry, Category, SemanticMetadata
from scripts.skillctl.search import _entry_to_dict, semantic_search

def make_registry():
    skills = {
        "alpha": SkillEntry("alpha", "Alpha 工具", "1.0.0", "第一个工具", "repo", tags=["开发"], category="dev"),
        "beta": SkillEntry("beta", "Beta 分析器", "2.0.0", "数据分析", "repo", tags=["数据"], category="data"),
    }
    cats = {"dev": Category("dev", "开发"), "data": Category("data", "数据")}
    return Registry(skills=skills, categories=cats)

class TestList(unittest.TestCase):
    def setUp(self):
        self.reg = make_registry()

    def test_list_all(self):
        self.assertEqual(len(self.reg.skills), 2)

    def test_list_filter_by_category(self):
        filtered = [s for s in self.reg.skills.values() if s.category == "dev"]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, "alpha")

class TestEntryToDict(unittest.TestCase):
    def test_entry_dict_has_required_keys(self):
        entry = SkillEntry("test", "测试", "1.0", "描述", "repo", tags=["a"], verified=True)
        d = _entry_to_dict(entry)
        for key in ("name", "display_name", "version", "description", "tags", "verified"):
            self.assertIn(key, d)

class TestSemanticSearch(unittest.TestCase):
    def setUp(self):
        skills = {
            "fin-copilot": SkillEntry(
                "fin-copilot", "金融副驾", "1.0", "金融分析", "repo",
                tags=["股票", "交易"],
                semantic=SemanticMetadata(
                    intents=["分析股票技术指标", "生成交易信号", "查看 RSI 和 MACD"]
                ),
            ),
            "crm-report": SkillEntry(
                "crm-report", "CRM 报表", "2.0", "CRM", "repo",
                tags=["crm", "销售"],
            ),
        }
        self.reg = Registry(skills=skills, categories={})

    def test_exact_intent_match_zh(self):
        results = semantic_search(self.reg, "分析股票技术指标")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "fin-copilot")

    def test_partial_match(self):
        results = semantic_search(self.reg, "RSI")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "fin-copilot")

    def test_tag_fallback(self):
        results = semantic_search(self.reg, "股票")
        self.assertEqual(len(results), 1)

    def test_no_match(self):
        results = semantic_search(self.reg, "完全无关")
        self.assertEqual(len(results), 0)

    def test_multiple_results_ordered(self):
        self.reg.skills["analysis-tool"] = SkillEntry(
            "analysis-tool", "分析工具", "1.0", "工具", "repo",
            tags=["分析", "交易"],
            semantic=SemanticMetadata(intents=["对数据执行分析", "生成分析报告"]),
        )
        results = semantic_search(self.reg, "交易 信号 分析", top_k=3)
        self.assertGreaterEqual(len(results), 2)

if __name__ == "__main__":
    unittest.main()
