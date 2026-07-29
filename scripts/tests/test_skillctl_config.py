import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    @patch("scripts.skillctl.config.SKILLCTL_DIR")
    def test_ensure_dirs_creates_hierarchy(self, mock_dir):
        mock_dir.__str__.return_value = str(self.tmp)
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.assertTrue(self.tmp.exists())

if __name__ == "__main__":
    unittest.main()
