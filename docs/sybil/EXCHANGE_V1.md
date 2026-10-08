# SYBIL task exchange v1

This specification covers the existing commitment/task meaning, not a BASIL-wide ontology, persistence layer, scheduler or rigid transition graph.

## Canonical payload

Envelope: format = BASIL_SYBIL_TASKS; schema_version = integer 1; tasks = array with unique task IDs.

Each task contains exactly:
- task_id, title: nonblank strings.
- state: ACTIVE, WAITING, SCHEDULED, BLOCKED, MONITOR, DONE.
- importance, urgency: independent integer 1..10 or null.
- owner, deadline: explicit nonblank string or null. Deadline remains opaque text.
- dependency_ids, source_refs, completion_evidence: ordered arrays of nonblank strings.

Python uses a typed TaskState and immutable tuples; Android maps task_id/title to existing id/description and uses defensive immutable reference lists. JSON strings become enums only at the decoding boundary. DONE requires a nonempty completion_evidence array. All blank entries are rejected, even mixed with valid entries; references otherwise retain exact text/order. A timestamp is never completion evidence. Dependency self-reference is rejected, but relationships are neither inferred nor resolved.

Unknown priority dimensions stay unknown independently. Only both known dimensions receive the existing priority calculation. The old partial-score rejection test was changed because skills/sybil/README.md and the current operator instructions explicitly keep dimensions separate and classify only both known; the paired-presence implementation detail contradicted that rule. The known-score matrix is unchanged.

Non-DONE changes remain permissive. Reopening clears current completion evidence as the existing transition helper did. No cancellation/deletion/archival states or universal transition graph are added. Structural validation of an evidence reference is not a claim that SYBIL has independently verified the external artifact; MANUEL/controller retain their current authority.

## Fixed Android compatibility sidecar

Optional envelope android_v01 maps included task IDs to exactly six existing client fields:
project, nextAction, notes: strings.
createdAt, updatedAt, completedAt: nonnegative signed-64-bit epoch milliseconds or null.

These are client metadata, not new canonical SYBIL fields. All six are preserved, including explicit unknown timestamps and empty strings. No extensible metadata framework is introduced. Python TaskExchange carries this sidecar through encode/decode; TaskRecord remains the ten-field canonical domain model. TaskExchange defensively copies and freezes both mapping levels; the six validated values are immutable primitives. External mutations cannot invalidate it. Encoding still revalidates and emits ordinary JSON objects.

## Legacy Android exports

Both implementations accept BASIL_TASK_EXPORT with schemaVersion integer 1. IDs, description, state and deadline map to canonical fields; unsupported scores/owner stay null, dependencies/source references stay empty. Project/nextAction/notes and known timestamps enter only the sidecar. Legacy blank deadline maps to null. exportedAt describes the export, not a task fact, and is not promoted to a task timestamp.

Historical DONE without completionEvidence raises LegacyReconciliationRequired:
Python: task_ids and original_payload.
Android: taskIds and originalPayload.

The error retains the exact original JSON string for later reconciliation. No task is discarded, reactivated or given invented proof. Existing Android import failure handling does not replace data when decoding fails, and local reads do not rewrite the original file. Supplying actual completionEvidence references in a retained legacy copy permits validation; blank/nontext references fail. There is no automatic adjudication of historical completion.

## Android application boundaries

### Historical local source recovery

Strict codec decoding still rejects historical DONE without explicit valid completion evidence, including blank references. The local application reads a separate LocalSnapshot: only strictly validated unaffected tasks are visible, read-only. A persistent source-problem banner names every affected ID. These source records never become canonical TaskRecords, acquire invented evidence or silently change state. Malformed unrelated JSON yields no operational tasks and an explicit source error.

Export original returns the exact original bytes, including whitespace and line endings. Save, delete, replacement and ordinary import all refuse to overwrite an invalid or unreconciled local register. Reading or failed reconciliation never rewrites that file.

The explicit recovery action accepts a complete reconciled file retaining every original ID exactly once. Only completion evidence for the affected historical tasks may change; every other canonical fact must match. Original client metadata is retained even if the supplied canonical file omitted it. After full validation, the exact original bytes are retained separately in basil_tasks_v01.legacy-original.json with create-only semantics before replacing the register atomically. A different existing backup blocks recovery rather than being overwritten. This is source preservation for a bounded local recovery, not a history database or external evidence adjudication.

### Task value semantics

Android TaskRecord deliberately remains an ordinary final class so constructor and copy() always defensively copy reference lists before validation. A generated data-class copy would make that boundary less explicit. Structural equals(), hashCode() and toString() are implemented using private immutable canonical/client value objects. Equality covers every represented field, including effective sidecar presence; an incidental constructor flag cannot break codec round-trip equality. An explicit empty sidecar remains distinct from no sidecar. Collections and Compose structural state policies therefore use task values, not object identity.

sameCanonicalContent() compares exactly the ten canonical fields, excluding client metadata. Ordered references remain ordered; they are not interpreted or resolved.

### Same-ID imports

| Case | Behaviour |
| --- | --- |
| New ID | Append the validated task. |
| Identical canonical content | Keep the local task and its client metadata. |
| Different canonical content, both timestamps known | Reconciliation conflict; neither version supersedes the other. |
| Imported timestamp unknown | The same canonical-conflict rule applies. |
| Local timestamp unknown | The same canonical-conflict rule applies. |
| Equal timestamps, different canonical content | The same canonical-conflict rule applies. |

Imports are all-or-nothing: any canonical conflict blocks the entire batch, including new IDs, leaving the local file unchanged. The structured conflict retains both variants and the exact supplied JSON string; a persistent UI banner lists IDs and offers export of the conflicting input. Android timestamps affect display ordering only, never canonical supersession. This is not a distributed synchronization protocol or a new conflict-resolution doctrine.

### Client-local deletion

Android v0.1 physical deletion remains a device-local action, explicitly described in the UI and repository interface. It emits no canonical state, tombstone or history-deletion instruction. A future persistence/synchronization layer MUST NOT interpret absence from an Android register/export as authority to delete canonical SYBIL state or history. Canonical deletion/abandonment doctrine remains unresolved; no new state is added.

## Verification

Shared synthetic fixtures in fixtures/sybil cover all six states, both unknown/partial dimensions, explicit dependencies/source references, known classification, evidence-backed DONE and client metadata. Android tests consume these same files.

The CI workflow checks out its actual evaluated commit, runs Python tests/doctor, generates JSON through the Python codec, runs Android tests/debug build, then compares Android-produced JSON in Python. Android acceptance failures fail the job: no continue-on-error or neutral implementation check.

Commands:
python -m unittest discover -s tests -v
python -m basil doctor
python scripts/verify_sybil_exchange.py --prepare
gradle -p clients/android/v0.1/source testDebugUnitTest assembleDebug --console=plain
python scripts/verify_sybil_exchange.py

Installed Gradle 8.9/JDK17 supports the recovered source without introducing a wrapper JAR. org.json's JVM implementation is test-only; production continues using Android's org.json.

## Explicitly deferred

SQLite, history, persistent CLI, scheduling, dependency resolution, network synchronization, APIs and other BASIL domains are excluded. Canonical deletion/history authority, external evidence adequacy, universal transitions, deadline interpretation, legacy completion adjudication and distributed conflict-resolution authority remain unresolved. This contract is a foundation for the next bounded persistence intervention, not a claim that those capabilities exist.
