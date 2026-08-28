# MANUEL diarisation v2 — exact-source recovery record

**Status:** EXACT SOURCE RECOVERED AND CANONICALISED  
**Capability maturity:** TESTED  
**Repository migration state:** CANONICAL

## Recovered source

- File: `diarise_meetings_v2.py`
- Drive file ID: `15LP5K5h6yX5YpsdOIkmNMt-FNQcse6cs`
- Drive repository area: `02_MEETING_PROCESSING_AND_INTELLIGENCE`
- Size: `66,544` bytes
- SHA-256: `6aae3e4200116aef7a8177fbfeada915620a27f28b8fb815bf1b3a36958454e8`
- Exact Git blob SHA: `0239ef918c5042da1c8702cccfaa3f38225316a2`
- Internal script version: `2.0.0`
- Model lineage: `pyannote/speaker-diarization-community-1`

The recovered file is complete through `raise SystemExit(main())`. Source inspection found no ARC, Adaiah, David, email-address or other case-specific participant identifiers. The only meeting names are generic CLI examples (`Meeting 01` / `Meeting 02`).

## Transfer verification

The source was recovered from private Drive, hashed locally and materialised on the short-lived migration branch from a compressed transfer payload. The materialisation step independently asserted the expected byte count, SHA-256 and Git blob SHA before writing the canonical file. GitHub subsequently reported the committed source blob as `0239ef918c5042da1c8702cccfaa3f38225316a2`, confirming byte-for-byte identity with the recovered source.

Temporary transfer payloads and the materialisation workflow are migration scaffolding only and are removed before promotion to `main`.
