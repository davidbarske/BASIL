"""Local SYBIL persistence; canonical validation and exchange remain separate."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import os
import sqlite3

from .sybil import TaskRecord, TaskState, nonblank, references
from .sybil_exchange import TASK_FIELDS, parse_json, task_from_dict, task_to_dict

SCHEMA_VERSION = 1
REFERENCE_FIELDS = ("dependency_ids", "source_refs", "completion_evidence")
SCALAR_FIELDS = tuple(name for name in TASK_FIELDS if name not in REFERENCE_FIELDS)
UPDATE_FIELDS = frozenset(TASK_FIELDS) - {"task_id", "state"}
OPERATIONS = ("CREATE", "UPDATE", "STATE_CHANGE", "COMPLETE")

SCHEMA = (
    """CREATE TABLE tasks (
        task_id TEXT PRIMARY KEY NOT NULL,
        title TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('ACTIVE','WAITING','SCHEDULED','BLOCKED','MONITOR','DONE')),
        importance INTEGER CHECK(importance IS NULL OR (typeof(importance)='integer' AND importance BETWEEN 1 AND 10)),
        urgency INTEGER CHECK(urgency IS NULL OR (typeof(urgency)='integer' AND urgency BETWEEN 1 AND 10)),
        owner TEXT, deadline TEXT
    )""",
    """CREATE TABLE task_references (
        task_id TEXT NOT NULL REFERENCES tasks(task_id),
        field TEXT NOT NULL CHECK(field IN ('dependency_ids','source_refs','completion_evidence')),
        position INTEGER NOT NULL CHECK(typeof(position)='integer' AND position>=0),
        reference TEXT NOT NULL,
        PRIMARY KEY(task_id,field,position)
    )""",
    """CREATE TABLE task_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL REFERENCES tasks(task_id),
        operation TEXT NOT NULL CHECK(operation IN ('CREATE','UPDATE','STATE_CHANGE','COMPLETE')),
        recorded_at TEXT NOT NULL,
        before_json TEXT, after_json TEXT NOT NULL, changed_fields_json TEXT NOT NULL,
        actor TEXT, mutation_source_refs_json TEXT, mutation_evidence_refs_json TEXT
    )""",
    "CREATE INDEX task_history_by_task ON task_history(task_id,history_id)",
    """CREATE TRIGGER task_history_no_update BEFORE UPDATE ON task_history
        BEGIN SELECT RAISE(ABORT,'SYBIL history is append-only'); END""",
    """CREATE TRIGGER task_history_no_delete BEFORE DELETE ON task_history
        BEGIN SELECT RAISE(ABORT,'SYBIL history is append-only'); END""",
)


class SybilStoreError(Exception):
    """Actionable storage failure; never a claim of successful mutation."""


class UnsupportedSchemaError(SybilStoreError):
    pass


class CorruptStoreError(SybilStoreError):
    pass


class DuplicateTaskError(SybilStoreError):
    pass


class TaskNotFoundError(SybilStoreError):
    pass


@dataclass(frozen=True)
class MutationContext:
    """Evidence about a mutation, not canonical task source_refs."""
    actor: str | None = None
    source_refs: tuple[str, ...] | None = None
    evidence_refs: tuple[str, ...] | None = None

    def __post_init__(self):
        if self.actor is not None:
            nonblank(self.actor, "actor")
        for name in ("source_refs", "evidence_refs"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, references(value, name))


@dataclass(frozen=True)
class HistoryEntry:
    history_id: int
    task_id: str
    operation: str
    recorded_at: str
    before: TaskRecord | None
    after: TaskRecord
    changed_fields: tuple[str, ...]
    context: MutationContext


def _canonical(task: TaskRecord) -> TaskRecord:
    if not isinstance(task, TaskRecord):
        raise ValueError("Expected a canonical TaskRecord")
    return task_from_dict(task_to_dict(task))


def _context(context: MutationContext | None) -> MutationContext:
    if context is None:
        return MutationContext()
    if not isinstance(context, MutationContext):
        raise ValueError("context must be a MutationContext or absent")
    return MutationContext(context.actor, context.source_refs, context.evidence_refs)


def _changed(before: TaskRecord | None, after: TaskRecord) -> tuple[str, ...]:
    return tuple(name for name in TASK_FIELDS
                 if before is None or getattr(before, name) != getattr(after, name))


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _context_json(value) -> str | None:
    return None if value is None else _json(list(value))


def _context_refs(value, label):
    if value is None:
        return None
    data = parse_json(value)
    if not isinstance(data, list):
        raise ValueError(f"{label} must contain a JSON reference array")
    return references(data, label)


class SybilStore:
    """One explicit local DB, no canonical delete, scheduler or Android sidecar."""
    def __init__(self, path: str | os.PathLike[str]):
        path = os.fspath(path)
        nonblank(path, "database path")
        self._closed = False
        try:
            self._connection = sqlite3.connect(path, timeout=5, isolation_level=None)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys=ON")
            self._connection.execute("PRAGMA synchronous=FULL")
            self.initialise()
        except BaseException as error:
            if hasattr(self, "_connection"):
                self._connection.close()
            self._closed = True
            if isinstance(error, sqlite3.Error):
                raise SybilStoreError(f"Unable to open SQLite database: {error}") from error
            raise

    def __enter__(self):
        if self._closed:
            raise SybilStoreError("SYBIL store is closed")
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if not self._closed:
            self._connection.close()
            self._closed = True

    @contextmanager
    def _transaction(self, *, write=False):
        if self._closed:
            raise SybilStoreError("SYBIL store is closed")
        try:
            self._connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            try:
                yield
                self._connection.commit()
            except BaseException:
                self._connection.rollback()
                raise
        except sqlite3.Error as error:
            raise SybilStoreError(f"SQLite transaction failed; no mutation committed: {error}") from error

    def initialise(self):
        with self._transaction(write=True):
            version = self._connection.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                objects = self._connection.execute(
                    "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
                ).fetchall()
                if objects:
                    raise UnsupportedSchemaError("Unversioned nonempty database; refusing to alter it")
                for statement in SCHEMA:
                    self._connection.execute(statement)
                self._connection.execute("PRAGMA user_version=1")
            elif version != SCHEMA_VERSION:
                raise UnsupportedSchemaError(f"Unsupported SYBIL database schema {version}; supported: 1")
            expected = {
                "tasks": set(SCALAR_FIELDS),
                "task_references": {"task_id", "field", "position", "reference"},
                "task_history": {"history_id", "task_id", "operation", "recorded_at",
                                 "before_json", "after_json", "changed_fields_json", "actor",
                                 "mutation_source_refs_json", "mutation_evidence_refs_json"},
            }
            for table, columns in expected.items():
                actual = {row["name"] for row in self._connection.execute(f"PRAGMA table_info({table})")}
                if actual != columns:
                    raise CorruptStoreError(f"Invalid SYBIL schema: {table}")
            triggers = {row[0] for row in self._connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'")}
            if not {"task_history_no_update", "task_history_no_delete"} <= triggers:
                raise CorruptStoreError("Missing append-preserving history guards")
            if self._connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise CorruptStoreError("Invalid SYBIL foreign-key references")

    def _get(self, task_id: str) -> TaskRecord:
        row = self._connection.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            raise TaskNotFoundError(f"Unknown SYBIL task: {task_id}")
        try:
            data = dict(row)
            collection_rows = self._connection.execute(
                "SELECT field,position,reference FROM task_references WHERE task_id=? ORDER BY field,position",
                (task_id,),
            ).fetchall()
            if any(item["field"] not in REFERENCE_FIELDS for item in collection_rows):
                raise ValueError("Unknown reference collection")
            for field in REFERENCE_FIELDS:
                values = [item for item in collection_rows if item["field"] == field]
                if [item["position"] for item in values] != list(range(len(values))):
                    raise ValueError(f"Noncontiguous reference positions: {field}")
                data[field] = [item["reference"] for item in values]
            return task_from_dict(data)
        except (ValueError, TypeError, KeyError) as error:
            raise CorruptStoreError(f"Invalid persisted SYBIL task {task_id}: {error}") from error

    def get(self, task_id: str) -> TaskRecord:
        nonblank(task_id, "task_id")
        with self._transaction():
            return self._get(task_id)

    def list(self) -> tuple[TaskRecord, ...]:
        with self._transaction():
            ids = [row[0] for row in self._connection.execute("SELECT task_id FROM tasks ORDER BY task_id")]
            return tuple(self._get(task_id) for task_id in ids)

    def _write_task(self, task: TaskRecord, *, create=False):
        data = task_to_dict(task)
        if create:
            self._connection.execute(
                "INSERT INTO tasks(task_id,title,state,importance,urgency,owner,deadline) VALUES(?,?,?,?,?,?,?)",
                tuple(data[name] for name in SCALAR_FIELDS),
            )
        else:
            self._connection.execute(
                "UPDATE tasks SET title=?,state=?,importance=?,urgency=?,owner=?,deadline=? WHERE task_id=?",
                tuple(data[name] for name in SCALAR_FIELDS[1:]) + (task.task_id,),
            )
            self._connection.execute("DELETE FROM task_references WHERE task_id=?", (task.task_id,))
        for field in REFERENCE_FIELDS:
            self._connection.executemany(
                "INSERT INTO task_references(task_id,field,position,reference) VALUES(?,?,?,?)",
                [(task.task_id, field, position, ref) for position, ref in enumerate(data[field])],
            )

    def _append_history(self, operation, before, after, context):
        self._connection.execute(
            """INSERT INTO task_history(task_id,operation,recorded_at,before_json,after_json,
               changed_fields_json,actor,mutation_source_refs_json,mutation_evidence_refs_json)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (after.task_id, operation, datetime.now(timezone.utc).isoformat(timespec="microseconds"),
             None if before is None else _json(task_to_dict(before)), _json(task_to_dict(after)),
             _json(list(_changed(before, after))), context.actor,
             _context_json(context.source_refs), _context_json(context.evidence_refs)),
        )

    def create(self, task: TaskRecord, *, context: MutationContext | None = None) -> TaskRecord:
        task, context = _canonical(task), _context(context)
        with self._transaction(write=True):
            if self._connection.execute("SELECT 1 FROM tasks WHERE task_id=?", (task.task_id,)).fetchone():
                raise DuplicateTaskError(f"SYBIL task already exists: {task.task_id}")
            self._write_task(task, create=True)
            self._append_history("CREATE", None, task, context)
        return task

    def update(self, task_id: str, *, context: MutationContext | None = None, **changes) -> TaskRecord:
        nonblank(task_id, "task_id")
        if set(changes) - UPDATE_FIELDS:
            raise ValueError("Unsupported update fields; task ID is immutable and state uses transition/complete")
        context = _context(context)
        with self._transaction(write=True):
            before = self._get(task_id)
            self._history(task_id, before)
            after = _canonical(replace(before, **changes))
            if after != before:
                self._write_task(after)
                self._append_history("UPDATE", before, after, context)
        return after

    def transition(self, task_id: str, state: TaskState, *,
                   completion_evidence: tuple[str, ...] = (),
                   context: MutationContext | None = None) -> TaskRecord:
        nonblank(task_id, "task_id")
        if not isinstance(state, TaskState):
            raise ValueError("state must be a valid TaskState; raw strings are not accepted")
        context = _context(context)
        with self._transaction(write=True):
            before = self._get(task_id)
            self._history(task_id, before)
            after = before.transition(state, completion_evidence=completion_evidence)
            if after != before:
                self._write_task(after)
                self._append_history("COMPLETE" if state is TaskState.DONE else "STATE_CHANGE",
                                     before, after, context)
        return after

    def complete(self, task_id: str, completion_evidence: tuple[str, ...], *,
                 context: MutationContext | None = None) -> TaskRecord:
        return self.transition(task_id, TaskState.DONE,
                               completion_evidence=completion_evidence, context=context)

    def _history(self, task_id, current) -> tuple[HistoryEntry, ...]:
        rows = self._connection.execute(
            "SELECT * FROM task_history WHERE task_id=? ORDER BY history_id", (task_id,),
        ).fetchall()
        entries = []
        previous = None
        try:
            for row in rows:
                before = None if row["before_json"] is None else task_from_dict(parse_json(row["before_json"]))
                after = task_from_dict(parse_json(row["after_json"]))
                fields = parse_json(row["changed_fields_json"])
                when = datetime.fromisoformat(row["recorded_at"])
                operation = row["operation"]
                if (operation not in OPERATIONS or after.task_id != task_id or
                        (before is not None and (before.task_id != task_id or before == after)) or before != previous or
                        not isinstance(fields, list) or tuple(fields) != _changed(before, after) or
                        when.utcoffset() is None or when.utcoffset().total_seconds() != 0):
                    raise ValueError("Invalid history chain, fields, operation or timestamp")
                if (before is None) != (operation == "CREATE"):
                    raise ValueError("Invalid creation history")
                if operation == "UPDATE" and before.state != after.state:
                    raise ValueError("UPDATE cannot change state")
                if operation == "COMPLETE" and after.state is not TaskState.DONE:
                    raise ValueError("COMPLETE must result in evidence-backed DONE")
                if operation == "STATE_CHANGE" and after.state is TaskState.DONE:
                    raise ValueError("DONE requires COMPLETE history")
                context = MutationContext(row["actor"],
                    _context_refs(row["mutation_source_refs_json"], "mutation source_refs"),
                    _context_refs(row["mutation_evidence_refs_json"], "mutation evidence_refs"))
                entries.append(HistoryEntry(row["history_id"], task_id, operation, row["recorded_at"],
                                            before, after, tuple(fields), context))
                previous = after
            if not entries or previous != current:
                raise ValueError("History does not reconstruct current canonical state")
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise CorruptStoreError(f"Invalid persisted SYBIL history for {task_id}: {error}") from error
        return tuple(entries)

    def history(self, task_id: str) -> tuple[HistoryEntry, ...]:
        nonblank(task_id, "task_id")
        with self._transaction():
            return self._history(task_id, self._get(task_id))
