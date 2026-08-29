# BASIL v0.1 canonical task record

| Field | Type | Rule |
|---|---|---|
| id | UUID string | Stable identity |
| description | string | Required |
| state | enum | ACTIVE, WAITING, SCHEDULED, BLOCKED, MONITOR, DONE |
| project | string | Optional |
| nextAction | string | Optional |
| deadline | string/null | Optional; never manufactured |
| notes | string | Optional |
| createdAt | epoch ms | Set once |
| updatedAt | epoch ms | Updated on mutation |
| completedAt | epoch ms/null | Set only when DONE |

## Export envelope

- `format`: `BASIL_TASK_EXPORT`
- `schemaVersion`: `1`
- `exportedAt`: epoch milliseconds
- `tasks`: canonical task array

The schema deliberately avoids Importance, Urgency and other fields that v0.1 does not yet operationally implement. Later migrations should add fields explicitly rather than silently populating invented values.
