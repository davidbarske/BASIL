# BASIL

![BASIL working mark](assets/brand/basil-logo.svg)

BASIL is a strategic operating environment for turning messy real-world information into preserved evidence, intelligence, decisions, commitments, execution and learning.

This repository is the first live, testable BASIL implementation node. It is deliberately small. The aim is to make BASIL executable and inspectable without pretending that every documented capability is already software.

## Current architecture

The principal evidence path is:

`source → MANUEL evidence → BRIAN intelligence → BASIL operationalisation`

That is not the whole topology. The current subsystem responsibilities are:

- **BASIL** — controller and operational layer. Turns validated state and intelligence into action.
- **MANUEL** — source preservation, intake, transcription/diarisation evidence, reconciliation, provenance and structured Interaction Evidence.
- **BRIAN** — Meeting Intelligence, behavioural/relational intelligence, strategic interpretation and specialist evaluation lenses.
- **SYBIL** — commitments, task control, sequencing and anomaly/risk monitoring.
- **FAWLTY** — cross-system learning and calibration. Proposes material changes rather than silently rewriting other capabilities.
- **GRAIL** — protects strategic arcs and longer-horizon intent.
- **POLLY** — orchestrates integrations but is never source of truth.
- **Visual Execution Layer** — human-facing representation of canonical state, including the Strategic Pressure Map, AXIS4+1 and Gravity Channel concepts.

**Logicators is historical and retired.** Logic remains a system function but not a current BASIL subsystem.

## What actually runs now

The initial Python core is intentionally dependency-light and exposes three useful behaviours:

```bash
python -m basil priority 9 7
python -m basil capabilities
python -m basil doctor
```

`priority` implements the current 3×3 Importance × Urgency semantics. `capabilities` exposes the current capability catalogue and maturity. `doctor` verifies that the repository structure and registered local artefacts are actually present before the repository claims a healthy state.

Run tests with:

```bash
python -m unittest discover -s tests -v
```

## Repository doctrine

1. **Evidence before interpretation.** Capture and provenance precede synthesis.
2. **Evidence before claims.** Do not claim a build, write, send, fix, persistence event or completion without fresh evidence that proves it.
3. **Importance and Urgency stay separate.** Never invent deadlines or urgency merely to make a queue look complete.
4. **Capability maturity is explicit.** Documented, designed, built, tested and deployed are different states.
5. **Old material is evidence, not authority.** Do not revive historical tasks, statuses or architecture merely because a document contains them.
6. **GitHub is the live implementation/test node. Google Drive remains the durable record/evidence repository.** The two should converge through explicit reconciliation rather than silent duplication.
7. **This repository is public.** Personal evidence, client records, legal material, credentials and raw meeting data do not belong here.

## Current working areas

- `src/basil/` — executable core
- `skills/` — BASIL-owned skills plus isolated experimental skill adaptations
- `integrations/` — repository-level candidates and adoption experiments
- `docs/` — current architecture, governance, visual design and reconciliation notes
- `assets/` — public-safe BASIL visual assets
- `tests/` — executable verification

## Open-source experiments

The current experiment is deliberately non-exclusive. BASIL may:

- adopt an entire external repository,
- install selected upstream skills,
- adapt a narrow mechanism,
- study a pattern without importing it, or
- reject it after testing.

The first experimental candidates include Matt Pocock's skills, obra/superpowers, gstack, Taste Skill and Diagram Design. See `docs/open-source/EXPERIMENTS.md` and `THIRD_PARTY_NOTICES.md`.

## Status

**Bootstrap v0.1 — WORKING.** The repository has an executable task-priority core, capability registry, repository doctor, tests, governance/architecture baseline, visual assets and first laboratory skills. It does **not** yet contain every historical BASIL artefact or the complete production meeting-processing code chain. Missing material is identified rather than fabricated.
