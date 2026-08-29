# BASIL Migration Completeness — 29 August 2026

**Status:** SUBSTANTIVE MIGRATION COMPLETE / CANONICAL CUTOVER READY  
**Canonical branch:** `main`  
**Machine-readable registry:** `src/basil/data/capabilities.json`  
**Remaining cutover marker:** Git tag `v0.2-canonical-baseline` cannot be created through the currently available GitHub connector and remains a technical/manual follow-up.

## Decision

The migration of existing current BASIL system, capability, build and implementation state into GitHub is complete to the evidence-supported maturity of each capability.

This does **not** mean every planned BASIL subsystem is built. Repository migration state and capability maturity remain deliberately separate. GRAIL and POLLY, for example, are now repository-canonical at **ARCHITECTURAL** maturity because their current responsibilities are fully represented while mature runtimes do not yet exist.

There are no remaining `placeholder` or `migrating` capability-registry entries at this cutover state.

## Completed migration estate

| Area | Repository state | Maturity boundary |
|---|---|---|
| BASIL controller/governance | CANONICAL | documented controller representation; chat/runtime enforcement separate |
| MANUEL Interaction Evidence Ingest | CANONICAL | operational v2.0 FINAL |
| MANUEL diarisation | CANONICAL | tested exact v2 source |
| MANUEL acoustic enrichment | CANONICAL | tested public-safe refactor with bounded historical compatibility validation |
| BRIAN Meeting Intelligence | CANONICAL | operational v2.0 FINAL |
| BRIAN Behavioural / Interaction Profile | CANONICAL | tested extension routed through Meeting Intelligence v2.0 |
| Hughes / Greene / Carnegie-Rory | CANONICAL | documented specialist skills; runtime binding not inflated |
| SYBIL | CANONICAL | tested task-state core; full orchestration remains future build |
| FAWLTY | CANONICAL | tested learning/calibration core; archaeology remains a working Drive pilot with public provenance |
| GRAIL | CANONICAL | architectural responsibility only; automation remains future build |
| POLLY | CANONICAL | architectural responsibility only; orchestration runtime remains future build |
| Visual Execution | CANONICAL | built, previously deployed Phase 1 prototype; historical frontend source not recovered and current deployment not revalidated |
| Android v0.1 | CANONICAL | built source; binary/APK/device validation still open |
| GrillMe | CANONICAL | tested and formally adopted |
| Ask the CEO | CANONICAL repository artefact | candidate; positive use signal but reliable ordinary-chat activation unverified |
| Other LABS/integrations | CANONICAL repository artefacts | remain at their stated candidate maturity |

## Registry location decision

The migration plan originally proposed moving the registry to a new top-level `registry/capabilities.json` after the schema stabilised. That relocation is **not being performed at cutover**.

`src/basil/data/capabilities.json` is already the single packaged catalogue consumed by the executable core and repository doctor. Creating a top-level copy would create two catalogues or require extra packaging/path logic without adding decision value. The existing packaged location therefore remains the canonical machine-readable registry until a future implementation requirement justifies moving it.

This is a deliberate cutover decision, not unfinished migration.

## Retrieval contract

The executable core now provides compact repository-first orientation:

```bash
python -m basil context
python -m basil context --json
python -m basil capability brian.meeting-intelligence
python -m basil capability brian.meeting-intelligence --json
```

`context` reports the canonical repository authority, architecture path, registry path/schema, core MANUEL → BRIAN → BASIL flow, capability count, repository-state counts and open migration count. `capability` resolves one stable capability ID and reports its owner, maturity, repository status, canonical path and evidence boundary.

Chats/controllers should use current GitHub `main` for BASIL system/capability/build state, recording the commit SHA when state matters. Drive remains the durable evidence repository for private, historical, heavyweight and source-evidence material referenced by canonical records.

## Future build — not migration debt

The following remain legitimate future work and must not be relabelled as unfinished migration:

- full SYBIL orchestration, sequencing and anomaly/risk automation beyond the tested task-state core
- GRAIL strategic-arc automation
- POLLY integration-orchestration runtime
- broader FAWLTY automated learning flows and continued archaeology
- future Visual Execution implementation and recovery of historical frontend source if it later surfaces
- Android APK/build/device validation and later app vertical slices
- reliable ordinary-chat runtime binding for Ask the CEO and other skill-surface work
- external repository adoption experiments
- the explicitly paused BASIL voice workstream unless David reopens it

## Residual housekeeping

Completed short-lived branches remain visible because the available GitHub connector does not expose branch deletion. Audited disposable branches carry `BRANCH_DELETE_MANUALLY.md`; this is branch clutter, not missing work.

The intended baseline tag is `v0.2-canonical-baseline`. Tag creation is the only planned cutover marker that cannot be executed with the current connector. The exact promoted `main` SHA and this exception are recorded in the Drive repository activity log after final verification.

## Cutover gate

Cutover is accepted only after the `work/canonical-cutover` branch passes the existing BASIL verification, current `main` is rechecked, the branch is fast-forward promoted, `main` passes verification and the Drive activity log records and verifies the exact transition.
