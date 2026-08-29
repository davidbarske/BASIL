from pathlib import Path
import unittest

from basil.registry import load_capabilities


class VisualExecutionStateTests(unittest.TestCase):
    def test_visual_execution_is_canonical_without_source_recovery_inflation(self):
        by_id = {item.id: item for item in load_capabilities()}
        capability = by_id["visual.execution"]

        self.assertEqual(capability.repo_status, "canonical")
        self.assertEqual(capability.maturity, "built")
        self.assertEqual(capability.path, "docs/visual/VISUAL_EXECUTION.md")
        note = capability.note.lower()
        self.assertIn("previously deployed", note)
        self.assertIn("source has not been recovered", note)
        self.assertIn("not revalidated", note)

    def test_visual_docs_preserve_implementation_boundary(self):
        root = Path(__file__).parents[1]
        visual = (root / "docs/visual/VISUAL_EXECUTION.md").read_text(encoding="utf-8").lower()
        evidence = (root / "docs/visual/WEB_PROTOTYPE_PHASE1_EVIDENCE.md").read_text(encoding="utf-8").lower()

        self.assertIn("built / previously deployed prototype", visual)
        self.assertIn("source recovery", visual)
        self.assertIn("historical source recovery: not recovered", evidence)
        self.assertIn("do not reconstruct or fabricate", evidence)


if __name__ == "__main__":
    unittest.main()
