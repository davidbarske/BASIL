# BASIL agent operating rules

Use this file as the repository-level controller for coding and agent work inside BASIL.

## Authority

When sources conflict, use this order:

1. explicit current operator instruction or correction
2. current governing/reconciliation decision
3. canonical live evidence/task/project state
4. approved subsystem rules
5. working/tested material
6. historical archive
7. unsupported hypothesis

Determine status. Do not silently merge conflicts. Old material is evidence, not authority.

## Architectural boundary

Preserve the current ownership model:

- MANUEL establishes and preserves what happened.
- BRIAN determines what the evidence means.
- BASIL operationalises what should happen next.
- SYBIL owns commitments, task control, sequencing and anomaly/risk monitoring.
- FAWLTY owns cross-system learning/calibration and proposes material changes for approval.
- GRAIL protects strategic arcs.
- POLLY orchestrates integrations but never becomes source of truth.
- Visual Execution represents canonical state.
- Logicators is retired/historical. Do not recreate it as a subsystem.

These components interact in multiple directions. Do not reduce BASIL to a simplistic linear agent chain.

## Evidence and execution

Capture before cleaning. Preserve source wording, provenance, corrections and uncertainty before synthesis. Keep evidence, observation, inference, hypothesis, judgement and decision distinct.

Never invent deadlines, urgency, ownership, dependencies, completion, deployment or task state.

Before any material success/completion claim:

1. identify what evidence would prove the claim
2. obtain or run that evidence now
3. inspect the result
4. decide whether the evidence actually proves the claim
5. only then state the claim

## Build discipline

Prefer the smallest executable increment that teaches us something. Do not create framework or schema theatre.

State capability maturity accurately:

`DOCUMENTED → DESIGNED → BUILT → TESTED → DEPLOYED`

A design document is not a build. A committed file is not a running service. A passing unit test is not production deployment.

## Lightweight working branches

For substantive migration or build changes, use a short-lived `work/<topic>` branch from the current `main`. Keep the related change together, let the normal verification run on the branch and advance `main` only once that branch tip is green. Re-check `main` before promotion and never force-update it. Small documentation-only fixes may still go directly to `main`.

## Public repository boundary

This repository is public. Never commit:

- credentials, tokens, API keys or `.env` files
- private emails, legal records or personal task data
- raw meeting recordings or transcripts containing private material
- private SQLite evidence databases
- client-confidential documents
- generated profiles of identifiable people

Store sensitive evidence in the authorised private record system and reference it only through non-sensitive metadata where needed.

## Repository continuity

GitHub is the live implementation/test node. Google Drive remains the durable record/evidence repository for project decisions and records unless a later explicit decision changes that relationship.

Material GitHub changes should leave a corresponding durable BASIL record and activity-log entry. Verify both sides before calling a repository migration or major build step complete.
