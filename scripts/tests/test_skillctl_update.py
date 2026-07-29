import unittest
from unittest.mock import patch, MagicMock
from scripts.skillctl.update import cmd_update
from scripts.skillctl.models import Registry, SkillEntry

class TestUpdate(unittest.TestCase):
    @patch("scripts.skillctl.update.load_installed")
    @patch("scripts.skillctl.update.load_registry")
    @patch("scripts.skillctl.update.save_installed")
    def test_update_check_only(self, mock_save, mock_reg, mock_inst):
        mock_inst.return_value = [
            {"name": "test-skill", "version": "1.0.0", "repo": "repo"},
        ]
        reg = Registry(skills={
            "test-skill": SkillEntry("test-skill", "测试", "2.0.0", "更新了", "repo"),
        }, categories={})
        mock_reg.return_value = reg

        args = MagicMock(name="test-skill", check=True)
        args.name = "test-skill"
        args.check = True

        result = cmd_update(args)
        self.assertEqual(result, 0)

if __name__ == "__main__":
    unittest.main()
