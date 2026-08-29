from pathlib import Path
import re
import unittest


class CeoReviewSkillManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path("skills/labs/ceo-review/SKILL.md")
        cls.text = cls.path.read_text(encoding="utf-8")

    def test_manifest_name_matches_directory(self):
        match = re.search(r"(?m)^name:\s*([^\n]+)$", self.text)
        self.assertIsNotNone(match)
        self.assertEqual(self.path.parent.name, match.group(1).strip())

    def test_agent_skill_metadata_is_portable(self):
        self.assertRegex(self.text, r"(?m)^description:\s*>-")
        self.assertRegex(self.text, r"(?m)^license:\s*MIT$")
        self.assertRegex(self.text, r"(?m)^metadata:")
        self.assertNotRegex(self.text, r"(?m)^status:")
        self.assertNotRegex(self.text, r"(?m)^owner:")
        self.assertNotRegex(self.text, r"(?m)^licence:")

    def test_ask_the_ceo_trigger_is_discoverable(self):
        lowered = self.text.lower()
        self.assertIn("ask the ceo", lowered)
        self.assertIn("ceo review", lowered)

    def test_four_scope_postures_are_preserved(self):
        for posture in ("EXPAND", "SELECTIVE EXPANSION", "HOLD", "REDUCE"):
            self.assertIn(posture, self.text)

    def test_runtime_binding_is_not_overclaimed(self):
        lowered = self.text.lower()
        self.assertIn("invocation binding not yet reliable", lowered)
        self.assertIn("not yet been demonstrated reliably", lowered)


if __name__ == "__main__":
    unittest.main()
