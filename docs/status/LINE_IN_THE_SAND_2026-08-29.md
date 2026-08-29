# Line in the Sand — 29 August 2026

**Status:** CANONICAL MIGRATION BASELINE / CUTOVER  
**Repository authority:** GitHub `main` for BASIL system, capability, build and implementation state  
**Evidence authority:** Google Drive remains durable evidence/records storage for private, historical and heavyweight material

## SYSTEM

Current BASIL architecture is represented in GitHub as BASIL, MANUEL, BRIAN, SYBIL, FAWLTY, GRAIL, POLLY and the Visual Execution Layer. Logicators is retired/historical.

The principal evidence-to-action flow remains:

`MANUEL establishes and preserves what happened → BRIAN determines what it means → BASIL operationalises what should happen next`

SYBIL owns commitments, task control, sequencing and risk/anomaly handling. FAWLTY owns cross-system learning/calibration with explicit approval required before material cross-component change. GRAIL protects strategic arcs. POLLY orchestrates integrations but never becomes source of truth.

## BUILD

The current repository contains the operational/tested MANUEL → BRIAN meeting chain, tested SYBIL and FAWLTY core primitives, current BRIAN specialist skills, the recovered Android v0.1 source and the canonical Visual Execution prototype state/provenance.

The Visual Execution web prototype is correctly classified as **BUILT / previously deployed Phase 1 prototype**, not merely designed. Its historical frontend source has not been recovered and current deployment availability is not revalidated.

Android v0.1 is **BUILT / source canonical**. APK/build/device validation remains open and is not implied by repository migration.

GRAIL and POLLY are **ARCHITECTURAL / repository canonical**. Their mature runtimes do not yet exist; that is future build work rather than migration debt.

## OPERATIONS

GrillMe is formally adopted and tested. Ask the CEO remains a candidate with a positive live-use signal but ordinary-chat runtime activation remains unverified.

FAWLTY Archive Learning Pilot v0.2 remains a working archaeology programme in Drive. GitHub contains its public-safe provenance and discovery-before-learning boundary. No historical archaeology finding has been promoted into current BASIL canon merely because it was found.

The BASIL voice workstream remains explicitly paused and isolated. It is not active migration or build work.

## REPOSITORY

The capability registry has no remaining `placeholder` or `migrating` entries at cutover. Repository canonicality no longer implies software maturity: documented, architectural, built, tested, operational and candidate remain distinct evidence-supported states.

The packaged `src/basil/data/capabilities.json` remains the single canonical machine-readable registry. The earlier proposal for a second top-level registry is not adopted because it would create duplication or packaging complexity without current value.

Compact canonical retrieval is available through:

```bash
python -m basil context
python -m basil context --json
python -m basil capability <capability-id>
python -m basil capability <capability-id> --json
```

Completed working branches are housekeeping only. Where deletion cannot be executed through the connector, branch-local deletion markers identify safe disposable branches. The paused voice branch remains deliberately retained.

## UNRESOLVED / FUTURE

Future work includes full SYBIL orchestration, GRAIL automation, POLLY runtime, broader FAWLTY automation, further Visual Execution implementation, Android binary/device validation, skill-runtime binding work and selected external capability experiments. None of these is silently promoted in maturity.

The intended cutover tag is `v0.2-canonical-baseline`. The currently available GitHub connector does not expose tag creation, so that marker remains a technical/manual follow-up after the verified cutover commit. This does not represent missing capability content.

## LINE

The repository migration programme is closed when this cutover branch and then `main` pass verification and the exact transition is persisted to the Drive repository activity log. New work after that point is ordinary BASIL development, testing, capability adoption or archaeology — not continuation of the original migration by default.
