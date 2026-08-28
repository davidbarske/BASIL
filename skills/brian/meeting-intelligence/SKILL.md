---
name: basil-meeting-intelligence
description: >
  Produce the durable human intelligence record for a meeting from a finalised interaction-evidence substrate. Use when the user asks to analyse, report on, summarise, extract actions from, review, compare or profile a meeting. For multi-speaker meetings where named attribution matters, default to ENHANCED evidence processing unless a completed compatible evidence substrate already exists. Produce a canonical transcript and comprehensive Meeting Intelligence Report, preserve uncertainty, promote valid actions into BASIL and retain validated longitudinal learning.
argument-hint: "<meeting folder | recording | transcript | meeting name> [STANDARD | ENHANCED | FORENSIC] [BEHAVIOURAL PROFILE optional]"
---

# BASIL Meeting Intelligence

**Skill version:** 2.0 FINAL
**Status:** Production baseline after ARC Meeting 01 and Meeting 02 empirical tests

## 1. Mission

Turn a recorded interaction into a durable, evidence-disciplined intelligence record. The skill is not ordinary minutes and it is not a hidden transcription or diarisation engine.

The operating chain is:

`source -> interaction-evidence-ingest -> evidence closure -> canonical transcript -> Meeting Intelligence -> BASIL action handoff -> optional behavioural/interaction profile -> validated learning`

The skill consumes the best finalised evidence state available. It must not silently redo or override raw evidence merely to make a cleaner narrative.

## 2. Mandatory durable outputs

For a successfully closed meeting, produce:

1. **Canonical master transcript** in editable Word and matching printable PDF when document creation is available.
2. **Meeting Intelligence Report** in editable Word and matching PDF when document creation is available.
3. **Compact chat-specific ZIP** whenever more than one new downloadable file is produced in the chat.

If the user explicitly requests a behavioural/interaction profile, also produce it from the same finalised evidence state. Do not reprocess the complete recording merely for that extension.

Recommended filenames:

- `ARC_MEETING_<NN>_MASTER_TRANSCRIPT_<YYYY-MM-DD>_FINAL_CANONICAL.docx`
- `MEETING_INTELLIGENCE_REPORT_<PROJECT>_<MEETING-NAME-OR-NUMBER>_<YYYY-MM-DD>_FINAL.docx`
- `BASIL_BEHAVIOURAL_INTERACTION_PROFILE_<PROJECT>_<MEETING-NAME-OR-NUMBER>_<YYYY-MM-DD>.docx`

## 3. Profile selection

Every invocation must name STANDARD, ENHANCED and FORENSIC and state which profile is used.

### 3.1 STANDARD

Use when all of the following are broadly true:

- the interaction is single-speaker, or speaker labels are already reliable and do not materially affect downstream conclusions;
- person-level attribution is not central to the requested output;
- there is no material dispute about quotations, commitments or speaker identity;
- no behavioural/participant-level analysis requiring reliable named speech is requested.

STANDARD may escalate targeted speaker processing under objective triggers defined by `interaction-evidence-ingest`.

### 3.2 ENHANCED

**Default for multi-speaker meetings when named attribution matters.**

Use ENHANCED when any of the following applies:

- a meeting has two or more speakers and the report must identify who said what;
- actions, commitments, quotations or decisions require named attribution;
- a canonical named-speaker transcript is required;
- longitudinal participant learning is intended;
- a behavioural/interaction profile is requested;
- prior attribution problems or mixed speaker boundaries are expected.

This default reflects the empirical result from ARC Meetings 01 and 02: final human outputs benefited materially from full diarisation, independent comparison, reconciliation and targeted calibration.

### 3.3 FORENSIC

Use when the user explicitly requests maximum evidential treatment or when material stakes justify it, for example:

- legal, disciplinary or evidentially contested recordings;
- severe recording quality problems;
- disputed quotations or identity with material consequence;
- repeated disagreement among high-confidence methods;
- multi-channel or otherwise technically complex evidence where maximum recovery matters.

Do not use FORENSIC merely because a meeting is long.

## 4. Start-of-run feedback contract

Before substantive processing or reporting, render a concise block containing:

1. **Processing profile** - name all three profiles and show which is used.
2. **Evidence admitted / reused** - principal recording, transcript and compatible existing evidence.
3. **Execution state** - DIRECT, STAGED or BLOCKED / PARTIALLY UNAVAILABLE.
4. **Planned layers** - only the major evidence/reporting layers required for this invocation.

Do not hide profile or evidence state inside technical prose.

## 5. Evidence closure requirement

A report is final only when the companion evidence layer has passed G3 or has explicitly reached `COMPLETE_WITH_EXCEPTIONS` with bounded disclosed exceptions.

If G3 has not passed, any report must be labelled:

**PROVISIONAL / INCOMPLETE - DO NOT TREAT AS FINAL**

Meeting Intelligence must not perform silent speaker attribution from narrative intuition when the evidence layer is materially unresolved. It may use contextual interpretation only as an explicit evidence channel within reconciliation.

## 6. Speaker-attribution doctrine

### 6.1 Keep evidence channels separate

Never collapse these into one label before reconciliation:

- recording-local machine cluster, e.g. `SPEAKER_00`;
- full diarisation boundary / overlap evidence;
- neural embedding or acoustic similarity evidence;
- BASIL Lightweight process result;
- longitudinal linguistic/idialect evidence;
- conversational context, role and knowledge-ownership evidence;
- human adjudication.

A pyannote cluster number is recording-local. `SPEAKER_00` in one meeting must never be assumed to identify the same person in another meeting.

### 6.2 Default evidential weighting

Use the following qualitative hierarchy, subject to signal quality and overlap:

1. **Human adjudication for the exact segment**, preserved as a separate evidence layer.
2. **Clean full-diarisation exclusive boundary plus strongly evidenced recording-local cluster-to-person mapping.**
3. **High-quality embedding/acoustic similarity from clean speech references.**
4. **BASIL Lightweight acoustic speaker result.**
5. **Stable longitudinal linguistic markers demonstrated across recordings.**
6. **Conversational turn logic, role, knowledge ownership and local context.**
7. **Historical prior alone.**

This is not a rigid numeric score. A lower-ranked channel may override a higher-ranked one when the higher-ranked evidence is degraded, overlapping, poorly mapped or internally inconsistent.

The ARC Meeting 02 calibration sample supported the clean Community-1 boundary in all three deliberately selected high-value disagreements. Treat that as a weighting lesson, not an accuracy estimate.

### 6.3 BASIL Lightweight process

Call the independent comparator simply **the BASIL Lightweight process**.

In ENHANCED multi-speaker meeting processing, retain it as an independent comparison arm where technically available. Do not feed full-diarisation labels into it before comparison. Its principal value is:

- independent speaker evidence;
- disagreement localisation;
- longitudinal acoustic learning;
- failure tolerance if the full method is unavailable;
- targeted review, not automatic ground truth.

## 7. High-value human calibration micro-loop

After automated reconciliation and before freezing the human outputs, evaluate residual uncertainty for **expected information value of human clarification**.

Ask **zero to three questions only**.

Select a candidate only when:

- uncertainty is material to attribution, wording, a commitment, quotation, participant learning or method calibration;
- the user is likely to know the answer authoritatively;
- the answer can usually be obtained from an 8-20 second audio clip or a similarly small burden;
- resolving it adds more value than leaving the uncertainty explicit.

Do not reveal which automated method chose which speaker before the user answers unless that information is necessary to understand the question.

Store the response as human adjudication evidence with provenance. Never overwrite raw STT, raw diarisation or the independent Lightweight layer.

At completion, report separately:

- true unresolved attribution;
- mixed/speaker-transition segments;
- cross-method disagreements;
- transcript-quality review items;
- high-confidence disagreement candidates;
- high-value calibration candidates selected;
- human adjudications completed.

Never compare one undifferentiated review count across meetings.

## 8. Canonical master transcript contract

The canonical transcript is the human-readable representation of the current reconciled evidence state. It is **not** an audit log of processing methods.

### 8.1 Required forms

- editable Word (`.docx`);
- matching printable PDF (`.pdf`).

### 8.2 Default body

Use a compact five-column table:

`Turn | elapsed time | wall-clock time | speaker | transcript`

### 8.3 Formatting and evidence rules

- keep all transcript text black;
- use restrained speaker-row shading where it improves scanning;
- keep turn IDs stable;
- use compact spacing and efficient page geometry;
- elapsed timestamps are authoritative;
- wall-clock timestamps may be shown when a start time is known, but must be marked provisional if derived only from container/device metadata;
- show only the current reconciled speaker state, e.g. participant initials/name, `MIXED` or `?`;
- exclude confirmed no-speech STT artefacts from the spoken transcript while retaining them in the evidence substrate;
- do not display Community-1-vs-Lightweight commentary, classifier diagnostics or acoustic telemetry in the transcript;
- preserve genuine uncertainty rather than forcing a name;
- incorporate human adjudications only after they have been stored separately with provenance.

## 9. Meeting Intelligence Report

The report must allow a reader who did not attend to understand the material meeting without reading the raw transcript.

### 9.1 Front-page Meeting Snapshot

Use a compact orientation layer:

- **WHO** - principal attendees and roles where useful;
- **WHEN & WHERE** - date, time, duration and location/platform;
- **MEETING ESSENCE** - approximately 70-140 words capturing the strategic and human character of the exchange without inventing emotions, motives or private mental states.

### 9.2 Required report structure

Use this order, omitting only genuinely inapplicable subsections:

1. Meeting administration, identification and source basis
2. Executive synthesis
3. Key takeaways
4. Chronological meeting map
5. Detailed discussion by theme
6. Participant positions and contributions
7. Decisions, agreements and working consensus
8. Disagreements, tensions and competing views
9. Commitments and action items
10. Requests, promises and expected inputs
11. Open questions and unresolved matters
12. Risks, blockers, assumptions and dependencies
13. Opportunities, ideas and strategic possibilities
14. Notable phrases and exact quotes
15. What changed during the meeting
16. Follow-up plan
17. Suggested next-meeting agenda
18. Transcript uncertainties and verification points
19. Compact BASIL action register

### 9.3 Evidence classes

Internally classify substantive statements as:

- **E1 - Explicit evidence**: directly supported by transcript/evidence.
- **E2 - Strong contextual interpretation**: strongly supported but not verbatim.
- **E3 - Analyst inference**: useful interpretation introduced by the analyst.

E3 must never be presented as something a participant said, agreed or intended.

### 9.4 Decision states

Use precise states:

- Decided
- Agreed
- Working consensus
- Proposed
- Considered
- Deferred
- Rejected
- Unresolved
- Unclear

Do not use `agreed` merely because nobody objected.

### 9.5 Commitment discipline

An action item requires evidence that someone is expected to do something. Distinguish:

- explicit commitment;
- assigned/requested action;
- implied next step;
- analyst recommendation.

Never invent an owner or deadline.

Preserve relative timing such as `next week` or `before the next meeting` unless conversion to a date is unambiguous from the meeting date.

### 9.6 Exact quotations

Quote only when materially useful. Use the canonical transcript and final evidence state. Do not silently repair grammar inside quotation marks. If wording or attribution remains uncertain, state that.

## 10. Optional behavioural and interaction extension

When the user requests a behavioural/interaction profile, produce it from confidently attributed speech and the final evidence substrate.

Do not pretend that separate specialist skills ran unless they actually exist and were invoked.

The extension may analyse, where supported:

- turn-taking and interruption patterns;
- question/answer structure;
- explanatory versus decision-closing behaviour;
- challenge/correction patterns;
- topic-to-decision movement;
- role and organisational language;
- stable cross-meeting linguistic markers;
- reliably comparable acoustic/temporal speaking patterns;
- interactional influence versus formal decision authority;
- change from prior meetings.

Rules:

- do not diagnose personality or mental state;
- distinguish topic/role effects from likely idiolect;
- use only confidently attributed speech for participant-level linguistic claims;
- ambiguous/mixed material is unavailable evidence, not a licence to guess;
- prior profiles are hypotheses with provenance, not templates the new meeting must confirm.

## 11. Longitudinal learning contract

Prior learning may improve future attribution and interpretation but remains subordinate to current evidence.

### 11.1 Learning states

Use:

- **TENTATIVE** - one observation or one evidence channel;
- **ACTIVE** - repeated within clean evidence or supported by authoritative human correction;
- **VALIDATED** - repeated across at least two recordings with independent support, or authoritative human adjudication plus corroborating current evidence;
- **CONTRADICTED** - later evidence materially conflicts;
- **SUPERSEDED** - replaced by a better-supported state while history remains preserved.

### 11.2 What may persist

- canonical names and terminology;
- recurrent STT errors;
- clean voice references and acoustic distributions;
- characteristic linguistic markers that persist across recordings;
- typical speaking-rate/turn distributions;
- role/knowledge patterns, at lower weight;
- validated attribution corrections;
- method calibration evidence.

### 11.3 Guardrails

- never persist recording-local cluster numbers as identities;
- never allow a prior to manufacture a fact absent from the current recording;
- stable linguistic markers require cross-recording persistence before strong weighting;
- role/topic vocabulary is weaker evidence than distinctive idiolect;
- prior learning may be contradicted and must retain its history.

## 12. BASIL action handoff

The compact action register is the bridge into BASIL.

Only promote genuine commitments, assigned actions or low-inference administrative follow-through. Preserve source lineage.

BASIL task states remain:

- ACTIVE
- WAITING
- SCHEDULED
- BLOCKED
- MONITOR
- DONE

Do not invent importance, urgency or deadlines simply because a matter was discussed.

## 13. Completion feedback contract

Every completion or provisional checkpoint must use exactly these six headings, in order:

1. **RUN STATUS**
2. **WHAT WAS PROCESSED**
3. **KEY RESULTS**
4. **EXCEPTIONS / UNRESOLVED ITEMS**
5. **WHERE THIS SITS IN BASIL**
6. **IMMEDIATE NEXT STEP**

Within **IMMEDIATE NEXT STEP**, include two compact sub-items when applicable:

- **High-value calibration** - zero to three questions, or state that none justify user burden.
- **Micro-improvement** - one small, high-impact corrective/process improvement exposed by the run, or state `None warranted from this run`.

Do not end every run with a generic request to update the skill. Method-learning candidates should be logged automatically. Surface a proposed skill promotion only when the evidence is sufficiently general or the user explicitly asks for a method review.

## 14. Skill-method learning and promotion

At each run, inspect for a small generalisable improvement in:

- processor ordering;
- attribution weighting;
- failure handling;
- review targeting;
- output clarity;
- learning persistence;
- data validation;
- redundant computation.

A candidate may be promoted into the generic skill when:

- it is supported by at least two materially independent runs, or
- it fixes an unambiguous integrity defect, or
- the user explicitly approves promotion after reviewing the evidence.

Participant-specific facts never belong in this generic skill.

## 15. Repository and delivery contract

The human-facing transcript and report are separate from the technical evidence repository.

For a comprehensive meeting repository, use the standard folders:

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

Current final human outputs belong only in folders 07 and 08. Internal method evidence stays in 03-06. Superseded and experimental material belongs in 90 or 99.

If more than one new downloadable file is generated in a chat, also provide a compact chat-specific ZIP containing only those new outputs unless the user explicitly asks for a full evidence archive.

## 16. Quality gate

Before declaring a final Meeting Intelligence run complete, verify:

1. The selected profile was declared and appropriate for the interaction.
2. Multi-speaker named-attribution meetings used ENHANCED unless a completed compatible evidence state made rerunning unnecessary.
3. G3 passed or the run is explicitly `COMPLETE_WITH_EXCEPTIONS`.
4. Original recording and native STT remain untouched.
5. Machine clusters remain separate from named identity.
6. Material mixed/uncertain segments were not forced.
7. Human calibration, if used, is stored separately with provenance.
8. Review metrics are disaggregated.
9. Canonical Word and PDF transcript reflect the final evidence state.
10. The report uses the canonical transcript plus final evidence substrate, not an obsolete pre-diarisation draft.
11. Every substantive topic, decision and commitment is captured.
12. Owners/deadlines are not invented.
13. Analyst inference is visibly separated.
14. Exact quotations match the final transcript state.
15. Behavioural/profile claims, if requested, use confidently attributed speech and distinguish inference from observation.
16. Reusable learning was updated without overwriting raw evidence.
17. A high-value calibration opportunity was evaluated.
18. One micro-improvement was considered.
19. The mandatory six-part completion block was rendered.
20. A compact chat ZIP was supplied when more than one downloadable file was generated.

## 17. Style

Use British English.

Prefer dense, precise prose over generic corporate minutes. Preserve nuance, minority views, caveats and changes of mind. Use tables where they improve retrieval. Do not pad the report with generic statements such as `a productive discussion took place`.

The technical system may be sophisticated underneath. The user-facing experience should remain simple: **what ran, what happened, what remains uncertain, what matters and what happens next.**
