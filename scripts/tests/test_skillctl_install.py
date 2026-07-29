import unittest
from unittest.mock import patch
from pathlib import Path
from scripts.skillctl.install import resolve_skill_entry, _detect_current_platform, resolve_install_dir
from scripts.skillctl.models import SkillEntry

class TestResolveEntry(unittest.TestCase):
    @patch("scripts.skillctl.install.load_registry")
    def test_resolve_existing(self, mock_load):
        entry = SkillEntry("test", "测试", "1.0", "描述", "repo")
        mock_load.return_value.skills = {"test": entry}
        result = resolve_skill_entry("test")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "test")

    @patch("scripts.skillctl.install.load_registry")
    def test_resolve_missing(self, mock_load):
        mock_load.return_value.skills = {}
        result = resolve_skill_entry("nonexistent")
        self.assertIsNone(result)

class TestDetectPlatform(unittest.TestCase):
    @patch("scripts.skillctl.install.Path.home")
    def test_universal_fallback(self, mock_home):
        mock_home.return_value = Path("/nonexistent")
        result = _detect_current_platform()
        self.assertEqual(result, "universal")

class TestResolveInstallDir(unittest.TestCase):
    def test_custom_dir(self):
        result = resolve_install_dir(None, "/tmp/test-install")
        self.assertEqual(result, Path("/tmp/test-install").resolve())

if __name__ == "__main__":
    unittest.main()
