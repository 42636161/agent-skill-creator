"""Tests for scripts.platforms — the canonical install-target registry.

The registry is the single source of truth for platform install paths; the
unified `skillctl` CLI consumes it at install time. These tests assert the
registry itself is well-formed (no duplicates, complete paths, round-trips).
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from platforms import PLATFORMS, get_platform, list_supported_platforms  # noqa: E402


class RegistrySanityTest(unittest.TestCase):
    def test_at_least_one_platform(self) -> None:
        self.assertGreater(len(PLATFORMS), 0)

    def test_names_unique(self) -> None:
        names = [p.name for p in PLATFORMS]
        self.assertEqual(len(names), len(set(names)))

    def test_get_platform_round_trip(self) -> None:
        for p in PLATFORMS:
            self.assertEqual(get_platform(p.name), p)

    def test_unknown_returns_none(self) -> None:
        self.assertIsNone(get_platform("does-not-exist"))

    def test_user_and_project_paths_non_empty(self) -> None:
        for p in PLATFORMS:
            self.assertTrue(p.user_path, f"{p.name} missing user_path")
            self.assertTrue(p.project_path, f"{p.name} missing project_path")


if __name__ == "__main__":
    unittest.main()
