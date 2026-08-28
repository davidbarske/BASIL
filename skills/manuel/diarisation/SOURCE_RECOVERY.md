# MANUEL diarisation v2 — exact-source recovery record

**Status:** EXACT SOURCE RECOVERED — PUBLIC-REPO COMMIT PENDING  
**Capability maturity:** TESTED  
**Repository migration state:** MIGRATING

## Recovered source

- File: `diarise_meetings_v2.py`
- Drive file ID: `15LP5K5h6yX5YpsdOIkmNMt-FNQcse6cs`
- Drive repository area: `02_MEETING_PROCESSING_AND_INTELLIGENCE`
- Size: `66,544` bytes
- SHA-256: `6aae3e4200116aef7a8177fbfeada915620a27f28b8fb815bf1b3a36958454e8`
- Git blob SHA if committed byte-for-byte: `0239ef918c5042da1c8702cccfaa3f38225316a2`
- Internal script version: `2.0.0`
- Model lineage: `pyannote/speaker-diarization-community-1`

The recovered file is complete through `raise SystemExit(main())`. A source inspection found no ARC, Adaiah, David, email-address or other case-specific participant identifiers. The only meeting names are generic CLI examples (`Meeting 01` / `Meeting 02`). It is therefore suitable in principle for the public BASIL repository.

## Why it is not marked canonical yet

The exact bytes have been recovered and hashed, but the current GitHub connector used for this migration only accepts source content as an inline UTF-8 string and cannot ingest the recovered Drive file reference directly. Do not reconstruct this 66 KB script from search excerpts merely to close the migration flag.

The canonicality gate remains:

1. commit the recovered bytes without semantic modification at `skills/manuel/diarisation/diarise_meetings_v2.py`;
2. verify the committed Git blob is `0239ef918c5042da1c8702cccfaa3f38225316a2`;
3. run repository verification/CI;
4. only then change repository status from `migrating` to `canonical`.

This is a repository-transfer constraint, not a source-recovery gap and not a change to the capability's tested maturity.
