from pathlib import Path
import unittest


class FawltyArchaeologyProvenanceTests(unittest.TestCase):
    def test_pilot_remains_archaeology_not_promoted_learning(self):
        root = Path(__file__).parents[1]
        text = (root / "docs/learning/FAWLTY_ARCHAEOLOGY_PILOT_PROVENANCE.md").read_text(encoding="utf-8").lower()

        self.assertIn("working pilot — archaeology phase active", text)
        self.assertIn("historical findings promoted to current basil", text)
        self.assertIn("none", text)
        self.assertIn("discovery before learning", text)
        self.assertIn("material change", text)
        self.assertIn("explicit approval", text)

    def test_public_record_keeps_private_corpus_out_of_github(self):
        root = Path(__file__).parents[1]
        text = (root / "docs/learning/FAWLTY_ARCHAEOLOGY_PILOT_PROVENANCE.md").read_text(encoding="utf-8").lower()

        self.assertIn("full archaeology corpus remains in drive", text)
        self.assertIn("inappropriate for a public source repository", text)
        self.assertIn("excludes those secrets from propagation", text)


if __name__ == "__main__":
    unittest.main()
