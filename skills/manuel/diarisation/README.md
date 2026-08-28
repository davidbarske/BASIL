# MANUEL diarisation v2 — migration record

**Known tested source:** `diarise_meetings_v2.py`  
**Model lineage:** `pyannote/speaker-diarization-community-1`  
**Script version reported in source:** 2.0.0  
**Maturity:** TESTED on real BASIL meeting audio  
**Repository status:** MIGRATING

Verified design goals from the current source include source preservation, progress/run-state visibility, safe resumability, portable JSON/TSV/RTTM evidence, QC metrics, representative speaker embeddings when exposed and cross-meeting embedding similarity when multiple recordings are processed.

The exact source has now been recovered from Drive and hashed. See [`SOURCE_RECOVERY.md`](./SOURCE_RECOVERY.md). It is public-safe in principle but is not yet committed byte-for-byte at its final GitHub path, so this capability is deliberately not marked repository-canonical yet.
