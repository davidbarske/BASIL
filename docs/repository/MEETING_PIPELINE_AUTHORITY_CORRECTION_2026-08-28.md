# BASIL meeting-pipeline authority correction

**Date:** 28 August 2026  
**Status:** CURRENT MIGRATION CORRECTION

## Finding

Migration research recovered a later, explicit production freeze for the BASIL meeting-processing subsystem than the v1.9 material currently named in the GitHub capability registry.

The controlling production set is:

- `INTERACTION_EVIDENCE_INGEST_SKILL_v2.0_FINAL.md`
- `BASIL_MEETING_INTELLIGENCE_SKILL_v2.0_FINAL.md`
- `BASIL_INTERACTION_EVIDENCE_MEETING_INTELLIGENCE_OPERATING_STANDARD_v1.0_FINAL`

The companion `00_CURRENT_BASIL_MEETING_SKILLS.md` explicitly identifies the two v2.0 skills as the current controlling skills and states that v1.6-v1.9 are historical development/provenance only. The v1.0 FINAL operating standard likewise identifies v2.0 as controlling and v1.9 as legacy.

## Authority treatment

This supersedes migration notes and later handover summaries that continued to describe v1.9 as current. Those handovers remain useful recovery evidence but do not outrank the explicit final production freeze.

Do not migrate v1.9 into canonical GitHub paths as the current skill. Preserve v1.9 only as lineage/history where useful.

## Migration consequence

The Phase-3 migration target is corrected to:

1. recover and migrate the exact v2.0 FINAL Interaction Evidence Ingest source;
2. recover and migrate the exact v2.0 FINAL Meeting Intelligence source;
3. preserve the v1.0 FINAL operating standard as the controlling parent subsystem rule;
4. update registry/README/test references from v1.9 to v2.0 only when the corresponding canonical source is present;
5. retain `repo_status: placeholder` until the exact/reconciled v2.0 source reaches its canonical GitHub path and passes repository verification.

This correction changes version authority only. It does not alter the established MANUEL -> BRIAN ownership boundary, public/private repository boundary or the evidence semantics of the meeting pipeline.
