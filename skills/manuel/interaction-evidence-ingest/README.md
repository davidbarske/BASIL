# Interaction Evidence Ingest v2.0 FINAL — migration record

**Owner:** MANUEL  
**Maturity:** production operational contract, empirically consolidated after ARC Meeting 01 and Meeting 02  
**Controlling source:** ChatGPT File Library `INTERACTION_EVIDENCE_INGEST_SKILL_v2.0_FINAL.md`, file id `file_00000000f0b88246a0d57c3ec37bf662`

The current production source is **v2.0 FINAL**. Earlier v1.6-v1.9 skill files are historical development/provenance only and are not controlling for new runs.

The exact v2.0 source has not yet been committed at the canonical GitHub skill path. This file therefore remains a migration record and must not be treated as the full skill.

Current controlling contract includes:

- preserve original media and native transcription as first-order evidence
- use STANDARD / ENHANCED / FORENSIC profiles with explicit declaration
- default to ENHANCED for multi-speaker meetings where named attribution matters
- perform preflight, source hashing, reuse and DIRECT/STAGED/BLOCKED execution classification
- keep full diarisation, BASIL Lightweight, acoustic/embedding, contextual and human-adjudication channels independent until reconciliation
- measure general acoustics early and aggregate named-speaker acoustics only after reconciliation
- preserve original, normalised, corrected and unresolved transcript states with provenance
- consolidate generated evidence into one SQLite substrate per recording
- retain recording-local speaker labels, disaggregated review classes and vector integrity checks
- evaluate zero-to-three high-value human calibration questions at evidence closure
- use explicit G0-G3 completion gates
- retain recording, participant/project and method learning with provenance and promotion states
- use the fixed six-part completion feedback contract

Parent production authority: `BASIL_INTERACTION_EVIDENCE_MEETING_INTELLIGENCE_OPERATING_STANDARD_v1.0_FINAL`.

Repository status remains **PLACEHOLDER** until the exact or deliberately reconciled v2.0 source reaches the canonical GitHub path and passes verification.
