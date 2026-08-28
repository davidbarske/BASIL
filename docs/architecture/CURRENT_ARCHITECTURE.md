# Current BASIL architecture

**Status:** working architecture baseline, updated for the explicit 27–28 August 2026 decisions.

## Core responsibility model

### BASIL
Overall strategic operating environment and controller. Converts validated state and intelligence into operational next action. BASIL is not merely a chatbot and should not depend indefinitely on disconnected chat surfaces.

### MANUEL
Owns evidence intake and preservation:

- original-source preservation and provenance
- recording/transcript intake
- transcription/STT evidence
- diarisation and acoustic/temporal evidence
- speaker reconciliation and human adjudication
- correction/normalisation while preserving source history
- canonical transcripts
- structured Interaction Evidence / SQLite where appropriate
- evidence uncertainty and QC

MANUEL answers: **what happened and what evidence do we actually have?**

### BRIAN
Owns downstream intelligence and strategic analysis:

- Meeting Intelligence
- behavioural and interaction intelligence
- participant and relationship analysis
- power/influence analysis
- strategic interpretation
- longitudinal synthesis
- Pre-Engagement Intelligence, once recalibrated
- specialist Strategic Evaluation Skills
- predictions/hypotheses for later calibration

BRIAN answers: **what does the evidence mean?** It does not rewrite MANUEL evidence.

### SYBIL
Owns commitments, task control, sequencing and anomaly/risk monitoring. Detailed runtime remains under development.

### FAWLTY
Cross-system learning and calibration. Every material skill/workflow should close with a local learning step. Reusable lessons flow to FAWLTY. FAWLTY identifies recurring failures/gains and proposes material changes. It does not silently rewrite other components.

### GRAIL
Protects strategic arcs and longer-horizon intent. Mature automation is not yet proven.

### POLLY
Orchestrates integrations. It never becomes source of truth.

### Visual Execution Layer
Human-facing behavioural interface representing canonical state. The current design includes Strategic Pressure Map, AXIS4+1 and Gravity Channel. The interface should create behavioural/decision value rather than merely display a tidy dashboard.

## Retired architecture

**Logicators is retired/historical.** Older documents assigning priority/commitment logic to Logicators are lineage only. The underlying logic remains a BASIL function, with task/control ownership currently assigned to SYBIL.

## Meeting evidence path already demonstrated

The real tested meeting pipeline is approximately:

`recording → source preservation → transcription → diarisation → acoustic/QC evidence → optional independent attribution → reconciliation → high-value human calibration → canonical transcript → Interaction Evidence SQLite → BRIAN Meeting Intelligence → optional deeper analysis`

This chain has been exercised on two real meetings. The unfinished work is primarily production standardisation, packaging, automation and durable source migration, not proof that the concept can work.
