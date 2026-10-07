from dataclasses import replace
import json
from pathlib import Path
import unittest

from basil.sybil import TaskRecord, TaskState
from basil.sybil_exchange import (TaskExchange, LegacyReconciliationRequired,
                                  dumps, loads, task_from_dict, task_to_dict)

FIXTURES = Path("fixtures/sybil")


class SybilExchangeTests(unittest.TestCase):
    def test_shared_fixture_exact_roundtrip_all_states(self):
        original = json.loads((FIXTURES / "canonical-v1.json").read_text())
        exchange = loads(json.dumps(original))
        self.assertEqual(original, json.loads(dumps(exchange)))
        self.assertEqual({t.state for t in exchange.tasks}, set(TaskState))
        active, waiting, monitor, blocked, scheduled, done = exchange.tasks
        self.assertIsNone(active.importance)
        self.assertIsNone(active.urgency)
        self.assertEqual(waiting.importance, 9)
        self.assertIsNone(waiting.urgency)
        self.assertIsNone(waiting.priority)
        self.assertIsNone(monitor.importance)
        self.assertEqual(monitor.urgency, 7)
        self.assertIsNone(monitor.priority)
        self.assertEqual(scheduled.priority.matrix_priority, 2)
        self.assertEqual(blocked.dependency_ids, ("active", "external:synthetic"))
        self.assertEqual(blocked.source_refs, ("meeting:synthetic-1", "decision:synthetic-2"))
        self.assertEqual(done.completion_evidence, ("artifact:synthetic-verified",))
        for task in exchange.tasks:
            self.assertEqual(task, task_from_dict(task_to_dict(task)))

    def test_done_validation_at_every_python_object_boundary(self):
        active = TaskRecord("T", "Task", TaskState.ACTIVE)
        for evidence in ((), ("",), (" \t\n",), ("valid", " "), "text", (False,)):
            with self.subTest(evidence=evidence):
                for build in (lambda: TaskRecord("T", "Task", TaskState.DONE, completion_evidence=evidence),
                              lambda: replace(active, state=TaskState.DONE, completion_evidence=evidence),
                              lambda: active.transition(TaskState.DONE, completion_evidence=evidence)):
                    with self.assertRaises((ValueError, TypeError)):
                        build()
        done = active.transition(TaskState.DONE, completion_evidence=("proof:1",))
        self.assertEqual(done.state, TaskState.DONE)

    def test_typed_state_required_even_with_valid_evidence(self):
        for state in ("DONE", "ACTIVE", "CANCELLED", "done", 1, None):
            with self.subTest(state=state), self.assertRaises(ValueError):
                TaskRecord("T", "Task", state, completion_evidence=("proof:1",))
            with self.assertRaises(ValueError):
                TaskRecord("T", "Task", TaskState.ACTIVE).transition(state)
        with self.assertRaises(ValueError):
            TaskState("ARCHIVED")

    def test_reference_collections_are_defensive_and_validated(self):
        source = ["source:1"]
        task = TaskRecord("T", "Task", TaskState.ACTIVE, source_refs=source)
        source.clear()
        self.assertEqual(task.source_refs, ("source:1",))
        for field, value in (("dependency_ids", ["T"]), ("dependency_ids", [" "]),
                             ("source_refs", [""]), ("source_refs", "plain text")):
            with self.assertRaises(ValueError):
                replace(task, **{field: value})

    def test_bad_canonical_payloads_fail(self):
        original = json.loads((FIXTURES / "canonical-v1.json").read_text())
        for field, value in (("state", "DELETED"), ("state", 1), ("importance", True),
                             ("importance", "9"), ("urgency", 11), ("urgency", 9.5),
                             ("source_refs", [False]), ("owner", 7), ("deadline", " "),
                             ("title", False), ("dependency_ids", "D")):
            data = json.loads(json.dumps(original))
            data["tasks"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises((ValueError, TypeError)):
                loads(json.dumps(data))
        for evidence in ([], [""], [" "], ["valid", " "]):
            data = json.loads(json.dumps(original))
            data["tasks"][0].update(state="DONE", completion_evidence=evidence)
            with self.assertRaises(ValueError):
                loads(json.dumps(data))

    def test_duplicate_ids_and_invalid_schema_rejected(self):
        original = json.loads((FIXTURES / "canonical-v1.json").read_text())
        original["tasks"].append(original["tasks"][0])
        with self.assertRaisesRegex(ValueError, "duplicate task IDs"):
            loads(json.dumps(original))
        for version in (True, 2, "1"):
            original["schema_version"] = version
            with self.assertRaises(ValueError):
                loads(json.dumps(original))
        with self.assertRaises(ValueError):
            loads('{"format":"BASIL_SYBIL_TASKS","schema_version":1,"schema_version":2,"tasks":[]}')
        with self.assertRaises(ValueError):
            loads('{"format":"BASIL_SYBIL_TASKS","schema_version":1,"tasks":[],"extra":1}')

    def test_unknowns_and_permissive_non_done_transitions(self):
        task = TaskRecord("T", "Task", TaskState.ACTIVE)
        for state in TaskState:
            if state is not TaskState.DONE:
                task = task.transition(state)
                self.assertEqual(task.state, state)
                self.assertIsNone(task.importance)
                self.assertIsNone(task.urgency)
                self.assertIsNone(task.owner)
                self.assertIsNone(task.deadline)
        done = task.transition(TaskState.DONE, completion_evidence=("proof",))
        self.assertEqual(done.transition(TaskState.MONITOR).completion_evidence, ())

    def test_serialization_revalidates_tampered_objects_and_metadata(self):
        task = TaskRecord("T", "Task", TaskState.DONE, completion_evidence=("proof",))
        object.__setattr__(task, "completion_evidence", ())
        with self.assertRaises(ValueError):
            task_to_dict(task)
        original = json.loads((FIXTURES / "canonical-v1.json").read_text())
        original["android_v01"]["active"]["createdAt"] = True
        with self.assertRaises(ValueError):
            loads(json.dumps(original))

    def test_legacy_migration_preserves_exact_client_data(self):
        old = (FIXTURES / "android-v01.json").read_text()
        expected = json.loads((FIXTURES / "android-v01-expected.json").read_text())
        self.assertEqual(expected, json.loads(dumps(loads(old))))
        self.assertEqual(expected, json.loads(dumps(loads(dumps(loads(old))))))

    def test_legacy_unproved_done_retains_original_payload(self):
        old = json.loads((FIXTURES / "android-v01.json").read_text())
        old["tasks"][0].update(state="DONE", completedAt=1700000001000)
        original = json.dumps(old, indent=2)
        with self.assertRaises(LegacyReconciliationRequired) as result:
            loads(original)
        self.assertEqual(result.exception.task_ids, ("legacy-task",))
        self.assertEqual(result.exception.original_payload, original)
        old["tasks"][0]["completionEvidence"] = ["proof:legacy"]
        self.assertEqual(loads(json.dumps(old)).tasks[0].state, TaskState.DONE)
        old["tasks"][0]["completionEvidence"] = [" "]
        with self.assertRaises(ValueError):
            loads(json.dumps(old))

    def test_android_origin_fixture_decodes_and_roundtrips(self):
        original = json.loads((FIXTURES / "android-origin.json").read_text())
        self.assertEqual(original, json.loads(dumps(loads(json.dumps(original)))))
