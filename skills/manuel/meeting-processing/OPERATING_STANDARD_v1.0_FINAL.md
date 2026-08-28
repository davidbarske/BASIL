# PROJECT BASIL
## Interaction Evidence, Transcription, Diarisation and Meeting Intelligence
### OPERATING STANDARD v1.0 FINAL

Empirically consolidated after ARC Meeting 01 and Meeting 02 | 24 August 2026

**STATUS:** FINAL PRODUCTION BASELINE  
**CONTROLS:** Interaction Evidence Ingest v2.0 FINAL + BASIL Meeting Intelligence v2.0 FINAL

> Repository note: this Markdown file is a text-normalised GitHub representation of the final production operating standard preserved in File Library as `BASIL_INTERACTION_EVIDENCE_MEETING_INTELLIGENCE_OPERATING_STANDARD_v1.0_FINAL.docx` (`file_00000000ff7482109147cff871c78055`). The original DOCX remains the source-format evidence artefact.

## 1. Purpose and authority

This document freezes the production operating model for BASIL meeting and interaction intelligence after two complete empirical ARC meeting runs. It replaces the Working Process Baseline v0.3 as the controlling parent process document. The earlier baseline remains historical development material.

The governing proposition is simple: BASIL is not fundamentally a transcription workflow. It is an interaction-evidence and intelligence pipeline that preserves the recording, recovers words and speaker activity, reconciles uncertainty, builds a reusable evidence substrate, produces human intelligence outputs, promotes valid commitments into BASIL and learns from validated corrections.

- Original recordings and native machine outputs remain evidence and are never silently overwritten.
- Machine speaker clusters are recording-local labels, not human identities.
- Independent evidence channels remain independent until reconciliation.
- Uncertainty is preserved when forcing certainty would reduce evidential integrity.
- Prior learning assists later meetings but never rewrites or dictates current evidence.
- The technical architecture may be deep; the user-facing process must remain short and intelligible.

## 2. Production architecture

| Stage | Layer | Controlling output |
|---|---|---|
| 0 | Source | Original recording, hash and metadata |
| 1 | Transcription | Native STT JSON/timestamp exports, preserved verbatim |
| 2 | Speech / acoustics / diarisation | Objective telemetry, speech activity, full diarisation, embeddings/fingerprints |
| 3 | Independent comparison | BASIL Lightweight speaker evidence where profile requires it |
| 4 | Reconciliation | Named attribution candidates, uncertainty classes, human adjudication where warranted |
| 5 | Interaction evidence | Final SQLite evidence substrate with provenance and learning state |
| 6 | Canonical transcript | Compact Word/PDF human transcript |
| 7 | Meeting Intelligence | Comprehensive evidence-disciplined report |
| 8 | BASIL handoff | Actions and commitments promoted with source lineage |
| 9 | Optional behavioural/interaction profile | Participant and interaction analysis from confidently attributed evidence |
| 10 | Learning | Recording-specific, participant/project and method learning |

## 3. User-facing workflow

The routine human workflow is: give BASIL the meeting. BASIL finds or admits the source, reuses valid existing evidence, processes only missing required layers, asks at most zero to three high-value calibration questions, freezes the evidence state, produces the canonical transcript and Meeting Intelligence Report, optionally produces the behavioural/interaction profile, promotes valid actions and retains learning.

| Step | Operation | Required behaviour |
|---|---|---|
| 1 | Intake and preflight | Resolve source, hash it, inventory native transcript/evidence and select profile. Reuse compatible completed work. |
| 2 | Transcription | Ingest or generate native STT. Preserve original text and timing. Record engine/model/parameters rather than making one implementation permanent. |
| 3 | Acoustic measurement | Measure general acoustics early on the source-derived analysis stream. Do not require named speakers. |
| 4 | Speaker processing | For ENHANCED multi-speaker meetings, run full diarisation and the BASIL Lightweight process independently. |
| 5 | Reconciliation | Align all evidence to one clock, map recording-local clusters to names with evidence, preserve mixed and unresolved states. |
| 6 | Calibration | Ask zero to three short user questions only when expected information value is high. |
| 7 | Evidence closure | Evaluate G0-G3, integrity, coverage, artifact completeness and cumulative learning. |
| 8 | Human outputs | Produce canonical Word/PDF transcript then Meeting Intelligence Report from the closed state. |
| 9 | Optional profile | If requested, derive behavioural/interaction profile from confidently attributed speech and longitudinal evidence. |
| 10 | BASIL + learning | Promote real commitments with lineage, update learning and surface one micro-improvement if justified. |

## 4. Profile selection is now frozen

| Profile | Use when | Speaker treatment |
|---|---|---|
| STANDARD | Single-speaker, already reliable labels, or person-level attribution not material. | Targeted speaker processing only under objective material-attribution triggers. |
| ENHANCED | Default for multi-speaker meetings when named attribution, quotations, actions, longitudinal learning or behavioural analysis matters. | Full Community-1/equivalent diarisation + independent BASIL Lightweight process + reconciliation + high-value calibration check. |
| FORENSIC | Legal/evidential contest, severe quality problems, materially disputed attribution/quotation or maximum-detail request. | ENHANCED plus denser/multiple evidence methods and targeted anomaly reinspection. |

Long duration triggers staging and checkpointing, not silent profile reduction. The two ARC tests demonstrated that multi-speaker meeting reports should not be finalised from contextual attribution alone when full speaker evidence can reasonably be obtained.

## 5. Speaker attribution and reconciliation

### 5.1 Evidence hierarchy

The hierarchy is qualitative, not a rigid score. Signal quality, overlap and mapping strength always matter.

1. Human adjudication at the exact segment, stored separately with provenance.
2. Clean full-diarisation exclusive boundary plus strongly evidenced recording-local cluster-to-person mapping.
3. High-quality voice embedding/acoustic similarity from clean speech.
4. BASIL Lightweight acoustic result.
5. Stable cross-meeting linguistic idiolect.
6. Local conversational turn logic, role and knowledge ownership.
7. Historical prior alone.

The Meeting 02 calibration sample supported the full Community-1 boundary in all three deliberately selected high-value disagreements. This changes default weighting, not the status of any method as ground truth.

### 5.2 Independent methods

Full diarisation and the BASIL Lightweight process must remain independent until comparison. Do not feed one current-run label set into the other before evaluating agreement/disagreement. The Lightweight process is retained because it is cheap, longitudinally useful and a strong error-localisation layer even when full diarisation receives greater default weight at clean boundaries.

### 5.3 Mixed boundaries are not failures

A native STT segment may physically cross two speakers. Such a segment is a mixed/speaker-transition case, not necessarily an attribution error. True unresolved attribution, mixed boundaries, transcript-quality review, cross-method disagreement and human calibration are separate metrics.

## 6. Acoustic evidence

General acoustic measurement runs early. Speaker-specific acoustic aggregation waits until the speaker map is reconciled. This prevents provisional identity assumptions contaminating objective signal data.

Production phrase: **Acoustic measurement early; speaker-specific acoustic aggregation after reconciliation.**

Persist profile-appropriate frame telemetry and a one-second summary layer.

Preserve speech activity, noise/SNR, clipping/dropout, pitch/F0, HNR or documented proxy, spectral measures, MFCCs and detected events where available.

Retain neural embeddings separately from non-neural MFCC-stat fingerprints and identify the model/type explicitly.

Validate vector dimensions, dtype and blob byte length. If inconsistent, preserve the declared metadata, flag the anomaly and record a byte-consistent inferred dtype separately rather than silently rewriting evidence.

Use acoustic features as evidence for attribution and longitudinal comparison, not as personality labels.

## 7. High-value calibration

At evidence closure BASIL evaluates residual uncertainty for expected information value of human clarification. It asks zero to three questions only. The user should never receive an 89-item review queue when a ten-second clip can answer the only question that materially matters.

Candidates are selected when uncertainty is material, the user is likely to know the answer authoritatively, the burden is small and the result can improve the current record or future participant/method learning. Audio questions should normally use an 8-20 second clip and should not reveal which method chose which speaker before the user answers.

Human answers become a new evidence layer. Raw STT, full diarisation and Lightweight evidence remain unchanged.

## 8. Longitudinal learning

| State | Meaning | Promotion logic |
|---|---|---|
| TENTATIVE | One observation or one evidence channel. | May guide attention but receives low attribution weight. |
| ACTIVE | Repeated clean evidence or authoritative human correction. | May assist current processing with provenance. |
| VALIDATED | Repeated across at least two recordings with independent support, or human adjudication plus corroborating evidence. | May be used as a substantial prior but remains subordinate to clean current evidence. |
| CONTRADICTED | Later evidence materially conflicts. | Do not delete; reduce/withdraw weight and preserve history. |
| SUPERSEDED | A better-supported learning state replaces it. | Retain lineage to the earlier state. |

Reusable participant learning may include canonical terminology, recurrent STT errors, clean voice references, acoustic distributions, stable linguistic markers, speaking-rate/turn-length patterns and role/knowledge patterns. Cross-recording linguistic markers become strong only when they persist across different content; topic and organisational-role vocabulary remains lower-weight evidence.

## 9. Canonical transcript and final human outputs

Every completed meeting produces a canonical Word transcript and matching PDF using the compact five-column table: Turn | elapsed time | wall-clock time | speaker | transcript. The transcript represents the current reconciled state. It deliberately excludes method-comparison commentary and acoustic telemetry, which remain in the evidence repository.

- All transcript text black, with restrained speaker-row shading for scanning.
- Elapsed timestamps authoritative; wall-clock times provisional when derived only from device/container metadata.
- Confirmed no-speech STT artefacts excluded from the spoken transcript but retained in raw evidence.
- MIXED or ? remains visible where uncertainty is genuine.
- Meeting Intelligence is generated only from the closed transcript/evidence pair, never from an obsolete pre-diarisation report.

## 10. Behavioural and interaction analysis

Behavioural/interaction profiling is an optional extension, not a hidden mandatory layer and not a claim that separate specialist skills ran when they do not exist. When requested, it reuses the final SQLite and confidently attributed speech.

- Turn-taking, interruption and question/answer patterns.
- Explanatory/model-building versus decision-closing behaviour.
- Challenge, correction, concession and scope-control patterns.
- Stable linguistic markers and confidently comparable acoustic/temporal patterns.
- Interactional influence versus formal decision authority.
- Change from prior meetings, with prior profiles treated as revisable hypotheses.

Do not diagnose personality, motives or private mental states. Ambiguous speech is unavailable evidence, not a licence to guess.

## 11. Repository and retention standard

| Folder | Purpose |
|---|---|
| 00_INDEX_AND_MANIFESTS | Repository guide, manifests, table/schema inventories and QA notes |
| 01_SOURCE_RECORDING | Original recording |
| 02_TRANSCRIPTION | Native STT artefacts and original transcription bundle |
| 03_DIARISATION | Full diarisation bundle and accessible principal outputs |
| 04_EVIDENCE_DATABASE | Final SQLite, calibrated derivative if any, schema/count exports |
| 05_ACOUSTIC_DATA | Detailed acoustic frames/summaries/events/speech/vector exports and dictionary |
| 06_RECONCILIATION_AND_CALIBRATION | Lightweight evidence, comparisons, disagreements and human adjudication |
| 07_CANONICAL_TRANSCRIPT | Current final Word/PDF transcript only |
| 08_INTELLIGENCE_AND_BEHAVIOURAL | Final Meeting Intelligence, optional profile and validated learning outputs |
| 09_METHODS_AND_RUN_PROVENANCE | Run-era scripts, skills and processor provenance |
| 90_BASELINES_AND_INTERMEDIATE | Superseded/provisional outputs retained for provenance |
| 99_ARCHIVE | Historical portable bundles only; never more authoritative than the live tree |

The repository is comprehensive without making the human transcript an audit log. For research-grade meeting records, detailed acoustic exports remain directly accessible in folder 05 in addition to the authoritative SQLite.

## 12. Run feedback and corrective learning

Every run ends with the same six headings: RUN STATUS; WHAT WAS PROCESSED; KEY RESULTS; EXCEPTIONS / UNRESOLVED ITEMS; WHERE THIS SITS IN BASIL; IMMEDIATE NEXT STEP.

Within IMMEDIATE NEXT STEP, BASIL evaluates two bounded opportunities: High-value calibration and Micro-improvement. The micro-improvement is exactly one small high-impact corrective/process improvement, or None warranted from this run.

Generic requests to update the skill after every run are retired; method-learning candidates are logged automatically and promoted only when generalisable evidence or explicit user approval supports promotion.

If more than one downloadable file is generated in a chat, BASIL also supplies one compact chat-specific ZIP. Large evidence archives remain separate.

## 13. Component decision register

| Component | Decision | Treatment |
|---|---|---|
| Original source + native STT | CURRENT / RETAIN | First-order evidence; immutable. |
| Transcription engine/model | CURRENT AS VERSIONED PROCESSOR | Do not block SOP on one Whisper notebook. Record engine/model/parameters per run. |
| diarise_meetings_v2.py | CURRENT | Verified local Community-1 runner. Replaceable later without changing the evidence contract. |
| BASIL Lightweight process | CURRENT | Independent comparator in ENHANCED multi-speaker runs where technically available. |
| Acoustic evidence layer | CURRENT | General measurement early; named-speaker aggregation after reconciliation. |
| SQLite interaction-evidence model | CURRENT / CONTROLLING | Operational in two full runs; implementation may be modularised later. |
| Canonical transcript Word/PDF | CURRENT / MANDATORY | Human-readable record pair. |
| BASIL Meeting Intelligence v2.0 | CURRENT / CONTROLLING | Final report layer. |
| Behavioural/interaction profile | OPTIONAL / CURRENT | Run on request from the final evidence state. |
| High-value human calibration | CURRENT / MANDATORY CHECK | Zero to three questions; zero is valid. |
| Cross-meeting participant learning | CURRENT | Explicit promotion states and current-evidence guardrails. |
| v1.9 skills | LEGACY | Preserve for historical provenance; superseded by v2.0. |
| Working Baseline v0.3 | SUPERSEDED | Historical development document; replaced by this v1.0 standard. |
| Older diarisation/merge scripts | LEGACY / RECOVERY | Not controlling. May be retained for compatibility or archaeology without blocking production. |
| Portable first-test archives | ARCHIVE ONLY | Historical provenance, never controlling over the live structured repository. |

## 14. Promoted empirical lessons from ARC Meeting 01 and Meeting 02

- Meeting 01 is the frozen calibration benchmark; Meeting 02 is the first generalisation case. Neither should be repeatedly retuned.
- Full diarisation plus an independent Lightweight arm provides useful triangulation and disagreement localisation.
- Meeting 01 learning modestly improved the Meeting 02 Lightweight held-out calibration without dominating the new run, supporting cumulative participant learning with guardrails.
- The three selected Meeting 02 human calibration questions all supported the clean full-diarisation boundary, justifying a weighting adjustment but not a ground-truth accuracy claim.
- Apparent review counts were misleading until true unresolved attribution, mixed boundaries, transcript-quality review and method disagreement were separated.
- Canonical transcripts should contain the resolved human record, not internal method comparison.
- End-of-run human feedback must be standardised and concise.
- A tiny human calibration burden can provide disproportionately valuable correction and learning.
- Acoustic/vector metadata needs its own integrity checks; declared dtype cannot be trusted blindly when blob size contradicts it.

## 15. What remains changeable after v1.0

Finalising this operating standard does not freeze every implementation forever. The following may evolve without reopening the architecture:

- Which STT engine/model is currently best, provided native output and provenance satisfy the transcription contract.
- Which full diarisation model replaces or complements Community-1.
- Which embedding model is available and how efficiently it is executed.
- Exact orchestration code/module packaging.
- Acoustic processor implementations, provided measurement provenance and integrity checks remain explicit.
- Profile thresholds when repeated empirical evidence supports a better cost/information trade-off.

Such changes are versioned processor or method changes. The process remains v1.0 unless the architecture, evidence hierarchy, output contract or learning doctrine materially changes.

## 16. Final operating principle

Capture reliably -> preserve evidence -> measure objectively -> reconcile independently -> ask the user only where their answer has high information value -> close the evidence state -> produce usable human intelligence -> promote only real commitments -> learn from validated reality.

The system is successful when it becomes more accurate and more useful over time while requiring less unnecessary user effort, not when it produces more files or invokes more processors.
