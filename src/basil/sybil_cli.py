"""Small argparse verification surface for the explicit-path SYBIL register."""
from __future__ import annotations

import argparse
import json
import sys

from .sybil import TaskRecord, TaskState
from .sybil_exchange import task_to_dict
from .sybil_store import HistoryEntry, MutationContext, SCHEMA_VERSION, SybilStore, SybilStoreError

STATES = tuple(state.value for state in TaskState)


def _score(text: str):
    if text == "unknown":
        return None
    try:
        value = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("score must be 1..10 or 'unknown'") from error
    if not 1 <= value <= 10:
        raise argparse.ArgumentTypeError("score must be 1..10 or 'unknown'")
    return value


def _facts(parser, *, update=False):
    default = argparse.SUPPRESS if update else None
    parser.add_argument("--title", required=not update, default=default)
    for name in ("importance", "urgency"):
        parser.add_argument("--" + name, type=_score, default=default)
    for name in ("owner", "deadline"):
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--" + name, default=default)
        if update:
            group.add_argument("--clear-" + name, dest=name, action="store_const", const=None,
                               default=argparse.SUPPRESS)
    for field, flag, clear in (
        ("dependency_ids", "depends-on", "dependencies"),
        ("source_refs", "source-ref", "source-refs"),
        ("completion_evidence", "completion-evidence", "completion-evidence"),
    ):
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--" + flag, dest=field, action="append", default=default)
        if update:
            group.add_argument("--clear-" + clear, dest=field, action="store_const", const=[],
                               default=argparse.SUPPRESS)


def add_parser(subparsers):
    parser = subparsers.add_parser("sybil", help="inspect durable canonical SYBIL state (explicit local DB)")
    parser.add_argument("--db", required=True, help="explicit SQLite path; no global default")
    operations = parser.add_subparsers(dest="sybil_operation", required=True)
    for operation in ("initialise", "create", "list", "show", "update", "transition", "complete", "history"):
        child = operations.add_parser(operation)
        child.add_argument("--json", action="store_true", dest="as_json")
        if operation not in {"initialise", "list"}:
            child.add_argument("task_id")
        if operation in {"create", "update"}:
            _facts(child, update=operation == "update")
        if operation in {"create", "transition"}:
            child.add_argument("--state", choices=STATES, default="ACTIVE" if operation == "create" else None,
                               required=operation == "transition")
        if operation in {"transition", "complete"}:
            child.add_argument("--evidence", action="append", required=operation == "complete",
                               default=None, help="explicit completion evidence reference; repeat for ordering")
        if operation in {"create", "update", "transition", "complete"}:
            child.add_argument("--actor", help="only an actually known actor/process identifier")
            child.add_argument("--change-source", action="append")
            child.add_argument("--change-evidence", action="append")


def history_to_dict(entry: HistoryEntry) -> dict:
    return {
        "history_id": entry.history_id, "task_id": entry.task_id,
        "operation": entry.operation, "recorded_at": entry.recorded_at,
        "before": None if entry.before is None else task_to_dict(entry.before),
        "after": task_to_dict(entry.after), "changed_fields": list(entry.changed_fields),
        "context": {
            "actor": entry.context.actor,
            "source_refs": None if entry.context.source_refs is None else list(entry.context.source_refs),
            "evidence_refs": None if entry.context.evidence_refs is None else list(entry.context.evidence_refs),
        },
    }


def run(args) -> int:
    try:
        operation = args.sybil_operation
        context = None
        if operation in {"create", "update", "transition", "complete"}:
            context = MutationContext(args.actor, args.change_source, args.change_evidence)
        with SybilStore(args.db) as store:
            if operation == "initialise":
                data = {"schema_version": SCHEMA_VERSION, "database": args.db}
            elif operation == "create":
                task = TaskRecord(args.task_id, args.title, TaskState(args.state),
                    importance=args.importance, urgency=args.urgency, owner=args.owner, deadline=args.deadline,
                    dependency_ids=tuple(args.dependency_ids or ()), source_refs=tuple(args.source_refs or ()),
                    completion_evidence=tuple(args.completion_evidence or ()))
                data = task_to_dict(store.create(task, context=context))
            elif operation == "list":
                data = [task_to_dict(task) for task in store.list()]
            elif operation == "show":
                data = task_to_dict(store.get(args.task_id))
            elif operation == "update":
                fields = ("title", "importance", "urgency", "owner", "deadline",
                          "dependency_ids", "source_refs", "completion_evidence")
                changes = {name: getattr(args, name) for name in fields if hasattr(args, name)}
                data = task_to_dict(store.update(args.task_id, context=context, **changes))
            elif operation == "transition":
                data = task_to_dict(store.transition(args.task_id, TaskState(args.state),
                    completion_evidence=tuple(args.evidence or ()), context=context))
            elif operation == "complete":
                data = task_to_dict(store.complete(args.task_id, tuple(args.evidence or ()), context=context))
            else:
                data = [history_to_dict(entry) for entry in store.history(args.task_id)]
        if args.as_json:
            print(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False))
        elif isinstance(data, list):
            for item in data:
                if "operation" in item:
                    print(f"{item['history_id']} {item['operation']} {item['recorded_at']} " +
                          ", ".join(item["changed_fields"]))
                else:
                    print(f"{item['task_id']} {item['state']} {item['title']}")
        elif "task_id" in data:
            print(f"{data['task_id']} {data['state']} {data['title']}")
        else:
            print(f"SYBIL schema {SCHEMA_VERSION}: {args.db}")
        return 0
    except (SybilStoreError, ValueError, OSError) as error:
        print(f"SYBIL: {error}", file=sys.stderr)
        return 1
