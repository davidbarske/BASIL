import io
import json
import unittest
from contextlib import redirect_stdout

from basil.cli import main
from basil.registry import get_capability, load_capabilities, registry_schema_version


class CanonicalCutoverTests(unittest.TestCase):
    def test_no_open_repository_migration_entries_remain(self):
        items = load_capabilities()
        open_items = [item.id for item in items if item.repo_status in {"placeholder", "migrating"}]
        self.assertEqual(open_items, [])

    def test_grail_and_polly_are_canonical_without_maturity_inflation(self):
        grail = get_capability("grail.strategic-arcs")
        polly = get_capability("polly.integrations")

        self.assertEqual((grail.repo_status, grail.maturity), ("canonical", "architectural"))
        self.assertEqual((polly.repo_status, polly.maturity), ("canonical", "architectural"))
        self.assertIn("future build", grail.note.lower())
        self.assertIn("future build", polly.note.lower())

    def test_context_reports_closed_migration(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["context", "--json"])
        self.assertEqual(exit_code, 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data["open_migration_count"], 0)
        self.assertEqual(data["registry_schema_version"], registry_schema_version())
        self.assertEqual(data["core_flow"], ["MANUEL", "BRIAN", "BASIL"])
        self.assertEqual(data["registry_path"], "src/basil/data/capabilities.json")

    def test_singular_capability_lookup_is_machine_readable(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["capability", "brian.meeting-intelligence", "--json"])
        self.assertEqual(exit_code, 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data["id"], "brian.meeting-intelligence")
        self.assertEqual(data["repo_status"], "canonical")

    def test_unknown_capability_fails_cleanly(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["capability", "missing.capability"])
        self.assertEqual(exit_code, 1)
        self.assertIn("Unknown capability", output.getvalue())


if __name__ == "__main__":
    unittest.main()
