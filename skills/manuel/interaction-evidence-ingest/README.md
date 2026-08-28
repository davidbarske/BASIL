# Interaction Evidence Ingest v1.9 — migration record

**Owner:** MANUEL  
**Maturity:** operational contract, exercised in real meeting work  
**Exact current source:** ChatGPT File Library `INTERACTION_EVIDENCE_INGEST_SKILL_v1.9.md`, file id `file_00000000acd0820cb446327c6ae1a66f`

The exact v1.9 source has not yet been safely committed into this public repository. This file records the verified capability boundary without pretending this summary is the full skill.

Known contract:

- preserve original recording and native transcription evidence
- use STANDARD / ENHANCED / FORENSIC profiles with explicit declaration
- perform preflight before heavy processing
- preserve independent evidence layers rather than replacing one with another
- consolidate generated evidence into one SQLite database per recording
- retain original, normalised and corrected transcript state with provenance
- preserve speaker evidence and uncertainty rather than forcing identity
- support human adjudication for zero–three high-value questions at closure
- retain run-local and cumulative learning with provenance
- expose compact analytical views such as best transcript, one-second timeline, open anomalies and speaker evidence

The production meeting chain has been exercised across two real meetings. Exact skill migration and executable orchestration remain repository work.
