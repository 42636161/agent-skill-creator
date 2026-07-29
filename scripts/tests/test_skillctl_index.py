import unittest
from scripts.skillctl.index import search_registry
from scripts.skillctl.models import Registry, SkillEntry, Category

def make_test_registry() -> Registry:
    """创建含示例技能的测试用 Registry"""
    skills = {
        "alice-financial-copilot": SkillEntry(
            name="alice-financial-copilot",
            display_name="Alice 金融副驾",
            version="1.2.0",
            description="基于 RSI、MACD 的技术分析",
            repo="https://github.com/agent-skills/alice-financial-copilot",
            tags=["股票", "买卖", "技术分析"],
            category="financial",
        ),
        "weekly-crm-report": SkillEntry(
            name="weekly-crm-report",
            display_name="每周 CRM 报表",
            version="2.0.0",
            description="销售数据清洗和区域汇总",
            repo="https://github.com/agent-skills/weekly-crm-report",
            tags=["crm", "销售", "报表"],
            category="crm",
        ),
    }
    categories = {
        "financial": Category("financial", "金融分析", "市场数据相关技能"),
        "crm": Category("crm", "销售 & CRM", "CRM 技能"),
    }
    return Registry(skills=skills, categories=categories)

class TestSearch(unittest.TestCase):
    def setUp(self):
        self.registry = make_test_registry()

    def test_search_by_name(self):
        results = search_registry(self.registry, "alice")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "alice-financial-copilot")

    def test_search_by_tag(self):
        results = search_registry(self.registry, "技术分析")
        self.assertEqual(len(results), 1)

    def test_search_by_description(self):
        results = search_registry(self.registry, "RSI")
        self.assertEqual(len(results), 1)

    def test_search_no_match(self):
        results = search_registry(self.registry, "不存在")
        self.assertEqual(len(results), 0)

if __name__ == "__main__":
    unittest.main()
