# Line in the Sand — current migration state

**Updated:** 29 August 2026  
**Status:** CURRENT WORKING IMPLEMENTATION BASELINE

## System

Current architecture recognises BASIL, MANUEL, BRIAN, SYBIL, FAWLTY, GRAIL, POLLY and the Visual Execution Layer. Logicators is retired/historical. GitHub `main` is the live implementation/test node; Drive remains the durable record/evidence node for private, historical and heavyweight material.

## Migration boundary

Migration means bringing **existing current BASIL capability, code, governing state and proven implementation** into GitHub with correct provenance and maturity. It does **not** mean building every future BASIL subsystem before migration can finish.

This distinction matters: several remaining registry entries are architectural because the mature implementation does not yet exist. Those are future build work, not an endless migration backlog.

## Canonical / migrated now

- Interaction Evidence Ingest v2.0 FINAL
- Community-1 diarisation runner v2, exact recovered source
- public-safe acoustic enrichment refactor with bounded compatibility validation
- BASIL Meeting Intelligence v2.0 FINAL
- Behavioural / Interaction Profile routed through the current Meeting Intelligence v2.0 extension
- Hughes Strategic Evaluation
- Greene Strategic Evaluation
- Carnegie-Rory Strategic Evaluation
- SYBIL tested task-state core primitive
- FAWLTY tested learning/calibration core primitive and approval gate
- Evidence Before Claims core skill
- current LABS skill candidates and external integration records already registered as repository-canonical at their stated candidate maturity

## Existing material still to reconcile or migrate

The remaining **actual migration** is much smaller than the original plan implied:

1. **BASIL controller/governance reconciliation** — confirm that the current GitHub controller/governance files fully reflect the latest authoritative Drive decisions, then mark the controller canonical.
2. **Visual Execution source recovery** — reconcile and migrate the latest proven web prototype source and the Android v0.1 vertical slice. The current GitHub visual document is design authority, not proof that those implementation sources are migrated.
3. **FAWLTY working-pilot evidence** — the executable core now exists in GitHub, but the current archive-learning/archaeology working material remains primarily in Drive and should be represented through appropriate public-safe capability/provenance records rather than copied wholesale.
4. **Registry/cutover cleanup** — remove stale migration wording, decide whether the machine-readable registry should move to the planned top-level location and produce the first coherent canonical cutover/tag once the remaining current-source items above are resolved.

## Future build, not migration blockers

These should not be counted as unfinished migration unless newer authoritative implementation evidence is recovered:

- full SYBIL orchestration, sequencing engine and anomaly/risk automation beyond the tested task-state core
- GRAIL strategic-arc automation
- POLLY integration orchestration runtime
- broader FAWLTY automated learning flows beyond the tested core and current working archaeology pilot
- further external-repository adoption experiments
- future Visual Execution behaviour and client development after the existing source is recovered

## Repository housekeeping

Short-lived `work/<topic>` branches are temporary verification scaffolding and should be removed after successful promotion when they contain no unique work. Paused/abandoned experiments may remain isolated where preservation has value.

The British-anchor voice branch is deliberately retained as PAUSED / INCOMPLETE / NON-CANONICAL evidence and must not be merged unless the voice workstream is explicitly reopened.

## Immediate next order

1. finish current branch housekeeping where the available GitHub interface permits it
2. reconcile controller/governance current state
3. recover the actual current Visual Execution web and Android sources
4. reconcile FAWLTY pilot provenance into GitHub without importing private/archive rubble
5. perform registry/cutover cleanup and produce the first coherent canonical-baseline tag

At this point the major MANUEL → BRIAN production chain and the first executable SYBIL/FAWLTY cores are no longer migration gaps.
