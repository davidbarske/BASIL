# Durable SYBIL state v1

SYBIL owns this local commitment register only. MANUEL evidence, BRIAN intelligence,
GRAIL strategy and FAWLTY learning remain outside it. Opaque task source references
are retained, not resolved or copied into a broader ontology. The settled ten-field
TaskRecord and BASIL_SYBIL_TASKS exchange v1 are unchanged. Android's compatibility
sidecar is not stored. This is a bounded implementation with automated verification,
not a deployed service or complete SYBIL orchestration.

## Location and schema

SybilStore(path) requires an explicit filesystem path; the CLI requires --db PATH.
There is no implicit global location. The parent directory must already exist.
Keep operational/private databases outside this public checkout. Tests use temporary
on-disk locations and synthetic records; no database is committed.

Standard-library sqlite3, PRAGMA user_version=1:
- tasks: task_id primary key, title, state, nullable importance/urgency/owner/deadline.
- task_references: task_id, canonical collection name, zero-based position, reference.
  The three ordered collections retain exact text, ordering, repetitions and emptiness.
- task_history: monotonically assigned history_id, task_id, operation, actual UTC
  recorded_at, canonical before/after JSON, changed canonical field names, optional
  actor and separate optional mutation source/evidence reference arrays.

Only an empty version-0 database is initialised. An unversioned nonempty database,
unknown/future version, missing required structure/history guards or broken foreign
keys is refused. Supported version-1 stores reopen without a migration or rewriting
tasks. No speculative migrations are supplied.

## API

Use a context manager or explicitly close the store:

    from basil.sybil import TaskRecord, TaskState
    from basil.sybil_store import SybilStore, MutationContext

    with SybilStore("/explicit/private/path/sybil.sqlite") as store:
        store.create(TaskRecord("synthetic", "Synthetic commitment", TaskState.ACTIVE))
        store.update("synthetic", importance=8)
        store.transition("synthetic", TaskState.WAITING)
        store.complete("synthetic", ("proof:explicit-output",),
                       context=MutationContext(evidence_refs=("mutation:explicit-proof",)))
        task = store.get("synthetic")
        history = store.history("synthetic")

initialise() creates/verifies schema and is idempotent. create() rejects duplicate IDs.
get() raises TaskNotFoundError for an absent ID. list() returns an immutable tuple in
task-ID order, without strategic ranking. update() accepts canonical fields except
immutable task_id and state; transition()/complete() handle state. Updates may alter
completion evidence only while the resulting task remains valid. Non-DONE transitions
follow the existing permissive domain helper, including clearing current completion
evidence on reopening. DONE always needs explicit nonblank evidence; raw string states
are rejected by the store API. A validated JSON/CLI boundary converts exact enum names.

Actual canonical changes append CREATE, UPDATE, STATE_CHANGE or COMPLETE. Unchanged
updates/transitions return the current task without manufacturing a mutation entry.
transition(..., TaskState.DONE, completion_evidence=...) is recorded as COMPLETE.
History is an immutable tuple of frozen HistoryEntry values containing frozen
TaskRecords and MutationContext values. No public history update/delete method exists;
SQLite triggers also reject history UPDATE/DELETE. These guards are not a claim of
tamper-proof storage against an external administrator.

## Transactions, continuity and corruption

Connections use explicit transactions with synchronous=FULL and foreign_keys=ON.
BEGIN IMMEDIATE serialises writers before reading/modifying canonical state. Scalar
writes, replacement of ordered reference rows and history insertion commit together.
Any SQL error, validation failure or interruption rolls the transaction back. Reads
of scalar/collection rows use one snapshot transaction. Independent store instances
observe prior committed changes before applying their own field updates.

Every reconstructed task passes the existing canonical decoder/TaskRecord validation.
Reference positions must be contiguous and collection names supported. Corrupt task
data fails loudly as CorruptStoreError; it is never repaired, downgraded, omitted from
a partial successful list or promoted by its presence in SQLite. SQL failures raise
SybilStoreError and are not reported as success.

history() validates canonical snapshots, changed fields, operation, UTC timestamp,
before/after chain and agreement with the current task. Mutations also validate this
history chain before extending it. History retains prior completion evidence after
a permissive reopening clears the current record's evidence.

MutationContext is separate from task source_refs. Actor/process identity is recorded
only if explicitly supplied; no CLI person or "system" actor is invented. Unknown
mutation reference collections are SQL NULL, distinct from explicitly supplied empty
arrays. Collection inputs are copied into tuples, preserving ordering.

## CLI verification

Each command opens/closes the explicit store. --json emits canonical task objects,
lists, history objects or schema/path information.

    python -m basil sybil --db /explicit/path/sybil.sqlite initialise --json
    python -m basil sybil --db /explicit/path/sybil.sqlite create synthetic --title "Synthetic commitment" --json
    python -m basil sybil --db /explicit/path/sybil.sqlite show synthetic --json
    python -m basil sybil --db /explicit/path/sybil.sqlite update synthetic --importance 8 --json
    python -m basil sybil --db /explicit/path/sybil.sqlite transition synthetic --state WAITING --json
    python -m basil sybil --db /explicit/path/sybil.sqlite complete synthetic --evidence proof:explicit-output --json
    python -m basil sybil --db /explicit/path/sybil.sqlite history synthetic --json
    python -m basil sybil --db /explicit/path/sybil.sqlite list --json

Scores accept 1..10 or unknown. Omitted update flags preserve facts. --clear-owner,
--clear-deadline, --clear-dependencies, --clear-source-refs and
--clear-completion-evidence explicitly clear optional facts/collections; validation
still blocks removing DONE evidence. Repeated --depends-on, --source-ref and
--completion-evidence replace those ordered collections on update. Mutation context
flags are --actor, --change-source and --change-evidence. No interactive prompts,
implicit owner/deadline/priority or hidden database path are introduced.

## Verification and explicit exclusions

tests/test_sybil_store.py exercises the full on-disk create/close/reopen/update/
close/reopen/transition/close/reopen/complete/close/reopen chain and chronological
history, all four priority-knowledge cases, shared canonical fixtures, ordered
references, corruption, failed writes, interrupted transactions and concurrent writers.
tests/test_sybil_cli.py runs independent OS processes against one temporary DB,
including the full lifecycle and a final reconstruction/history read in new processes.
Existing Python/Android exchange tests and workflows remain part of acceptance.

There is no canonical delete, cancellation, archival or abandonment operation/state.
Android local absence authorises no durable deletion or history removal. Scheduling,
dependency resolution/cycle planning, remote/Android synchronization, APIs, cloud
infrastructure, controller automation and other BASIL domains are excluded.
External evidence adequacy, canonical deletion and a universal transition graph remain
unresolved doctrine, not SQLite implementation decisions.
