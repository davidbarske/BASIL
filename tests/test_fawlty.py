import unittest

from basil.fawlty import (
    ApprovalStatus,
    approve_material_change,
    learning_record,
    propose_change,
    reject_material_change,
)


class FawltyLearningTests(unittest.TestCase):
    def test_learning_record_requires_evidence(self):
        with self.assertRaises(ValueError):
            learning_record(
                source_component="SYBIL",
                process="task close",
                evidence_refs=(),
                lesson="A useful lesson",
            )

    def test_prediction_and_actual_can_be_preserved(self):
        record = learning_record(
            source_component="BRIAN",
            process="meeting analysis",
            evidence_refs=("evidence:meeting-001",),
            lesson="Prediction calibration matters",
            expected="low interruption rate",
            actual="high interruption rate",
        )
        self.assertEqual(record.expected, "low interruption rate")
        self.assertEqual(record.actual, "high interruption rate")

    def test_material_change_is_blocked_pending_approval(self):
        record = learning_record(
            source_component="FAWLTY",
            process="calibration review",
            evidence_refs=("evidence:run-001",),
            lesson="Method needs adjustment",
        )
        proposal = propose_change(
            record,
            target_component="BRIAN",
            proposed_change="Change the default evaluation procedure",
            material=True,
        )
        self.assertEqual(proposal.approval_status, ApprovalStatus.PENDING)
        self.assertFalse(proposal.can_apply)

    def test_material_change_requires_explicit_approval_reference(self):
        record = learning_record(
            source_component="FAWLTY",
            process="calibration review",
            evidence_refs=("evidence:run-002",),
            lesson="A material correction is warranted",
        )
        proposal = propose_change(
            record,
            target_component="SYBIL",
            proposed_change="Alter task-state behaviour",
            material=True,
        )
        approved = approve_material_change(proposal, approval_ref="operator:decision-001")
        self.assertEqual(approved.approval_status, ApprovalStatus.APPROVED)
        self.assertTrue(approved.can_apply)
        self.assertEqual(approved.approval_ref, "operator:decision-001")

    def test_rejected_material_change_remains_blocked(self):
        record = learning_record(
            source_component="FAWLTY",
            process="calibration review",
            evidence_refs=("evidence:run-003",),
            lesson="Proposal was considered",
        )
        proposal = propose_change(
            record,
            target_component="MANUEL",
            proposed_change="Alter evidence establishment rules",
            material=True,
        )
        rejected = reject_material_change(proposal, approval_ref="operator:decision-002")
        self.assertEqual(rejected.approval_status, ApprovalStatus.REJECTED)
        self.assertFalse(rejected.can_apply)

    def test_non_material_local_change_does_not_require_approval(self):
        record = learning_record(
            source_component="MANUEL",
            process="processor close",
            evidence_refs=("evidence:run-004",),
            lesson="Improve local diagnostic wording",
        )
        proposal = propose_change(
            record,
            target_component="MANUEL",
            proposed_change="Clarify a local diagnostic message",
            material=False,
        )
        self.assertEqual(proposal.approval_status, ApprovalStatus.NOT_REQUIRED)
        self.assertTrue(proposal.can_apply)


if __name__ == "__main__":
    unittest.main()
