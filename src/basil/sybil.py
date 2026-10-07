from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from basil.priority import PriorityResult, classify_priority, importance_band, urgency_band


class TaskState(str, Enum):
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    SCHEDULED = "SCHEDULED"
    BLOCKED = "BLOCKED"
    MONITOR = "MONITOR"
    DONE = "DONE"


def nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonblank text")
    return value


def references(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError(f"{label} must be a list/tuple of references")
    return tuple(nonblank(item, label) for item in value)


@dataclass(frozen=True)
class TaskRecord:
    """Canonical commitment state, without inferred facts or a rigid transition graph."""
    task_id: str
    title: str
    state: TaskState
    importance: int | None = None
    urgency: int | None = None
    owner: str | None = None
    deadline: str | None = None
    dependency_ids: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    completion_evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        nonblank(self.task_id, "task_id")
        nonblank(self.title, "title")
        if not isinstance(self.state, TaskState):
            raise ValueError("state must be a valid TaskState")
        if self.importance is not None:
            importance_band(self.importance)
        if self.urgency is not None:
            urgency_band(self.urgency)
        for label in ("owner", "deadline"):
            if getattr(self, label) is not None:
                nonblank(getattr(self, label), label)
        for label in ("dependency_ids", "source_refs", "completion_evidence"):
            object.__setattr__(self, label, references(getattr(self, label), label))
        if self.task_id in self.dependency_ids:
            raise ValueError("a task cannot depend on itself")
        if self.state is TaskState.DONE and not self.completion_evidence:
            raise ValueError("DONE requires explicit nonblank completion evidence")

    @property
    def priority(self) -> PriorityResult | None:
        if self.importance is None or self.urgency is None:
            return None
        return classify_priority(self.importance, self.urgency)

    def transition(self, new_state: TaskState, *,
                   completion_evidence: tuple[str, ...] = ()) -> "TaskRecord":
        """Permissive non-DONE changes; the completion gate also applies to construction."""
        if not isinstance(new_state, TaskState):
            raise ValueError("new_state must be a valid TaskState")
        evidence = references(completion_evidence, "completion_evidence")
        return replace(self, state=new_state,
                       completion_evidence=evidence if new_state is TaskState.DONE else ())
