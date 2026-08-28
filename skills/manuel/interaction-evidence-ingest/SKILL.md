---
name: interaction-evidence-ingest
description: >
  Build the reusable, time-aligned evidence substrate for recorded interactions. Preserve original media and native transcription, ingest or generate objective acoustic and speech evidence, run profile-appropriate speaker processing, reconcile independent attribution channels, support bounded human calibration and store the final machine-readable record in SQLite with provenance and longitudinal learning. Use for meetings, calls, interviews, hearings, voice notes and other recorded spoken interactions.
argument-hint: "<recording | folder | Drive URL | meeting name> [STANDARD | ENHANCED | FORENSIC]"
---

# Interaction Evidence Ingest

**Skill version:** 2.0 FINAL
**Status:** Production baseline after ARC Meeting 01 and Meeting 02 empirical tests

## 1. Mission

Create one rigorous evidence substrate from a recording and its transcript artefacts so downstream reporting, quotation, action extraction, behavioural analysis and longitudinal learning do not need to repeatedly reinterpret the raw media.

Core rule:

> Preserve first. Measure before interpreting. Keep independent evidence channels independent until reconciliation. Learn only from validated evidence.

The default machine-readable output is:

`<recording-name>--INTERACTION_DATA.sqlite`

The original media and native transcription remain separate first-order evidence and are never overwritten.

## 2. Place in BASIL

Preferred sequence:

`recording/native STT -> interaction-evidence-ingest -> evidence closure -> canonical transcript -> basil-meeting-intelligence -> BASIL action handoff -> optional behavioural/interaction profile -> validated learning`

This skill supplies evidence. It does not itself decide what the meeting meant.

## 3. Processing profiles and automatic selection

Every invocation must explicitly name all three profiles.

### STANDARD

Use for single-speaker interactions, already reliable speaker labels or cases where person-level attribution is not material.

Mandatory when available:

- source inventory, hashes and media metadata;
- native transcript ingestion;
- transcript quality windows and anomaly flags;
- canonical recording clock;
- speech/non-speech activity and silence;
- amplitude/RMS/peak, clipping/dropout, noise floor and SNR;
- pitch/F0, voicing, intensity, HNR or documented proxy;
- selected formants where technically stable;
- zero-crossing and spectral descriptors;
- MFCC or equivalent compact descriptors;
- approximately 100 ms persistent acoustic telemetry;
- 1 second acoustic summaries;
- audio-event/anomaly detection;
- linguistic/temporal transcript features;
- learning update generation.

Targeted speaker processing becomes mandatory when a material statement, quotation, action or participant identity cannot otherwise be attributed adequately.

### ENHANCED

**Default for multi-speaker meetings when named attribution matters.**

Includes STANDARD and adds, when technically available:

- approximately 50 ms persistent acoustic telemetry;
- full Community-1 or equivalent diarisation across the recording;
- regular and exclusive diarisation outputs;
- overlap and speaker-change analysis;
- speaker embeddings / representative vectors;
- systematic acoustic speaker fingerprints from clean speech;
- speaker-similarity matrices;
- independent BASIL Lightweight speaker process;
- transcript-speaker reconciliation;
- richer linguistic fingerprinting over confidently attributed speech;
- high-value human calibration check;
- cumulative participant-learning update.

The full diarisation arm and BASIL Lightweight arm must remain independent until comparison. Do not seed one with the other's labels merely to increase agreement.

### FORENSIC

Includes STANDARD and ENHANCED and adds maximum evidential detail when justified:

- approximately 20 ms frames with approximately 10 ms hop where feasible;
- multiple materially distinct diarisation/embedding comparisons;
- multi-channel analysis where source channels exist;
- detailed noise/dropout/clipping mapping;
- intensive anomaly localisation and targeted source-audio reinspection;
- dense cross-method attribution evidence and high-resolution event boundaries.

Long duration alone is not a reason to select FORENSIC.

## 4. Mandatory profile declaration

Use these rendered declarations:

### STANDARD

**Processing profile: STANDARD**  
Standard: **USED**  
Enhanced: **NOT USED**  
Forensic: **NOT USED**

### ENHANCED

**Processing profile: ENHANCED**  
Standard: **USED AS BASELINE**  
Enhanced: **USED**  
Forensic: **NOT USED**

### FORENSIC

**Processing profile: FORENSIC**  
Standard: **USED AS BASELINE**  
Enhanced: **USED AS INTERMEDIATE LAYER**  
Forensic: **USED**

Do not silently downgrade a selected profile.

## 5. Preflight, execution state and reuse

Before heavy processing, inspect:

- original recording size, format, codec, duration, sample rate and channels;
- native transcript artefacts and their time horizon;
- existing compatible SQLite/run artefacts;
- processor/model availability;
- expected data volume;
- source hash and prior source-hash matches;
- whether the run should be DIRECT or STAGED.

Classify:

- **DIRECT EXECUTION**
- **STAGED EXECUTION**
- **BLOCKED / PARTIALLY UNAVAILABLE**

Long recordings should normally trigger staging/checkpointing rather than reduced evidence depth.

Reuse compatible prior work when source hash, processor version and relevant parameters match. Never recompute the complete recording merely because one downstream layer is missing.

## 6. Source and working-audio discipline

### 6.1 Original source

Preserve the original recording byte-for-byte. Record SHA-256 before substantive processing where possible.

### 6.2 Working streams

Decode only as required by processors. Prefer shared derivatives:

1. native-information PCM retaining source rate/channel structure where practical;
2. speech-model PCM, commonly mono 16 kHz, for STT/VAD/diarisation models;
3. specialised derivative only for a concrete incompatible processor requirement.

Do not claim that WAV conversion improves a lossy source.

### 6.3 Cross-environment equivalence

Two decoded PCM derivatives of the same original source may be byte-different because of decoder behaviour or container padding. The original source hash is controlling.

When derivatives differ:

- record both derivative hashes;
- compare duration and timebase;
- document any start/end padding difference;
- preserve alignment to one recording clock;
- do not treat byte inequality alone as evidence of a different recording.

## 7. Native transcription contract

Treat native transcription JSON as first-order machine evidence when present. Preserve original fields and text.

Maintain logically distinct states:

- `original_text`
- `normalised_text`
- `corrected_text`
- `unresolved_text`

Never destroy `original_text`.

Group shared decoder-window metadata where appropriate and preserve quality indicators such as:

- `temperature`
- `avg_logprob`
- `compression_ratio`
- `no_speech_prob`

Prioritise transcript review when anomalies affect names, organisations, numbers, money, dates, negation, commitments, decisions, technical terms, quotations or speaker attribution.

The transcription engine/model is an implementation choice, not a reason to keep the process specification provisional. Every run must record the actual engine, model, version and parameters used.

## 8. Acoustic processing contract

### 8.1 General measurement early

Run general acoustic measurement from the original-information working stream as early as practical. It does not require named speakers.

Capture profile-appropriate measures including:

- RMS/peak/dBFS;
- clipping and dropout indicators;
- silence/speech/voiced fractions;
- noise floor and SNR;
- F0/pitch and confidence where available;
- intensity;
- HNR/harmonicity or documented proxy;
- selected formants;
- zero-crossing rate;
- spectral centroid/bandwidth/rolloff/flatness/flux;
- MFCCs;
- abrupt acoustic changes and quality anomalies.

Always generate a 1 second summary layer.

### 8.2 Speaker-specific aggregation after reconciliation

Apply named-speaker acoustic summaries only after speaker labels have been reconciled sufficiently.

Operating phrase:

> **Acoustic measurement early; speaker-specific acoustic aggregation after reconciliation.**

Do not let an early provisional speaker map contaminate the raw acoustic measurements.

### 8.3 Vector integrity check

Every stored speaker vector must pass a structural integrity check:

- declared dimensions;
- declared dtype;
- blob byte length;
- expected bytes = dimensions x bytes per element.

If the declared dtype/dimensions conflict with the stored byte length:

- do not silently rewrite the raw record;
- flag the mismatch as an evidence/provenance anomaly;
- record a byte-consistent inferred dtype separately where reconstruction is possible;
- expose both declared and inferred states in exports.

This rule is promoted from the Meeting 02 repository QA finding.

## 9. Speech activity and diarisation

### 9.1 Full diarisation

When ENHANCED/FORENSIC runs, preserve:

- recording-local cluster labels;
- regular diarisation;
- exclusive diarisation;
- overlap evidence;
- speaker-change boundaries where available;
- model/configuration version;
- embeddings/representative vectors when exposed;
- run status, QC and artifact manifest.

Use reliable known-speaker count constraints where genuinely known.

### 9.2 Artifact completeness

A processor claiming full diarisation completion must verify the expected output set, not merely one summary file. Where the processor supports JSON, TSV and RTTM regular/exclusive outputs, missing expected artefacts must be flagged rather than silently reused as complete.

### 9.3 Recording-local identity

Never persist `SPEAKER_00`, `SPEAKER_01` or similar as a person identity across recordings.

## 10. BASIL Lightweight process

The BASIL Lightweight process is a separate, cheaper speaker-attribution arm using lightweight acoustic fingerprints plus contextual/linguistic reconciliation.

In ENHANCED multi-speaker meetings, run it independently where technically available.

It may use validated prior participant learning, but must not use current full-diarisation labels before the comparison phase.

Use it to:

- provide independent attribution evidence;
- locate disagreements;
- test longitudinal learning;
- provide fallback evidence;
- identify review candidates.

Do not describe its calibration accuracy as whole-meeting DER unless genuine ground truth exists.

## 11. Reconciliation and attribution fusion

Align all evidence to one recording clock.

Keep separate candidate evidence for:

- full-diarisation cluster/boundary;
- embedding/acoustic similarity;
- BASIL Lightweight result;
- longitudinal linguistic similarity;
- conversational context/turn logic;
- role/knowledge ownership;
- human adjudication.

### 11.1 Default weighting

Subject to quality and overlap:

1. human adjudication at the exact segment;
2. clean full-diarisation exclusive boundary plus strong recording-local identity mapping;
3. high-quality embedding/acoustic similarity;
4. BASIL Lightweight result;
5. stable cross-meeting linguistic idiolect;
6. local conversational/role/context evidence;
7. historical prior alone.

Context may resolve a full-method conflict when the full boundary is itself weak, overlapping or inconsistent. Do not blindly follow any method.

### 11.2 Review classes

Store separately:

- true unresolved attribution;
- mixed/speaker-transition segment;
- transcript-quality review;
- cross-method disagreement;
- high-confidence disagreement;
- high-value human-calibration candidate;
- completed human adjudication.

Do not aggregate these into one `review count` for cross-meeting performance comparison.

## 12. High-value human calibration

At evidence closure, evaluate unresolved items for expected information value.

Ask **zero to three** user questions only when a brief answer can materially improve the record or future learning.

Where audio is available, provide an 8-20 second clip with sufficient context.

Store:

- question ID;
- start/end timestamps;
- machine states before adjudication;
- user answer;
- answer confidence/provenance;
- resulting attribution/correction state;
- learning promotion decision.

Human adjudication is additional evidence, not destructive replacement.

## 13. SQLite output and required evidence classes

The final SQLite is the authoritative consolidated generated evidence substrate.

At minimum retain logical tables for:

- schema/run/processor state;
- source files and media streams;
- processing stages/chunks/coverage;
- transcript segments/windows/corrections;
- audio frames and one-second summaries;
- audio events and speech segments;
- speaker segments and embeddings;
- text/linguistic features;
- attribution candidates and method comparisons;
- anomalies and human adjudication evidence;
- learning updates, cumulative learning state and skill-method candidates.

Maintain convenience views equivalent to:

- best available transcript;
- one-second combined timeline;
- open anomalies;
- speaker evidence.

The exact executable/module implementing this contract may evolve. The evidence schema and behavioural contract are controlling.

## 14. Longitudinal learning

### 14.1 Learning classes

Distinguish:

1. **recording-specific evidence learning**;
2. **reusable participant/project/domain learning**;
3. **skill-method learning**.

### 14.2 Promotion states

Use:

- TENTATIVE
- ACTIVE
- VALIDATED
- CONTRADICTED
- SUPERSEDED

Suggested promotion logic:

- TENTATIVE: one observation or one channel;
- ACTIVE: repeated clean evidence in the same recording or authoritative human correction;
- VALIDATED: repeated across two or more recordings with independent evidence, or authoritative human adjudication plus corroborating machine/context evidence;
- CONTRADICTED/SUPERSEDED: preserve history rather than deleting it.

### 14.3 Reusable participant learning

May include:

- canonical names/terminology;
- recurring STT errors;
- validated voice references;
- pitch/intensity/acoustic distributions from clean attributed speech;
- stable characteristic words/phrases and discourse markers;
- speaking-rate/turn-length distributions;
- role/knowledge patterns at lower weight;
- corrected attribution patterns.

Cross-recording linguistic features must distinguish likely idiolect from topic/role vocabulary. A marker becomes stronger when it persists across different meeting content.

### 14.4 Prior use

Import only relevant validated/active learning with provenance. Current evidence remains free to contradict it.

Prior learning must never override a clean current full-diarisation boundary solely because the participant previously spoke differently.

## 15. Processing gates

### G0 - Preflight / admission

Pass when source, profile, processor availability, source identity and execution mode are recorded.

### G1 - Evidence coverage

Pass when every feasible processor required by the selected profile covered its intended range. Use `PASS WITH EXCEPTIONS` only for explicit technical failures/unavailability, not discretionary omissions.

### G2 - Reconciliation

Pass when transcript, diarisation, acoustic, Lightweight, chunks, overlaps and gaps are aligned to one recording clock and material attribution states are reconciled or explicitly unresolved.

### G3 - Finalisation

Pass when:

- SQLite integrity succeeds;
- WAL/temporary state is checkpointed;
- required indexes/views resolve;
- expected run artefacts are present or explicitly excepted;
- review classes are disaggregated;
- high-value calibration has been evaluated;
- cumulative learning state is updated;
- final status is `COMPLETE` or `COMPLETE_WITH_EXCEPTIONS`.

No downstream human report is final before G3.

## 16. Retention and repository contract

For comprehensive BASIL meeting repositories, retain:

- original source recording;
- native STT artefacts/bundle;
- full diarisation bundle and accessible principal outputs;
- final SQLite and any later human-calibrated derivative;
- detailed acoustic data in SQLite plus direct exports where the repository is intended to be comprehensive/research-grade;
- reconciliation/comparison/calibration records;
- canonical transcript Word/PDF;
- final Meeting Intelligence Word/PDF;
- behavioural/interaction profile if run;
- run manifest, relevant methods and run-era skill versions;
- validated learning snapshot/memo where useful.

Use the standard folders:

`00_INDEX_AND_MANIFESTS`
`01_SOURCE_RECORDING`
`02_TRANSCRIPTION`
`03_DIARISATION`
`04_EVIDENCE_DATABASE`
`05_ACOUSTIC_DATA`
`06_RECONCILIATION_AND_CALIBRATION`
`07_CANONICAL_TRANSCRIPT`
`08_INTELLIGENCE_AND_BEHAVIOURAL`
`09_METHODS_AND_RUN_PROVENANCE`
`90_BASELINES_AND_INTERMEDIATE`
`99_ARCHIVE`

Historical portable ZIPs are never more authoritative than the live structured evidence tree.

## 17. Completion feedback contract

Render these six headings exactly:

1. **RUN STATUS**
2. **WHAT WAS PROCESSED**
3. **KEY RESULTS**
4. **EXCEPTIONS / UNRESOLVED ITEMS**
5. **WHERE THIS SITS IN BASIL**
6. **IMMEDIATE NEXT STEP**

Within **IMMEDIATE NEXT STEP**, include:

- **High-value calibration** - selected questions or `None warranted`;
- **Micro-improvement** - exactly one small, high-impact improvement exposed by the run, or `None warranted from this run`.

Do not dump raw telemetry into chat.

If more than one new downloadable file is produced, also create one compact chat-specific ZIP containing those new outputs.

## 18. Skill-method learning

Log method-learning candidates automatically. Do not ask a generic skill-update question after every run.

Promote a candidate when:

- at least two materially independent runs support it;
- it fixes a clear integrity/provenance defect;
- or the user explicitly approves promotion after evidence review.

Examples of promoted lessons from ARC Meetings 01-02 include:

- multi-speaker named-attribution meetings default to ENHANCED;
- full diarisation and BASIL Lightweight stay independent until comparison;
- clean full-diarisation boundaries receive greater default weight than Lightweight contextual inference when mapping is strong;
- human calibration is bounded to zero to three high-value questions;
- review metrics are disaggregated;
- acoustic measurement precedes named-speaker aggregation;
- canonical human transcript is mandatory after evidence closure;
- embedding dtype/dimensionality is structurally validated.

## 19. Quality gate

Before declaring ingest complete, verify:

1. Profile declared and appropriate.
2. Original source and native STT preserved.
3. Source hash recorded.
4. Recording clock consistent across all layers.
5. Transcript raw fields preserved.
6. General acoustic telemetry and 1 second summaries exist at profile resolution.
7. Full diarisation ran when ENHANCED/FORENSIC required it, or has an explicit technical exception.
8. Expected diarisation artefacts are complete or explicitly excepted.
9. Cluster labels remain recording-local.
10. Full and Lightweight arms stayed independent before comparison when both were run.
11. Speaker-specific acoustic/linguistic summaries use reconciled labels.
12. Review categories are disaggregated.
13. High-value calibration was evaluated.
14. Human adjudications preserve pre-existing machine evidence.
15. Embedding vector dimensionality/dtype integrity was checked.
16. SQLite passes integrity checking.
17. Required views/indexes resolve.
18. G0-G3 were explicitly evaluated.
19. Learning state updated with provenance.
20. One micro-improvement was considered.
21. Completion feedback used the fixed six-part block.
22. A compact chat ZIP was supplied when multiple downloadable files were produced.

## 20. Operating principle

Prefer engineering simplicity over decorative architecture. The success criterion is not how many processors ran. It is the amount of trustworthy, reusable evidence retained per unit of computation and administrative burden.
