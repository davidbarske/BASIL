# MANUEL acoustic enrichment — migration record

**Known tested source:** `acoustic_enrich.py`  
**Maturity:** built/tested supporting method

Role: extract acoustic and quality-control evidence that can support later reconciliation and analysis. It is explicitly **not** a psychological inference engine.

The tested meeting evidence model includes dense acoustic frames/summaries, speech activity and measures such as MFCC/F0/HNR-related or proxy features, LPC/spectral evidence, SNR, clipping/dropout evidence where available. Deep acoustic passes remain conditional rather than routine blockers.

Exact full source migration is pending recovery of the canonical script bytes.
