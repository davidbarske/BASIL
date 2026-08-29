# MANUEL acoustic enrichment — source recovery and public migration

## Private empirical source

- File: `acoustic_enrich.py`
- Drive file ID: `1OjkfJBCOr4Gb15IFJsBrojrCYQTv0rN6`
- Size: `28,942` bytes
- SHA-256: `938c1688f6c9c829370481c35093f3bd12c3585ad2703fb5f0bac64b3b0f33f8`
- Expected byte-for-byte Git blob: `77e40693820144f36b3f3512f115ebd2ed35c622`

That exact tested file is deliberately **not** copied into this public repository. It contains hard-coded Meeting 02 paths and case-specific participant/project identifiers. It remains private provenance evidence in Drive.

## Public reusable implementation

The current public implementation is [`acoustic_enrich.py`](./acoustic_enrich.py).

- Public refactor SHA-256: `9b88e0ee96eb2a5f61f4f8ee518636cd078e341bb770f1d3d9a92c74fa9adbe9`
- Git blob: `9655dba310936eeec49a75283bab029c24d809e8`
- Case-specific paths/participants/source IDs removed
- Inputs and outputs are parameterised rather than bound to `/mnt/data/MEETING_02...`
- Historical skill-learning side effects are excluded from the reusable processor

The refactor preserves the acoustic algorithms rather than preserving case-specific orchestration. See [`VALIDATION.md`](./VALIDATION.md) for the empirical compatibility boundary.

## Canonicality boundary

The public implementation is repository-canonical at TESTED maturity because it satisfies the migration gate: exact private source preserved with provenance, case-neutral implementation produced, compatibility demonstrated against appropriate frozen empirical evidence, intentional differences documented and repository verification required before promotion to `main`.

This does not mean every possible recording has been reprocessed with the refactor. In particular, the full 107-minute Meeting 02 rerun was not completed within the available execution window and is not claimed as verified.
