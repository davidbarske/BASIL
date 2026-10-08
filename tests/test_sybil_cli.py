import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


class SybilCliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "cli.sqlite"
        self.root = Path(__file__).parents[1]
        self.environment = dict(os.environ)
        self.environment["PYTHONPATH"] = str(self.root / "src") + os.pathsep + self.environment.get("PYTHONPATH", "")

    def tearDown(self):
        self.directory.cleanup()

    def invoke(self, operation, *arguments, success=True):
        # Every invocation is a completely new OS process against the same on-disk DB.
        result = subprocess.run([sys.executable, "-m", "basil", "sybil", "--db", str(self.path),
                                 operation, *arguments, "--json"], cwd=self.root, env=self.environment,
                                text=True, capture_output=True, timeout=15)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertTrue(result.stderr.strip())
        return result

    def test_full_cli_lifecycle_in_new_processes_preserves_canonical_state_and_history(self):
        self.assertEqual(self.invoke("initialise")["schema_version"], 1)
        task = self.invoke("create", "synthetic", "--title", "Synthetic commitment",
                           "--importance", "8", "--depends-on", "external:two",
                           "--depends-on", "external:one", "--source-ref", "source:two",
                           "--source-ref", "source:one")
        self.assertEqual(self.invoke("show", "synthetic"), task)
        self.assertIsNone(task["urgency"])
        self.assertIsNone(task["owner"])
        self.assertIsNone(task["deadline"])
        updated = self.invoke("update", "synthetic", "--title", "Updated commitment",
                              "--urgency", "9", "--change-source", "mutation:source")
        self.assertEqual(self.invoke("show", "synthetic"), updated)
        waiting = self.invoke("transition", "synthetic", "--state", "WAITING")
        self.assertEqual(waiting["state"], "WAITING")
        completed = self.invoke("complete", "synthetic", "--evidence", "proof:two",
                                "--evidence", "proof:one", "--actor", "explicit:test-process",
                                "--change-evidence", "mutation:proof")
        self.assertEqual(completed["state"], "DONE")
        self.assertEqual(completed["completion_evidence"], ["proof:two", "proof:one"])
        self.assertEqual(completed["dependency_ids"], ["external:two", "external:one"])
        self.assertEqual(completed["source_refs"], ["source:two", "source:one"])
        history = self.invoke("history", "synthetic")
        self.assertEqual([entry["operation"] for entry in history], ["CREATE", "UPDATE", "STATE_CHANGE", "COMPLETE"])
        self.assertIsNone(history[0]["context"]["actor"])
        self.assertIsNone(history[0]["context"]["source_refs"])
        self.assertIsNone(history[0]["context"]["evidence_refs"])
        self.assertEqual(history[1]["context"]["source_refs"], ["mutation:source"])
        self.assertEqual(history[-1]["context"]["actor"], "explicit:test-process")
        self.assertEqual(history[-1]["context"]["evidence_refs"], ["mutation:proof"])
        self.assertEqual(history[-1]["after"], completed)
        # The final two invocations again use distinct processes/connections.
        self.assertEqual(self.invoke("show", "synthetic"), completed)
        self.assertEqual(self.invoke("history", "synthetic"), history)

    def test_cli_rejects_invalid_mutations_without_state_or_history_changes(self):
        task = self.invoke("create", "T", "--title", "Synthetic")
        history = self.invoke("history", "T")
        cases = [
            ("complete", "T"),
            ("complete", "T", "--evidence", " "),
            ("transition", "T", "--state", "DONE"),
            ("transition", "T", "--state", "ARCHIVED"),
            ("update", "T", "--importance", "0"),
            ("update", "T", "--urgency", "11"),
            ("update", "T", "--urgency", "false"),
            ("update", "T", "--owner", " "),
            ("update", "T", "--deadline", " "),
            ("update", "T", "--depends-on", "T"),
            ("update", "T", "--source-ref", " "),
            ("update", "T", "--actor", " "),
            ("update", "T", "--change-evidence", " "),
            ("create", "T", "--title", "Duplicate"),
            ("create", "invalid-done", "--title", "Synthetic", "--state", "DONE"),
        ]
        for operation, *arguments in cases:
            with self.subTest(operation=operation, arguments=arguments):
                self.invoke(operation, *arguments, success=False)
                self.assertEqual(self.invoke("show", "T"), task)
                self.assertEqual(self.invoke("history", "T"), history)
        self.assertEqual(self.invoke("list"), [task])

    def test_cli_explicit_path_is_required_and_no_delete_operation_exists(self):
        for arguments in (["sybil", "list"], ["sybil", "--db", str(self.path), "delete", "T"]):
            result = subprocess.run([sys.executable, "-m", "basil", *arguments], cwd=self.root,
                env=self.environment, text=True, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 2)
            self.assertTrue(result.stderr.strip())
        self.assertFalse(self.path.exists())

    def test_cli_update_preserves_unspecified_facts_and_can_explicitly_clear(self):
        task = self.invoke("create", "T", "--title", "Synthetic", "--importance", "7",
                           "--urgency", "4", "--owner", "Explicit owner",
                           "--deadline", "opaque wording", "--depends-on", "external",
                           "--source-ref", "source")
        updated = self.invoke("update", "T", "--title", "Changed")
        self.assertEqual(updated, dict(task, title="Changed"))
        cleared = self.invoke("update", "T", "--importance", "unknown", "--clear-owner",
                              "--clear-deadline", "--clear-dependencies", "--clear-source-refs")
        self.assertIsNone(cleared["importance"])
        self.assertEqual(cleared["urgency"], 4)
        self.assertIsNone(cleared["owner"])
        self.assertIsNone(cleared["deadline"])
        self.assertEqual(cleared["dependency_ids"], [])
        self.assertEqual(cleared["source_refs"], [])

    def test_cli_cannot_remove_done_evidence_and_reports_corruption(self):
        done = self.invoke("create", "T", "--title", "Synthetic", "--state", "DONE",
                           "--completion-evidence", "proof")
        history = self.invoke("history", "T")
        self.invoke("update", "T", "--clear-completion-evidence", success=False)
        self.assertEqual(self.invoke("show", "T"), done)
        self.assertEqual(self.invoke("history", "T"), history)
        with sqlite3.connect(self.path) as connection:
            connection.execute("DELETE FROM task_references WHERE field='completion_evidence'")
        for operation, arguments in (("show", ("T",)), ("list", ()), ("update", ("T", "--title", "Must fail"))):
            result = self.invoke(operation, *arguments, success=False)
            self.assertIn("Invalid persisted SYBIL task", result.stderr)
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM task_history").fetchone()[0], 1)

    def test_cli_refuses_future_schema_and_missing_database_parent(self):
        self.invoke("initialise")
        with sqlite3.connect(self.path) as connection:
            connection.execute("PRAGMA user_version=2")
        result = self.invoke("list", success=False)
        self.assertIn("Unsupported SYBIL database schema 2", result.stderr)
        self.path = Path(self.directory.name) / "missing-parent" / "db.sqlite"
        result = self.invoke("initialise", success=False)
        self.assertIn("Unable to open SQLite database", result.stderr)
