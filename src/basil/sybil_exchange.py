"""SYBIL exchange v1, with a fixed sidecar for existing Android v0.1 data."""
from __future__ import annotations

from dataclasses import dataclass, field
import json

from .sybil import TaskRecord, TaskState

FORMAT = "BASIL_SYBIL_TASKS"
SCHEMA_VERSION = 1
TASK_FIELDS = ("task_id", "title", "state", "importance", "urgency", "owner",
               "deadline", "dependency_ids", "source_refs", "completion_evidence")
CLIENT_FIELDS = {"project", "nextAction", "notes", "createdAt", "updatedAt", "completedAt"}


class LegacyReconciliationRequired(ValueError):
    def __init__(self, task_ids: tuple[str, ...], original_payload: str):
        self.task_ids = task_ids
        self.original_payload = original_payload
        super().__init__("Legacy DONE tasks lack completion evidence; original payload retained: " + ", ".join(task_ids))


def task_to_dict(task: TaskRecord) -> dict:
    # Explicit fields and revalidation; never blindly serialize __dict__.
    task = TaskRecord(**{name: getattr(task, name) for name in TASK_FIELDS})
    return {
        "task_id": task.task_id, "title": task.title, "state": task.state.value,
        "importance": task.importance, "urgency": task.urgency,
        "owner": task.owner, "deadline": task.deadline,
        "dependency_ids": list(task.dependency_ids), "source_refs": list(task.source_refs),
        "completion_evidence": list(task.completion_evidence),
    }


def task_from_dict(data: object) -> TaskRecord:
    if not isinstance(data, dict) or set(data) != set(TASK_FIELDS):
        raise ValueError("task must contain exactly the canonical fields")
    values = dict(data)
    if not isinstance(values["state"], str):
        raise ValueError("JSON state must be an exact canonical name")
    try:
        values["state"] = TaskState(values["state"])
    except ValueError as exc:
        raise ValueError("unknown canonical task state") from exc
    for name in ("dependency_ids", "source_refs", "completion_evidence"):
        if not isinstance(values[name], list):
            raise ValueError(f"{name} must be a JSON array")
    return TaskRecord(**values)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def parse_json(text: str):
    return json.loads(text, object_pairs_hook=_object, parse_constant=_constant)


def validate_client(metadata: object):
    if not isinstance(metadata, dict) or set(metadata) != CLIENT_FIELDS:
        raise ValueError("Android sidecar must contain exactly the six v0.1 client fields")
    for name in ("project", "nextAction", "notes"):
        if not isinstance(metadata[name], str):
            raise ValueError(f"client {name} must be text")
    for name in ("createdAt", "updatedAt", "completedAt"):
        value = metadata[name]
        if value is not None and (type(value) is not int or not 0 <= value <= 2**63 - 1):
            raise ValueError(f"client {name} must be epoch-millisecond integer or null")


@dataclass(frozen=True)
class TaskExchange:
    tasks: tuple[TaskRecord, ...]
    android_v01: dict[str, dict] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "tasks", tuple(self.tasks))
        for task in self.tasks:
            task_to_dict(task)
        ids = {task.task_id for task in self.tasks}
        if len(ids) != len(self.tasks):
            raise ValueError("duplicate task IDs")
        if not isinstance(self.android_v01, dict) or set(self.android_v01) - ids:
            raise ValueError("sidecar must refer only to included tasks")
        for metadata in self.android_v01.values():
            validate_client(metadata)


def dumps(exchange: TaskExchange) -> str:
    exchange = TaskExchange(exchange.tasks, exchange.android_v01)
    data = {"format": FORMAT, "schema_version": SCHEMA_VERSION,
            "tasks": [task_to_dict(task) for task in exchange.tasks]}
    if exchange.android_v01:
        data["android_v01"] = exchange.android_v01
    return json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)


def loads(text: str) -> TaskExchange:
    data = parse_json(text)
    if not isinstance(data, dict):
        raise ValueError("exchange must be an object")
    if data.get("format") == "BASIL_TASK_EXPORT":
        return _legacy(data, text)
    if set(data) - {"format", "schema_version", "tasks", "android_v01"}:
        raise ValueError("unknown exchange fields")
    if (data.get("format") != FORMAT or type(data.get("schema_version")) is not int
            or data["schema_version"] != SCHEMA_VERSION):
        raise ValueError("unsupported SYBIL format/version")
    if not isinstance(data.get("tasks"), list):
        raise ValueError("tasks must be an array")
    return TaskExchange(tuple(task_from_dict(task) for task in data["tasks"]),
                        data.get("android_v01", {}))


def _legacy(data: dict, original: str) -> TaskExchange:
    if (set(data) - {"format", "schemaVersion", "exportedAt", "tasks"}
            or type(data.get("schemaVersion")) is not int or data["schemaVersion"] != 1
            or not isinstance(data.get("tasks"), list)):
        raise ValueError("unsupported legacy export")
    allowed = {"id", "description", "state", "deadline", "completionEvidence"} | CLIENT_FIELDS
    incomplete = []
    for old in data["tasks"]:
        if not isinstance(old, dict) or set(old) - allowed or not {"id", "description", "state"} <= set(old):
            raise ValueError("invalid legacy task fields")
        if old["state"] == "DONE" and not old.get("completionEvidence"):
            incomplete.append(old["id"])
    if incomplete:
        if not all(isinstance(task_id, str) for task_id in incomplete):
            raise ValueError("legacy IDs must be text")
        raise LegacyReconciliationRequired(tuple(incomplete), original)
    tasks, metadata = [], {}
    for old in data["tasks"]:
        deadline = old.get("deadline")
        if deadline is not None and not isinstance(deadline, str):
            raise ValueError("legacy deadline must be text/null")
        evidence = old.get("completionEvidence", [])
        if not isinstance(evidence, list):
            raise ValueError("legacy completionEvidence must be an array")
        task = TaskRecord(old["id"], old["description"], TaskState(old["state"]),
                          deadline=deadline if deadline and deadline.strip() else None,
                          completion_evidence=evidence)
        tasks.append(task)
        metadata[task.task_id] = {name: old.get(name, "" if name in {"project", "nextAction", "notes"} else None)
                                  for name in CLIENT_FIELDS}
    return TaskExchange(tuple(tasks), metadata)
