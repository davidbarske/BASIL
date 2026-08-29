# BASIL Milestone 1 — Canonical Baseline

**Date:** 29 August 2026  
**Status:** ACHIEVED  
**Baseline version:** 0.2.0

## What Milestone 1 means

Milestone 1 closes the original BASIL repository migration and establishes one coherent, inspectable public-safe implementation baseline in GitHub.

At this boundary:

- GitHub `main` is canonical for BASIL architecture, capability definitions, public-safe build/implementation state and maturity metadata
- Google Drive remains the durable evidence/records repository for private, historical, heavyweight and source-evidence material
- the capability registry contains no `placeholder` or `migrating` entries
- the current MANUEL → BRIAN meeting-production chain is represented canonically at its evidence-supported maturity
- BASIL controller/governance is canonical
- SYBIL and FAWLTY have tested core primitives without pretending their full future automation already exists
- Visual Execution is correctly represented as a built historical Phase 1 prototype capability with its source-recovery limitation preserved
- Android v0.1 source is recovered and canonical while binary/device validation remains explicitly open
- GRAIL and POLLY are canonical architectural responsibilities, not falsely reported as unfinished migrations or mature runtimes
- GrillMe is adopted while other LABS/integration items retain their actual candidate state
- compact repository retrieval is available through `python -m basil context` and `python -m basil capability <id>`

## Evidence boundary

Milestone 1 does **not** claim that BASIL is complete, deployed as a whole or finished as a product.

Open development remains ordinary post-milestone work, including full SYBIL orchestration, GRAIL automation, POLLY runtime integration, further Visual Execution development, Android build/device validation, broader FAWLTY automation and any explicitly reopened voice work.

The historical Visual Execution frontend source remains unrecovered. That is preserved as a source-lineage limitation, not silently reconstructed.

## Repository evidence

The cutover state immediately preceding this milestone is documented in:

- `docs/repository/MIGRATION_COMPLETENESS_2026-08-29.md`
- `docs/status/LINE_IN_THE_SAND_2026-08-29.md`
- `docs/learning/FAWLTY_ARCHAEOLOGY_PILOT_PROVENANCE.md`
- `src/basil/data/capabilities.json`

The migration-complete cutover commit is `9d877296c8e3b4c04ce1f084c47f0df56d09b380` and passed main verification run `33242286079`.

## Version marker

The executable core advances from `0.1.0` bootstrap status to `0.2.0` for this canonical baseline.

The preferred immutable Git tag remains `v0.2-canonical-baseline`. The connected GitHub toolset does not currently expose creation of tag refs and no additional installed plugin provides that mutation, so the exact Git commit remains the authoritative machine-verifiable milestone boundary until the tag is created manually or the tool surface changes.

## Transition

The migration programme is closed. Further work should be described and prioritised as BASIL development, validation, deployment or capability maturation rather than as migration debt unless genuinely newer authoritative historical implementation evidence is recovered.
