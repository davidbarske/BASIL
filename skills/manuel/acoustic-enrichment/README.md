# MANUEL acoustic enrichment

**Owner:** MANUEL  
**Maturity:** TESTED supporting method  
**Repository status:** CANONICAL

`acoustic_enrich.py` is the public-safe reusable acoustic-evidence processor extracted from the empirically tested Meeting 02 implementation. It preserves the tested acoustic/QC mechanism while removing meeting-specific paths, participant/project identifiers, source IDs and skill-learning side effects.

Its role is evidential: acoustic frames and summaries, speech activity, quality measures, spectral evidence, MFCC fingerprints and related comparison support. It is **not** a psychological inference engine.

The exact case-specific empirical source remains private in Google Drive as provenance evidence. See [`SOURCE_RECOVERY.md`](./SOURCE_RECOVERY.md) and [`VALIDATION.md`](./VALIDATION.md).

Canonical repository status means this is the current public BASIL implementation of the acoustic-enrichment method. It does **not** promote maturity beyond TESTED. The public refactor was matched exactly to the historical implementation on an appropriate frozen Meeting 02 evidence window after preserving the one-second look-ahead required at the comparison boundary. A complete 107-minute refactor rerun has not been claimed.
