"""Durable SYBIL exchange: atomic import, round-trip and failure preservation."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from basil.sybil import TaskRecord, TaskState
from basil.sybil_exchange import TaskExchange, dumps, loads, LegacyReconciliationRequired
from basil.sybil_store import (SybilStore, ExchangeReconciliationRequired,
                               UnpersistedClientMetadataError, CorruptStoreError)


class StoreExchangeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "state.sqlite"

    def record(self, id, title="Synthetic", state=TaskState.ACTIVE, **kwargs):
        return TaskRecord(id, title, state, **kwargs)

    def test_roundtrip_ordered_refs_partial_scores_and_proven_done(self):
        records = (
            self.record("b", "Completed", TaskState.DONE, importance=None, urgency=8,
                        source_refs=("doc:2", "doc:1", "doc:1"),
                        completion_evidence=("proof:2", "proof:1")),
            self.record("a", "Waiting", TaskState.WAITING, importance=9, urgency=None,
                        dependency_ids=("ext:2", "ext:1"), owner=None, deadline=None),
        )
        payload = dumps(TaskExchange(records))
        with SybilStore(self.path) as store:
            summary = store.import_exchange(payload)
            self.assertEqual(summary.created_ids, ("b", "a"))
            self.assertEqual(summary.unchanged_ids, ())
            exported = store.export_exchange()
            self.assertEqual(loads(exported).tasks, (records[1], records[0]))
            for task in records:
                history = store.history(task.task_id)
                self.assertEqual([e.operation for e in history], ["CREATE"])
                self.assertEqual(history[0].after, task)
                self.assertIsNone(history[0].context.actor)
        with SybilStore(self.path) as store:
            self.assertEqual(store.export_exchange(), exported)
            summary = store.import_exchange(exported)
            self.assertEqual(summary.created_ids, ())
            self.assertEqual(summary.unchanged_ids, ("a", "b"))
            self.assertEqual(len(store.history("a")), 1)
            self.assertEqual(len(store.history("b")), 1)

    def test_same_id_conflict_blocks_all_new_records_and_preserves_both(self):
        with SybilStore(self.path) as store:
            old = store.create(self.record("same", "Local"))
            history_before = store.history("same")
            new = self.record("new", "Proposed new")
            proposed = self.record("same", "Different")
            payload = dumps(TaskExchange((new, proposed)))
            with self.assertRaises(ExchangeReconciliationRequired) as err:
                store.import_exchange(payload)
            failure = err.exception
            self.assertEqual(failure.task_ids, ("same",))
            self.assertEqual(failure.original_payload, payload)
            self.assertEqual(failure.conflicts, ((old, proposed),))
            self.assertEqual(store.list(), (old,))
            self.assertEqual(store.history("same"), history_before)
            with self.assertRaises(Exception):
                store.get("new")

    def test_existing_identical_and_new_are_imported_without_touching_history(self):
        with SybilStore(self.path) as store:
            old = store.create(self.record("same"))
            store.update("same", importance=7)
            old = store.get("same")
            hist = store.history("same")
            result = store.import_exchange(dumps(TaskExchange((old, self.record("new")))))
            self.assertEqual(result.unchanged_ids, ("same",))
            self.assertEqual(result.created_ids, ("new",))
            self.assertEqual(store.history("same"), hist)
            self.assertEqual([e.operation for e in store.history("new")], ["CREATE"])

    def test_android_sidecar_rejected_without_dropping_client_fields(self):
        a = self.record("a")
        sidecar = {"a": {"project": "Client project", "nextAction": "Call",
                         "notes": "Preserve", "createdAt": 1000, "updatedAt": None,
                         "completedAt": None}}
        payload = dumps(TaskExchange((a,), sidecar))
        with SybilStore(self.path) as store:
            with self.assertRaises(UnpersistedClientMetadataError) as err:
                store.import_exchange(payload)
            self.assertEqual(err.exception.original_payload, payload)
            self.assertEqual(err.exception.task_ids, ("a",))
            self.assertEqual(store.list(), ())
            self.assertEqual(json.loads(store.export_exchange())["tasks"], [])

    def test_invalid_json_fields_duplicate_ids_and_legacy_done_never_mutate(self):
        with SybilStore(self.path) as store:
            initial = store.create(self.record("known"))
            correct = json.loads(dumps(TaskExchange((self.record("new"),))))
            duplicate = {**correct, "tasks": [correct["tasks"][0], correct["tasks"][0]]}
            unknown = {**correct, "tasks": [dict(correct["tasks"][0], importance=11)]}
            legacy = {"format": "BASIL_TASK_EXPORT", "schemaVersion": 1, "tasks": [
                {"id": "prior", "description": "Prior", "state": "DONE"}]}
            for body in ('{"format":', json.dumps(duplicate), json.dumps(unknown),
                         json.dumps(legacy)):
                with self.subTest(body=body[:80]):
                    with self.assertRaises(ValueError):
                        store.import_exchange(body)
                    self.assertEqual(store.list(), (initial,))
            with self.assertRaises(LegacyReconciliationRequired) as e:
                store.import_exchange(json.dumps(legacy))
            self.assertEqual(e.exception.task_ids, ("prior",))

    def test_export_refuses_corrupt_history_not_just_corrupt_task(self):
        with SybilStore(self.path) as store:
            store.create(self.record("a"))
        with sqlite3.connect(self.path) as db:
            db.execute("DROP TRIGGER task_history_no_update")
            db.execute("UPDATE task_history SET after_json='{}' WHERE task_id='a'")
            db.execute("""CREATE TRIGGER task_history_no_update BEFORE UPDATE ON task_history
                         BEGIN SELECT RAISE(ABORT,'SYBIL history is append-only'); END""")
        with SybilStore(self.path) as store:
            with self.assertRaises(CorruptStoreError):
                store.export_exchange()

    def test_empty_export_is_valid_and_never_deletes_existing_tasks(self):
        with SybilStore(self.path) as store:
            empty = store.export_exchange()
            self.assertEqual(loads(empty).tasks, ())
            store.create(self.record("a"))
            store.import_exchange(empty)
            self.assertEqual(tuple(x.task_id for x in store.list()), ("a",))


class CliExchangeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.directory = Path(self.folder.name)
        self.db = self.directory / "tasks.sqlite"
        self.root = Path(__file__).parents[1]
        self.environment = dict(os.environ)
        self.environment["PYTHONPATH"] = str(self.root / "src") + os.pathsep + self.environment.get("PYTHONPATH", "")

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "basil", "sybil", "--db", str(self.db),
                               *args], cwd=self.root, env=self.environment,
                              text=True, capture_output=True, timeout=15)

    def test_independent_process_export_import_reopen_idempotent(self):
        original = TaskExchange((
            TaskRecord("b", "Évidence: complete", TaskState.DONE,
                       completion_evidence=("source:⟨2⟩",), urgency=None),
            TaskRecord("a", "Follow up", TaskState.WAITING, importance=9),
        ))
        source = self.directory / "import.json"
        payload = dumps(original).replace("\n", "\r\n")
        source.write_bytes(payload.encode("utf-8"))
        first = self.run_cli("import", "--input", str(source), "--json")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(json.loads(first.stdout)["created_ids"], ["b", "a"])
        again = self.run_cli("import", "--input", str(source), "--json")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(json.loads(again.stdout)["unchanged_ids"], ["b", "a"])
        exported = self.run_cli("export")
        self.assertEqual(exported.returncode, 0, exported.stderr)
        self.assertEqual(loads(exported.stdout).tasks, tuple(sorted(original.tasks, key=lambda t: t.task_id)))
        self.assertEqual(len(json.loads(self.run_cli("history", "a", "--json").stdout)), 1)
        self.assertEqual(source.read_bytes(), payload.encode("utf-8"))

    def test_cli_conflict_fails_without_partial_import_or_input_mutation(self):
        self.assertEqual(self.run_cli("create", "existing", "--title", "Local").returncode, 0)
        exchange = dumps(TaskExchange((TaskRecord("new", "Proposed", TaskState.ACTIVE),
                                        TaskRecord("existing", "Changed", TaskState.ACTIVE))))
        input_file = self.directory / "conflict.json"
        input_file.write_bytes(exchange.encode("utf-8"))
        result = self.run_cli("import", "--input", str(input_file), "--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical conflict", result.stderr)
        self.assertEqual(input_file.read_bytes(), exchange.encode("utf-8"))
        self.assertEqual([x["task_id"] for x in json.loads(self.run_cli("list", "--json").stdout)], ["existing"])


if __name__ == "__main__":
    unittest.main()
