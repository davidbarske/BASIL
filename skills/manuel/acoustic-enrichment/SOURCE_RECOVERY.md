# MANUEL acoustic enrichment — exact-source recovery record

**Status:** EXACT HISTORICAL/TESTED SOURCE RECOVERED — PUBLIC-SAFE REFACTOR REQUIRED  
**Capability maturity:** TESTED supporting method  
**Repository migration state:** MIGRATING

## Recovered source

- File: `acoustic_enrich.py`
- Drive file ID: `1OjkfJBCOr4Gb15IFJsBrojrCYQTv0rN6`
- Drive repository area: `02_MEETING_PROCESSING_AND_INTELLIGENCE`
- Size: `28,942` bytes
- SHA-256: `938c1688f6c9c829370481c35093f3bd12c3585ad2703fb5f0bac64b3b0f33f8`
- Git blob SHA if committed byte-for-byte: `77e40693820144f36b3f3512f115ebd2ed35c622`

The exact recovered file is a staged empirical implementation rather than a clean reusable public module. Inspection shows hard-coded Meeting 02 paths and case-specific participant/project identifiers, including ARC, Adaiah and David. Because `davidbarske/BASIL` is public, the exact script must remain in the private Drive evidence/method repository rather than being copied byte-for-byte into GitHub.

## Migration treatment

Do not call the existing GitHub placeholder an exact-source migration. The next public-repository step is to extract/refactor the reusable acoustic-evidence mechanism into a case-neutral module, then validate that refactor against frozen meeting evidence before changing repository status to `canonical`.

The required gate is:

1. preserve this exact source in Drive with its hash and provenance;
2. produce a case-neutral implementation without private participant/project data or fixed `/mnt/data/MEETING_02...` paths;
3. demonstrate output compatibility on appropriate frozen test evidence;
4. document any intentional behavioural differences;
5. run repository verification/CI;
6. only then mark the public implementation canonical.

This is a public-repository boundary and packaging/refactor issue, not evidence that the tested acoustic method did not exist.
