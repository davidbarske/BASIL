import dataclasses
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch

from basil.sybil import TaskRecord, TaskState
from basil.sybil_exchange import TASK_FIELDS, loads, task_to_dict
from basil.sybil_store import (SCHEMA, SCHEMA_VERSION, CorruptStoreError, DuplicateTaskError,
    MutationContext, SybilStore, SybilStoreError, TaskNotFoundError, UnsupportedSchemaError)


class SybilStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "sybil.sqlite"
        self.store = SybilStore(self.path)

    def tearDown(self):
        self.store.close()
        self.directory.cleanup()

    def task(self, task_id="T", **changes):
        return dataclasses.replace(TaskRecord(task_id, "Synthetic commitment", TaskState.ACTIVE), **changes)

    def raw(self, sql, values=()):
        with sqlite3.connect(self.path) as connection:
            connection.execute("PRAGMA ignore_check_constraints=ON")
            return connection.execute(sql, values).fetchall()

    def test_schema_initialise_and_supported_reopen_are_idempotent(self):
        self.store.initialise()
        self.assertEqual(self.raw("PRAGMA user_version"), [(SCHEMA_VERSION,)])
        self.assertEqual(self.store.list(), ())
        self.store.create(self.task())
        self.store.close()
        with SybilStore(self.path) as reopened:
            reopened.initialise()
            self.assertEqual(reopened.get("T"), self.task())
            self.assertEqual(len(reopened.history("T")), 1)

    def test_future_and_unknown_versions_refuse_without_alteration(self):
        for version in (2, -1):
            path = Path(self.directory.name) / f"unsupported-{version}.sqlite"
            with sqlite3.connect(path) as connection:
                connection.execute(f"PRAGMA user_version={version}")
                connection.execute("CREATE TABLE preserved(value TEXT)")
                connection.execute("INSERT INTO preserved VALUES('synthetic')")
            before = path.read_bytes()
            with self.assertRaises(UnsupportedSchemaError):
                SybilStore(path)
            self.assertEqual(path.read_bytes(), before)

    def test_unversioned_nonempty_database_is_not_claimed_or_modified(self):
        path = Path(self.directory.name) / "unrelated.sqlite"
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE unrelated(value TEXT)")
        before = path.read_bytes()
        with self.assertRaises(UnsupportedSchemaError):
            SybilStore(path)
        self.assertEqual(path.read_bytes(), before)

    def test_schema_initialisation_failure_rolls_back_tables_and_version(self):
        path = Path(self.directory.name) / "failed-init.sqlite"
        with patch("basil.sybil_store.SCHEMA", SCHEMA[:1] + ("NOT SQL",)):
            with self.assertRaises(SybilStoreError):
                SybilStore(path)
        with sqlite3.connect(path) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)
            self.assertEqual(connection.execute(
                "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall(), [])

    def test_schema_with_missing_history_guards_is_refused(self):
        self.store.close()
        self.raw("DROP TRIGGER task_history_no_delete")
        with self.assertRaises(CorruptStoreError):
            SybilStore(self.path)

    def test_four_priority_knowledge_cases_and_deterministic_list(self):
        tasks = [self.task("D", importance=8, urgency=9), self.task("B", importance=8),
                 self.task("C", urgency=9), self.task("A")]
        for task in tasks:
            self.store.create(task)
        self.store.close()
        with SybilStore(self.path) as reopened:
            actual = reopened.list()
            self.assertEqual(actual, tuple(sorted(tasks, key=lambda item: item.task_id)))
            self.assertTrue(all(task.priority is None for task in actual[:3]))
            self.assertEqual(actual[3].priority, tasks[0].priority)
            self.assertIsNotNone(actual[3].priority)

    def test_shared_canonical_fixture_has_lossless_storage_without_client_metadata(self):
        fixture = Path(__file__).parents[1] / "fixtures/sybil/canonical-v1.json"
        exchange = loads(fixture.read_text(encoding="utf-8"))
        for task in exchange.tasks:
            self.store.create(task)
        self.store.close()
        with SybilStore(self.path) as reopened:
            for task in exchange.tasks:
                self.assertEqual(task_to_dict(reopened.get(task.task_id)), task_to_dict(task))
            self.assertEqual({task.state for task in reopened.list()}, set(TaskState))
        columns = {row[1] for row in self.raw("PRAGMA table_info(tasks)")}
        self.assertEqual(columns, set(TASK_FIELDS) - {
            "dependency_ids", "source_refs", "completion_evidence"})
        self.assertFalse({"project", "nextAction", "notes", "updatedAt"} & columns)

    def test_full_on_disk_restart_update_transition_complete_history_lifecycle(self):
        # New connection/store at every stage, never an in-memory database.
        unknown = self.task("unknown")
        partial = self.task("partial", importance=8, owner="Explicit synthetic owner",
            deadline="opaque deadline wording", dependency_ids=("unknown", "external"),
            source_refs=("source:second", "source:first"))
        self.store.create(unknown)
        self.store.create(partial)
        self.store.close()
        with SybilStore(self.path) as reopened:
            self.assertEqual(reopened.get("unknown"), unknown)
            self.assertEqual(reopened.get("partial"), partial)
            updated = reopened.update("partial", title="Updated synthetic commitment", urgency=9)
        with SybilStore(self.path) as reopened:
            self.assertEqual(reopened.get("partial"), updated)
            self.assertEqual([entry.operation for entry in reopened.history("partial")], ["CREATE", "UPDATE"])
            waiting = reopened.transition("partial", TaskState.WAITING)
        with SybilStore(self.path) as reopened:
            self.assertEqual(reopened.get("partial"), waiting)
            self.assertEqual(reopened.history("partial")[-1].after.state, TaskState.WAITING)
            done = reopened.complete("partial", ("proof:second", "proof:first"),
                context=MutationContext(actor="explicit:test-process", evidence_refs=("mutation:proof",)))
        with SybilStore(self.path) as reopened:
            self.assertEqual(reopened.get("partial"), done)
            self.assertEqual(done.state, TaskState.DONE)
            self.assertEqual(done.completion_evidence, ("proof:second", "proof:first"))
            self.assertEqual(done.dependency_ids, partial.dependency_ids)
            self.assertEqual(done.source_refs, partial.source_refs)
            history = reopened.history("partial")
            self.assertEqual([entry.operation for entry in history],
                             ["CREATE", "UPDATE", "STATE_CHANGE", "COMPLETE"])
            self.assertEqual(history[0].after, partial)
            self.assertEqual(history[1].before, partial)
            self.assertEqual(history[1].after, updated)
            self.assertEqual(history[2].before, updated)
            self.assertEqual(history[3].before, waiting)
            self.assertEqual(history[-1].after, done)
            self.assertEqual(history[-1].context.evidence_refs, ("mutation:proof",))
            self.assertEqual(reopened.get("unknown"), unknown)
            self.assertEqual(len(reopened.history("unknown")), 1)

    def test_create_and_update_history_fields_are_exact(self):
        task = self.store.create(self.task())
        creation = self.store.history("T")[0]
        self.assertIsNone(creation.before)
        self.assertEqual(creation.after, task)
        self.assertEqual(creation.changed_fields, TASK_FIELDS)
        after = self.store.update("T", owner="Explicit owner", importance=6,
                                  source_refs=("s:two", "s:one"))
        history = self.store.history("T")
        self.assertEqual(history[-1].operation, "UPDATE")
        self.assertEqual(history[-1].before, task)
        self.assertEqual(history[-1].after, after)
        self.assertEqual(history[-1].changed_fields, ("importance", "owner", "source_refs"))
        self.assertLess(history[0].history_id, history[1].history_id)
        self.assertTrue(history[-1].recorded_at.endswith("+00:00"))

    def test_history_context_is_separate_known_only_and_defensively_copied(self):
        refs, proofs = ["mutation:source"], ["mutation:evidence"]
        context = MutationContext("explicit:test-process", refs, proofs)
        self.store.create(self.task(source_refs=("canonical:source",)), context=context)
        refs.clear()
        proofs.clear()
        self.store.update("T", title="Changed")
        self.store.close()
        with SybilStore(self.path) as reopened:
            history = reopened.history("T")
            self.assertEqual(history[0].context, MutationContext(
                "explicit:test-process", ("mutation:source",), ("mutation:evidence",)))
            self.assertEqual(history[0].after.source_refs, ("canonical:source",))
            self.assertEqual(history[1].context, MutationContext())
            self.assertIsNone(history[1].context.actor)
            self.assertIsNone(history[1].context.source_refs)
            self.assertIsNone(history[1].context.evidence_refs)

    def test_history_values_and_sql_guards_are_append_preserving(self):
        self.store.create(self.task())
        history = self.store.history("T")
        self.assertIsInstance(history, tuple)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            history[0].operation = "UPDATE"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            history[0].after.title = "Changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            history[0].context.actor = "Invented"
        for sql in ("UPDATE task_history SET operation='UPDATE'", "DELETE FROM task_history"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.raw(sql)
        self.assertEqual(self.store.history("T"), history)
        self.assertFalse(hasattr(self.store, "delete"))

    def test_noop_update_or_transition_creates_no_false_mutation(self):
        task = self.store.create(self.task())
        before = self.store.history("T")
        self.assertEqual(self.store.update("T"), task)
        self.assertEqual(self.store.update("T", title=task.title), task)
        self.assertEqual(self.store.transition("T", TaskState.ACTIVE), task)
        self.assertEqual(self.store.history("T"), before)

    def test_permissive_non_done_transitions_and_reopening_preserve_domain_rule(self):
        self.store.create(self.task())
        for state in TaskState:
            if state is not TaskState.DONE:
                self.assertEqual(self.store.transition("T", state).state, state)
        self.store.complete("T", ("proof",))
        after = self.store.transition("T", TaskState.MONITOR)
        self.assertEqual(after.completion_evidence, ())
        entry = self.store.history("T")[-1]
        self.assertEqual(entry.operation, "STATE_CHANGE")
        self.assertEqual(entry.before.state, TaskState.DONE)
        self.assertEqual(entry.after.state, TaskState.MONITOR)

    def test_invalid_completion_and_raw_states_leave_task_and_history_unchanged(self):
        task = self.store.create(self.task())
        history = self.store.history("T")
        for evidence in ((), (" ",), ("proof", "\t"), "proof", (7,)):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                self.store.complete("T", evidence)
        for state in ("DONE", "ACTIVE", "UNKNOWN", None):
            with self.subTest(state=state), self.assertRaises(ValueError):
                self.store.transition("T", state, completion_evidence=("proof",))
        with self.assertRaises(ValueError):
            self.store.transition("T", TaskState.DONE)
        self.assertEqual(self.store.get("T"), task)
        self.assertEqual(self.store.history("T"), history)
        self.assertEqual(self.store.transition("T", TaskState.DONE, completion_evidence=("proof",)).state,
                         TaskState.DONE)
        self.assertEqual(self.store.history("T")[-1].operation, "COMPLETE")

    def test_tampered_direct_done_creation_is_revalidated_before_storage(self):
        for changes in ({"state": "DONE"}, {"state": TaskState.DONE},
                        {"state": TaskState.DONE, "completion_evidence": (" ",)}):
            task = self.task()
            for key, value in changes.items():
                object.__setattr__(task, key, value)
            with self.assertRaises(ValueError):
                self.store.create(task)
            self.assertEqual(self.store.list(), ())
            self.assertEqual(self.raw("SELECT * FROM task_history"), [])

    def test_invalid_updates_or_context_cannot_create_history(self):
        task = self.store.create(self.task())
        history = self.store.history("T")
        changes = [{"importance": 0}, {"importance": True}, {"importance": 2.5},
                   {"urgency": 11}, {"urgency": "8"}, {"owner": " "}, {"owner": 7},
                   {"deadline": []}, {"deadline": " "}, {"title": ""},
                   {"dependency_ids": ("T",)}, {"dependency_ids": (" ",)},
                   {"source_refs": ("s", "")}, {"completion_evidence": "proof"},
                   {"completion_evidence": (None,)}, {"state": TaskState.DONE}, {"id": "new"}]
        for change in changes:
            # The established canonical score validator distinguishes type from range errors.
            expected_error = TypeError if any(
                name in change and type(change[name]) is not int
                for name in ("importance", "urgency")
            ) else ValueError
            with self.subTest(change=change), self.assertRaises(expected_error):
                self.store.update("T", **change)
        for args in ({"actor": " "}, {"source_refs": ("",)}, {"evidence_refs": "reference"}):
            with self.assertRaises(ValueError):
                MutationContext(**args)
        self.assertEqual(self.store.get("T"), task)
        self.assertEqual(self.store.history("T"), history)

    def test_done_evidence_cannot_be_removed_through_update(self):
        task = self.store.create(self.task(state=TaskState.DONE, completion_evidence=("proof:one", "proof:two")))
        history = self.store.history("T")
        for evidence in ((), (" ",), ("proof", "")):
            with self.assertRaises(ValueError):
                self.store.update("T", completion_evidence=evidence)
        self.assertEqual(self.store.get("T"), task)
        self.assertEqual(self.store.history("T"), history)

    def test_ordered_collections_empty_values_and_updates_survive_restart(self):
        task = self.task(dependency_ids=("z", "a", "z"), source_refs=("s:two", "s:one"))
        self.store.create(task)
        self.store.complete("T", ("e:two", "e:one", "e:two"))
        self.store.close()
        with SybilStore(self.path) as reopened:
            actual = reopened.get("T")
            self.assertEqual(actual.dependency_ids, task.dependency_ids)
            self.assertEqual(actual.source_refs, task.source_refs)
            self.assertEqual(actual.completion_evidence, ("e:two", "e:one", "e:two"))
            cleared = reopened.update("T", dependency_ids=(), source_refs=())
        with SybilStore(self.path) as reopened:
            self.assertEqual(reopened.get("T"), cleared)
            self.assertEqual(reopened.get("T").dependency_ids, ())
            self.assertEqual(reopened.get("T").source_refs, ())

    def test_duplicate_create_preserves_original_state_and_history(self):
        task = self.store.create(self.task())
        history = self.store.history("T")
        with self.assertRaises(DuplicateTaskError):
            self.store.create(self.task(title="Conflicting replacement"))
        self.assertEqual(self.store.get("T"), task)
        self.assertEqual(self.store.history("T"), history)

    def test_task_write_success_history_sql_failure_rolls_back_create(self):
        self.raw("""CREATE TRIGGER reject_history BEFORE INSERT ON task_history
                    BEGIN SELECT RAISE(ABORT,'synthetic history failure'); END""")
        with self.assertRaises(SybilStoreError):
            self.store.create(self.task(source_refs=("s:one", "s:two")))
        self.assertEqual(self.store.list(), ())
        self.assertEqual(self.raw("SELECT * FROM task_references"), [])
        self.assertEqual(self.raw("SELECT * FROM task_history"), [])

    def test_task_update_success_history_sql_failure_rolls_back_every_field(self):
        task = self.store.create(self.task(source_refs=("old:one", "old:two")))
        history = self.store.history("T")
        self.raw("""CREATE TRIGGER reject_history BEFORE INSERT ON task_history
                    BEGIN SELECT RAISE(ABORT,'synthetic history failure'); END""")
        with self.assertRaises(SybilStoreError):
            self.store.update("T", title="Changed", source_refs=("new:one", "new:two"))
        self.assertEqual(self.store.get("T"), task)
        self.assertEqual(self.store.history("T"), history)

    def test_reference_sql_failure_leaves_no_half_written_collections(self):
        task = self.store.create(self.task(source_refs=("old:one", "old:two")))
        history = self.store.history("T")
        self.raw("""CREATE TRIGGER reject_reference BEFORE INSERT ON task_references
                    WHEN NEW.reference='new:two'
                    BEGIN SELECT RAISE(ABORT,'synthetic reference failure'); END""")
        with self.assertRaises(SybilStoreError):
            self.store.update("T", title="Changed", source_refs=("new:one", "new:two", "new:three"))
        self.assertEqual(self.store.get("T"), task)
        self.assertEqual(self.store.history("T"), history)

    def test_interrupted_transaction_rolls_back_before_any_history_is_appended(self):
        task = self.store.create(self.task(source_refs=("old",)))
        history = self.store.history("T")
        with patch.object(self.store, "_append_history", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.store.update("T", source_refs=("new:one", "new:two"))
        self.assertEqual(self.store.get("T"), task)
        self.assertEqual(self.store.history("T"), history)

    def test_corrupt_canonical_rows_fail_loudly_without_mutation_or_history(self):
        cases = [
            ("UPDATE tasks SET state='DONE'", ()),
            ("UPDATE tasks SET state='NOT_A_STATE'", ()),
            ("UPDATE tasks SET importance=99", ()),
            ("UPDATE tasks SET urgency=2.5", ()),
            ("UPDATE tasks SET owner=' '", ()),
            ("UPDATE tasks SET deadline=' '", ()),
            ("INSERT INTO task_references VALUES('T','dependency_ids',0,'T')", ()),
            ("INSERT INTO task_references VALUES('T','source_refs',0,' ')", ()),
            ("INSERT INTO task_references VALUES('T','source_refs',2,'gap')", ()),
            ("INSERT INTO task_references VALUES('T','invalid_field',0,'ref')", ()),
            ("INSERT INTO task_references VALUES('T','source_refs',0,?)", (b"not text",)),
        ]
        self.store.close()
        for index, (sql, values) in enumerate(cases):
            with self.subTest(sql=sql):
                path = Path(self.directory.name) / f"corrupt-{index}.sqlite"
                with SybilStore(path) as store:
                    store.create(self.task())
                with sqlite3.connect(path) as connection:
                    connection.execute("PRAGMA ignore_check_constraints=ON")
                    connection.execute(sql, values)
                    before = connection.execute("SELECT * FROM task_history").fetchall()
                    tasks = connection.execute("SELECT * FROM tasks").fetchall()
                    refs = connection.execute("SELECT * FROM task_references").fetchall()
                with SybilStore(path) as reopened:
                    for operation in (lambda: reopened.get("T"), reopened.list,
                                      lambda: reopened.update("T", title="Must fail"),
                                      lambda: reopened.complete("T", ("proof",)),
                                      lambda: reopened.history("T")):
                        with self.assertRaises(CorruptStoreError):
                            operation()
                with sqlite3.connect(path) as connection:
                    self.assertEqual(connection.execute("SELECT * FROM tasks").fetchall(), tasks)
                    self.assertEqual(connection.execute("SELECT * FROM task_references").fetchall(), refs)
                    self.assertEqual(connection.execute("SELECT * FROM task_history").fetchall(), before)

    def test_corrupt_history_cannot_be_exposed_or_extended(self):
        self.store.create(self.task())
        self.raw("DROP TRIGGER task_history_no_update")
        self.raw("UPDATE task_history SET changed_fields_json=?", ('["state"]',))
        # Existing connection also validates history before extending a task.
        with self.assertRaises(CorruptStoreError):
            self.store.history("T")
        with self.assertRaises(CorruptStoreError):
            self.store.update("T", title="Must fail")
        self.assertEqual(self.store.get("T"), self.task())
        self.assertEqual(len(self.raw("SELECT * FROM task_history")), 1)

    def test_explicit_empty_context_is_distinct_from_unknown_context(self):
        self.store.create(self.task(), context=MutationContext(source_refs=(), evidence_refs=()))
        self.store.update("T", title="Changed")
        history = self.store.history("T")
        self.assertEqual(history[0].context.source_refs, ())
        self.assertEqual(history[0].context.evidence_refs, ())
        self.assertIsNone(history[1].context.source_refs)
        self.assertIsNone(history[1].context.evidence_refs)

    def test_two_store_writers_serialize_read_modify_write_without_lost_fields(self):
        self.store.create(self.task())
        barrier = threading.Barrier(2)
        def writer(changes):
            with SybilStore(self.path) as store:
                barrier.wait(timeout=5)
                return store.update("T", **changes)
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(writer, {"owner": "Explicit owner"}),
                       executor.submit(writer, {"title": "Concurrent synthetic update"})]
            for future in futures:
                future.result(timeout=10)
        actual = self.store.get("T")
        self.assertEqual(actual.owner, "Explicit owner")
        self.assertEqual(actual.title, "Concurrent synthetic update")
        self.assertEqual([entry.operation for entry in self.store.history("T")], ["CREATE", "UPDATE", "UPDATE"])

    def test_missing_tasks_closed_store_and_explicit_path_are_clear_failures(self):
        for operation in (lambda: self.store.get("missing"), lambda: self.store.update("missing", title="x"),
                          lambda: self.store.transition("missing", TaskState.MONITOR),
                          lambda: self.store.history("missing")):
            with self.assertRaises(TaskNotFoundError):
                operation()
        with self.assertRaises(TypeError):
            SybilStore()
        with self.assertRaises(ValueError):
            SybilStore(" ")
        self.store.close()
        self.store.close()
        with self.assertRaises(SybilStoreError):
            self.store.list()
