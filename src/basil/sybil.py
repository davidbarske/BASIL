from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from basil.priority import PriorityResult, classify_priority


class TaskState(str, Enum):
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    SCHEDULED = "SCHEDULED"
    BLOCKED = "BLOCKED"
    MONITOR = "MONITOR"
    DONE = "DONE"


@dataclass(frozen=True)
class TaskRecord:
    """Minimal canonical SYBIL task/commitment state.

    The model deliberately does not infer importance, urgency, owner, deadline,
    dependencies or completion. Those fields remain absent until supported by
    evidence or an explicit decision.
    """

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
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if (self.importance is None) != (self.urgency is None):
            raise ValueError("importance and urgency must either both be set or both be absent")
        if self.importance is not None and self.urgency is not None:
            classify_priority(self.importance, self.urgency)
        if self.state is TaskState.DONE and not self.completion_evidence:
            raise ValueError("DONE requires completion evidence")
        if self.task_id in self.dependency_ids:
            raise ValueError("a task cannot depend on itself")

    @property
    def priority(self) -> PriorityResult | None:
        if self.importance is None or self.urgency is None:
            return None
        return classify_priority(self.importance, self.urgency)

    def transition(
        self,
        new_state: TaskState,
        *,
        completion_evidence: tuple[str, ...] = (),
    ) -> "TaskRecord":
        """Return a new state record without inventing additional task facts.

        BASIL has not yet reconciled a stricter universal transition graph, so
        non-DONE state changes are intentionally permissive. Completion is the
        hard evidence gate: DONE cannot be reached without explicit evidence.
        """
        if new_state is TaskState.DONE:
            evidence = tuple(x for x in completion_evidence if x.strip())
            if not evidence:
                raise ValueError("DONE requires completion evidence")
            return replace(self, state=new_state, completion_evidence=evidence)
        return replace(self, state=new_state, completion_evidence=())
