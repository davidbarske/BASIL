# GitHub and Google Drive repository model

## Current decision

As of 28 August 2026, GitHub becomes BASIL's **live implementation and test node**. The existing `davidbarske/BASIL` repository is where executable code, public-safe skills, implementation documentation, tests, integration experiments and public-safe visual assets should increasingly live.

Google Drive remains necessary as BASIL's **durable record/evidence node**: source records, governing artefacts, decisions, reports, private evidence, archival bundles and material that does not belong in a public software repository.

This is not a declaration that Drive is obsolete or that GitHub alone is now canonical for every type of state.

## Division of labour

### GitHub
Best home for:

- source code
- tests and CI
- executable schemas and registries
- skills intended to be run or edited as code-like artefacts
- public-safe architecture documentation
- implementation status
- integration prototypes
- public-safe images/assets
- issues and build backlog

### Drive
Best home for:

- raw evidence and recordings
- private transcripts and intelligence outputs
- client/legal/personal records
- signed/final human documents
- governing decision records and repository activity log
- historical archives and preservation bundles
- material too large or inappropriate for public GitHub

## Reconciliation rule

A GitHub commit proves only what was committed. A Drive document proves only what was persisted there. Major BASIL state changes should explicitly reconcile both when both are relevant.

Do not duplicate private evidence into GitHub merely to make the repository look complete.
