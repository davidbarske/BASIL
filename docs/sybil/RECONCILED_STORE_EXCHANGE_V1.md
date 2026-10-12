# SYBIL durable-store exchange and strict reconciliation (working implementation)

**Status:** implemented on a development branch; acceptance is subject to fresh CI.
This is not a deployed BASIL service, remote sync, migration of the live Drive
task register or authority to overwrite another device.

## Purpose and limits

Connect the existing `BASIL_SYBIL_TASKS` v1 canonical exchange codec to the
explicit-path SQLite `SybilStore` (schema v1), **without changing the ten-field
task contract or storing new undocumented fields**.

The store remains local, with no implicit database path, online service, Android
synchronisation, dependency scheduling or deletion mechanism.

## Canonical export

`SybilStore.export_exchange()` takes a consistent read transaction, reconstructs
all tasks in stable task-ID order, validates each task **and its history chain**
and returns `sybil_exchange.dumps(TaskExchange(tasks))`. An empty store produces
a valid empty exchange. The Android v0.1 client sidecar is absent because it is
not held in this durable store. Export does not infer owner, timing or evidence.

## Canonical import

`SybilStore.import_exchange(original_payload, context=None)` strictly decodes
the input using the existing exchange decoder **before** opening a write
transaction. Duplicate IDs, invalid canonical facts, unsupported versions and
unproved historical DONE are rejected by the decoder. Legacy reconciliation
exceptions preserve the original string.

An exchange with an Android v0.1 compatibility sidecar is **rejected**, not
silently stripped. This store cannot persist client `project`, `nextAction`,
`notes` or display timestamps. Callers must maintain that data separately and
explicitly prepare a sidecar-free canonical exchange; this API will not
automatically discard it. `UnpersistedClientMetadataError` retains the
original payload and affected IDs.

After decoding, one `BEGIN IMMEDIATE` transaction checks all incoming IDs:
- **New ID:** add exact canonical task with one atomic CREATE history entry.
- **Existing with identical canonical fields:** preserve local record, all
  history and any context; no new mutation or timestamp is fabricated.
- **Existing with different canonical fields:** refuse **the whole import**
  including otherwise-new IDs. `ExchangeReconciliationRequired` retains the
  exact original JSON string, conflicted IDs and **both canonical TaskRecords**.
  No clock or Android display timestamp decides which version wins.

All existing same-ID history chains are checked before any new records are
written. Any validation/SQLite failure rolls the transaction back. A missing
ID in an import never means delete: the store retains all other tasks and
append-only history.

Return `ImportResult(created_ids, unchanged_ids)` in input order on success.
`MutationContext` is optional and records only actually supplied actor/source/
evidence references on newly created records. It is not evidence adjudication.

## Minimal CLI examples

    python -m basil sybil --db /private/sybil.sqlite export
    python -m basil sybil --db /private/sybil.sqlite import --input /explicit/safe/export.json --json

Export prints valid exchange JSON to stdout. Import reads the original UTF-8
bytes without rewriting the source file; it prints a created/unchanged summary
on success and an error on failure. Use an explicit path for the database and
the import file. This implementation deliberately does not redirect export to
a file, create an automatic backup or install scheduled exchange/sync.

## Verification and unresolved boundaries

`tests/test_sybil_store_exchange.py` covers restart roundtrip, task sorting,
ordered/repeated references, independently unknown priorities, DONE evidence,
idempotency, atomic same-ID conflict refusal, client metadata loss refusal,
legacy input, corrupted history and independent CLI processes. Existing Python
and Android contract suites must continue to pass on the final branch head.

This does **not** resolve external evidence adequacy, provenance adjudication,
client sidecar retention in durable storage, canonical task deletion, universal
state transitions, remote convergence or cross-surface task authority.
