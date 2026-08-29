# BASIL repository state

Current cutover authority is `MIGRATION_COMPLETENESS_2026-08-29.md` together with the latest GitHub `main` state.

`CAPABILITY_MIGRATION_AND_CANONICALITY_PLAN.md` is retained as the execution plan and migration history. Its phase language and original immediate-next-action list should not be read as current backlog after cutover.

Repository authority division:

- GitHub `main` — current public-safe BASIL architecture, capability definitions, skill/code source, build state, maturity state and implementation documentation
- Google Drive — durable private/raw evidence, historical archives, heavyweight artefacts and source evidence referenced from canonical GitHub records

The single machine-readable capability registry remains `src/basil/data/capabilities.json` by deliberate cutover decision.
