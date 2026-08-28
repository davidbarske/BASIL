# Current operating rules

This file captures the stable operational semantics from the BASIL Operating Protocol v1.2, subject to later explicit decisions.

## Importance and Urgency

Keep separate 1–10 dimensions.

| Raw score | Importance | Urgency |
|---|---|---|
| 9–10 | Critical | Immediate |
| 6–8 | Important | Pressing |
| 1–5 | Relevant | Pending |

The upper band is scarce. Immediate means materially today-or-fail. Ordinary "urgent" normally maps to Pressing unless the consequences genuinely require immediate action.

## 3×3 sequence matrix

| Importance \ Urgency | Immediate | Pressing | Pending |
|---|---:|---:|---:|
| Critical | 1 | 2 | 5 |
| Important | 3 | 4 | 7 |
| Relevant | 6 | 8 | 9 |

The matrix number is a sequencing aid, not another importance or urgency score.

## Deadlines and dependencies

For significant work progressively record:

- hard deadline, if one actually exists
- practical target, if useful
- consequence of missing it

Never invent a deadline to fill a field. Dependencies can override naive ordering. Within the same matrix cell use dependency first, then actual deadline/target, then leverage/opportunity/financial effect, then ease/startability.

## Task states

- `ACTIVE` — authorised action can happen now
- `WAITING` — response, payment, document or external event is outstanding
- `SCHEDULED` — future trigger/date, no action required now
- `BLOCKED` — cannot progress until a dependency resolves
- `MONITOR` — no action now; watch for change
- `DONE` — completed; remove from active queue but preserve history

SYBIL owns current commitment/task control and sequencing. Logicators is retired.
