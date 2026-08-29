# BASIL

![BASIL working mark](assets/brand/basil-logo.svg)

BASIL is a strategic operating environment for turning messy real-world information into preserved evidence, intelligence, decisions, commitments, execution and learning.

**GitHub `main` is the canonical source for BASIL architecture, capability, build and implementation state.** Google Drive remains the durable evidence/records repository for private, historical, heavyweight and source-evidence material that does not belong in this public repository.

Current cutover state: see `docs/status/LINE_IN_THE_SAND_2026-08-29.md` and `docs/repository/MIGRATION_COMPLETENESS_2026-08-29.md`.

## Current architecture

The principal evidence path is:

`source → MANUEL evidence → BRIAN intelligence → BASIL operationalisation`

That is not the whole topology. Current subsystem responsibilities are:

- **BASIL** — controller and operational layer. Turns validated state and intelligence into action.
- **MANUEL** — source preservation, intake, transcription/diarisation evidence, reconciliation, provenance and structured Interaction Evidence.
- **BRIAN** — Meeting Intelligence, behavioural/relational intelligence, strategic interpretation and specialist evaluation lenses.
- **SYBIL** — commitments, task control, sequencing and anomaly/risk monitoring.
- **FAWLTY** — cross-system learning and calibration. Proposes material changes rather than silently rewriting other capabilities.
- **GRAIL** — protects strategic arcs and longer-horizon intent. Mature automation is future build work.
- **POLLY** — orchestrates integrations but is never source of truth. Mature orchestration runtime is future build work.
- **Visual Execution Layer** — human-facing representation of canonical state, including Strategic Pressure Map, AXIS4+1 and Gravity Channel.

**Logicators is historical and retired.**

## Canonical context and capability discovery

```bash
python -m basil context
python -m basil context --json
python -m basil capability brian.meeting-intelligence
python -m basil capability brian.meeting-intelligence --json
python -m basil capabilities
python -m basil doctor
```

`context` emits compact canonical orientation state. `capability` resolves one stable capability ID. `capabilities` lists the catalogue and evidence-supported maturity. `doctor` verifies registered paths and repository structure.

The single machine-readable capability registry is `src/basil/data/capabilities.json`. Repository state and capability maturity are separate: a capability may be repository-canonical while remaining architectural, documented, built or candidate rather than tested/deployed.

## What is materially migrated

The current repository includes:

- Interaction Evidence Ingest v2.0 FINAL
- tested exact v2 diarisation source
- tested public-safe acoustic enrichment refactor
- Meeting Intelligence v2.0 FINAL and its Behavioural / Interaction Profile extension
- Hughes, Greene and Carnegie-Rory specialist strategic evaluation skills
- tested SYBIL task-state core
- tested FAWLTY learning/calibration core plus public-safe archaeology provenance
- BASIL controller/governance representation
- Visual Execution capability/prototype state and Phase 1 evidence boundary
- recovered Android v0.1 source
- adopted GrillMe skill and current LABS/integration records at their stated maturity

The repository does not inflate open work. Android binary/device testing remains open. The historical Visual Execution frontend source has not been recovered. GRAIL and POLLY mature runtimes remain future work. Ask the CEO ordinary-chat activation remains unverified. The BASIL voice workstream remains paused.

## Repository doctrine

1. **Evidence before interpretation.** Capture and provenance precede synthesis.
2. **Evidence before claims.** Do not claim a build, write, send, fix, persistence event or completion without fresh evidence.
3. **Importance and Urgency stay separate.** Never invent deadlines or urgency to make a queue look complete.
4. **Capability maturity is explicit.** Documented, architectural, built, tested and operational are different states.
5. **Old material is evidence, not authority.** Historical tasks, statuses and architecture do not revive themselves.
6. **GitHub and Drive have different jobs.** GitHub holds current public-safe system/capability/build state; Drive preserves evidence, records and sensitive/history-heavy material.
7. **This repository is public.** Personal evidence, client records, legal material, credentials and raw meeting data do not belong here.

## Working areas

- `src/basil/` — executable core and packaged capability registry
- `clients/` — current client source such as Android v0.1
- `skills/` — BASIL-owned skills plus isolated experiments
- `integrations/` — repository/package adoption candidates
- `docs/` — architecture, governance, visual, learning, repository and status records
- `assets/` — public-safe BASIL visual assets
- `tests/` — executable verification

Run tests with:

```bash
python -m unittest discover -s tests -v
```

## Cutover marker

The substantive migration is complete subject to the final cutover verification recorded in `docs/repository/MIGRATION_COMPLETENESS_2026-08-29.md`. The intended Git tag is `v0.2-canonical-baseline`; tag creation is a small technical/manual follow-up because the currently available GitHub connector does not expose tag creation.
