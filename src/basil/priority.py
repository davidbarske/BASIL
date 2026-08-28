from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ImportanceBand(str, Enum):
    CRITICAL = "Critical"
    IMPORTANT = "Important"
    RELEVANT = "Relevant"


class UrgencyBand(str, Enum):
    IMMEDIATE = "Immediate"
    PRESSING = "Pressing"
    PENDING = "Pending"


@dataclass(frozen=True)
class PriorityResult:
    importance_score: int
    urgency_score: int
    importance: ImportanceBand
    urgency: UrgencyBand
    matrix_priority: int


_PRIORITY_MATRIX: dict[tuple[ImportanceBand, UrgencyBand], int] = {
    (ImportanceBand.CRITICAL, UrgencyBand.IMMEDIATE): 1,
    (ImportanceBand.CRITICAL, UrgencyBand.PRESSING): 2,
    (ImportanceBand.CRITICAL, UrgencyBand.PENDING): 5,
    (ImportanceBand.IMPORTANT, UrgencyBand.IMMEDIATE): 3,
    (ImportanceBand.IMPORTANT, UrgencyBand.PRESSING): 4,
    (ImportanceBand.IMPORTANT, UrgencyBand.PENDING): 7,
    (ImportanceBand.RELEVANT, UrgencyBand.IMMEDIATE): 6,
    (ImportanceBand.RELEVANT, UrgencyBand.PRESSING): 8,
    (ImportanceBand.RELEVANT, UrgencyBand.PENDING): 9,
}


def _validate_score(score: int, label: str) -> int:
    if isinstance(score, bool) or not isinstance(score, int):
        raise TypeError(f"{label} must be an integer from 1 to 10")
    if not 1 <= score <= 10:
        raise ValueError(f"{label} must be between 1 and 10")
    return score


def importance_band(score: int) -> ImportanceBand:
    score = _validate_score(score, "importance")
    if score >= 9:
        return ImportanceBand.CRITICAL
    if score >= 6:
        return ImportanceBand.IMPORTANT
    return ImportanceBand.RELEVANT


def urgency_band(score: int) -> UrgencyBand:
    score = _validate_score(score, "urgency")
    if score >= 9:
        return UrgencyBand.IMMEDIATE
    if score >= 6:
        return UrgencyBand.PRESSING
    return UrgencyBand.PENDING


def classify_priority(importance_score: int, urgency_score: int) -> PriorityResult:
    importance_score = _validate_score(importance_score, "importance")
    urgency_score = _validate_score(urgency_score, "urgency")
    importance = importance_band(importance_score)
    urgency = urgency_band(urgency_score)
    return PriorityResult(
        importance_score=importance_score,
        urgency_score=urgency_score,
        importance=importance,
        urgency=urgency,
        matrix_priority=_PRIORITY_MATRIX[(importance, urgency)],
    )
