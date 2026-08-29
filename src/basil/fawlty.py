from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class LearningRecord:
    source_component: str
    process: str
    evidence_refs: tuple[str, ...]
    lesson: str
    expected: str | None = None
    actual: str | None = None


@dataclass(frozen=True)
class ChangeProposal:
    source_record: LearningRecord
    target_component: str
    proposed_change: str
    material: bool
    approval_status: ApprovalStatus
    approval_ref: str | None = None

    @property
    def approval_gate_allows_application(self) -> bool:
        return (not self.material) or self.approval_status is ApprovalStatus.APPROVED


def _require_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def learning_record(
    *,
    source_component: str,
    process: str,
    evidence_refs: tuple[str, ...] | list[str],
    lesson: str,
    expected: str | None = None,
    actual: str | None = None,
) -> LearningRecord:
    refs = tuple(_require_text(ref, "evidence reference") for ref in evidence_refs)
    if not refs:
        raise ValueError("at least one evidence reference is required")
    return LearningRecord(
        source_component=_require_text(source_component, "source_component"),
        process=_require_text(process, "process"),
        evidence_refs=refs,
        lesson=_require_text(lesson, "lesson"),
        expected=expected.strip() if isinstance(expected, str) and expected.strip() else None,
        actual=actual.strip() if isinstance(actual, str) and actual.strip() else None,
    )


def propose_change(
    record: LearningRecord,
    *,
    target_component: str,
    proposed_change: str,
    material: bool,
) -> ChangeProposal:
    target = _require_text(target_component, "target_component")
    if not material and target.casefold() != record.source_component.casefold():
        raise ValueError("cross-component changes must be treated as material and approval-gated")
    return ChangeProposal(
        source_record=record,
        target_component=target,
        proposed_change=_require_text(proposed_change, "proposed_change"),
        material=bool(material),
        approval_status=ApprovalStatus.PENDING if material else ApprovalStatus.NOT_REQUIRED,
    )


def approve_material_change(proposal: ChangeProposal, *, approval_ref: str) -> ChangeProposal:
    if not proposal.material:
        raise ValueError("non-material local proposals do not require approval")
    return replace(
        proposal,
        approval_status=ApprovalStatus.APPROVED,
        approval_ref=_require_text(approval_ref, "approval_ref"),
    )


def reject_material_change(proposal: ChangeProposal, *, approval_ref: str) -> ChangeProposal:
    if not proposal.material:
        raise ValueError("non-material local proposals do not require approval")
    return replace(
        proposal,
        approval_status=ApprovalStatus.REJECTED,
        approval_ref=_require_text(approval_ref, "approval_ref"),
    )
