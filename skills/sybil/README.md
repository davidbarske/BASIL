# SYBIL task and commitment state model

**Owner:** SYBIL  
**Maturity:** TESTED core primitive  
**Scope:** commitments, task state and sequencing foundations

SYBIL owns commitments, task control, sequencing and anomaly/risk monitoring. This module implements only the currently supported task-state primitives. It does not pretend that the full SYBIL subsystem is operational.

## Canonical rules implemented

- Importance and Urgency are separate fields.
- Unknown Importance/Urgency remain unknown; BASIL does not manufacture scores to obtain a matrix position.
- Current task states are `ACTIVE`, `WAITING`, `SCHEDULED`, `BLOCKED`, `MONITOR` and `DONE`.
- Owner, deadline and dependencies are explicit fields and remain unset when unsupported.
- Dependencies are represented by task IDs; a task cannot depend on itself.
- Source references preserve lineage into evidence or decisions.
- `DONE` requires explicit completion evidence.
- The existing BASIL priority primitive classifies a task only when both Importance and Urgency are actually known.

## Deliberate boundary

Detailed universal transition sequencing has not yet been reconciled authoritatively. The implementation therefore does **not** invent a rigid state-transition graph. Non-DONE transitions preserve the record and may be applied when supported by canonical operational evidence. Completion is the current hard gate because BASIL's Evidence Before Claims doctrine requires evidence before a task is represented as complete.

The implementation lives at `src/basil/sybil.py` with focused tests in `tests/test_sybil.py`.
