from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

import basil


ROOT = Path(__file__).resolve().parents[1]


class MilestoneOneTests(unittest.TestCase):
    def test_core_and_package_versions_match_milestone(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        self.assertEqual("0.2.0", basil.__version__)
        self.assertEqual("0.2.0", project["version"])

    def test_milestone_record_exists(self) -> None:
        text = (ROOT / "docs/status/MILESTONE_1_CANONICAL_BASELINE_2026-08-29.md").read_text(encoding="utf-8")
        self.assertIn("Status:** ACHIEVED", text)
        self.assertIn("Baseline version:** 0.2.0", text)
        self.assertIn("migration programme is closed", text)


if __name__ == "__main__":
    unittest.main()
