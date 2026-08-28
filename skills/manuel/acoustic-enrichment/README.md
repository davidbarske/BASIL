# MANUEL acoustic enrichment — migration record

**Known tested source:** `acoustic_enrich.py`  
**Maturity:** BUILT + TESTED supporting method  
**Repository status:** MIGRATING

Role: extract acoustic and quality-control evidence that can support later reconciliation and analysis. It is explicitly **not** a psychological inference engine.

The tested meeting evidence model includes dense acoustic frames/summaries, speech activity and measures such as MFCC/F0/HNR-related or proxy features, LPC/spectral evidence, SNR, clipping/dropout evidence where available. Deep acoustic passes remain conditional rather than routine blockers.

The exact tested source has now been recovered from Drive and hashed. See [`SOURCE_RECOVERY.md`](./SOURCE_RECOVERY.md). Inspection confirms that it is a case-specific empirical script with hard-coded Meeting 02 paths and participant/project identifiers. Because this repository is public, the exact private/case-specific script remains in Drive. A case-neutral reusable implementation must be extracted and validated before the public repository state can become canonical.
