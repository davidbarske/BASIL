import unittest

from basil.sybil import TaskRecord, TaskState


class SybilTaskStateTests(unittest.TestCase):
    def test_unknown_priority_remains_unknown(self):
        task = TaskRecord(task_id="T1", title="Evidence not yet prioritised", state=TaskState.ACTIVE)
        self.assertIsNone(task.priority)
        self.assertIsNone(task.owner)
        self.assertIsNone(task.deadline)

    def test_importance_and_urgency_remain_separate(self):
        task = TaskRecord(
            task_id="T2",
            title="Known priority",
            state=TaskState.ACTIVE,
            importance=9,
            urgency=7,
        )
        self.assertEqual(task.importance, 9)
        self.assertEqual(task.urgency, 7)
        self.assertEqual(task.priority.matrix_priority, 2)

    def test_partial_priority_is_rejected(self):
        with self.assertRaises(ValueError):
            TaskRecord(
                task_id="T3",
                title="Incomplete classification",
                state=TaskState.ACTIVE,
                importance=9,
            )

    def test_done_requires_completion_evidence(self):
        task = TaskRecord(task_id="T4", title="Do the thing", state=TaskState.ACTIVE)
        with self.assertRaises(ValueError):
            task.transition(TaskState.DONE)
        done = task.transition(TaskState.DONE, completion_evidence=("verified output",))
        self.assertEqual(done.state, TaskState.DONE)
        self.assertEqual(done.completion_evidence, ("verified output",))

    def test_non_done_transition_does_not_invent_fields(self):
        task = TaskRecord(
            task_id="T5",
            title="Await external input",
            state=TaskState.ACTIVE,
            dependency_ids=("T9",),
            source_refs=("meeting:42",),
        )
        waiting = task.transition(TaskState.WAITING)
        self.assertEqual(waiting.dependency_ids, ("T9",))
        self.assertEqual(waiting.source_refs, ("meeting:42",))
        self.assertIsNone(waiting.owner)
        self.assertIsNone(waiting.deadline)

    def test_self_dependency_is_rejected(self):
        with self.assertRaises(ValueError):
            TaskRecord(
                task_id="T6",
                title="Impossible dependency",
                state=TaskState.BLOCKED,
                dependency_ids=("T6",),
            )


if __name__ == "__main__":
    unittest.main()
