from pathlib import Path
import re
import unittest


class GrillingSkillManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path("skills/labs/grilling/SKILL.md")
        cls.text = cls.path.read_text(encoding="utf-8")

    def test_manifest_name_matches_directory(self):
        match = re.search(r"(?m)^name:\s*([^\n]+)$", self.text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), self.path.parent.name)

    def test_required_agent_skill_metadata_exists(self):
        self.assertRegex(self.text, r"(?m)^description:\s*>-")
        self.assertRegex(self.text, r"(?m)^license:\s*MIT$")
        self.assertNotRegex(self.text, r"(?m)^status:")
        self.assertNotRegex(self.text, r"(?m)^upstream:")
        self.assertNotRegex(self.text, r"(?m)^licence:")

    def test_explicit_grillme_trigger_is_discoverable(self):
        lowered = self.text.lower()
        self.assertIn('"grill me"', lowered)
        self.assertIn("grillme", lowered)
        self.assertIn("stress-test", lowered)

    def test_frontier_mechanism_and_stop_gate_are_preserved(self):
        lowered = self.text.lower()
        for term in ("decision tree", "frontier", "prerequisite", "shared understanding"):
            self.assertIn(term, lowered)


if __name__ == "__main__":
    unittest.main()
