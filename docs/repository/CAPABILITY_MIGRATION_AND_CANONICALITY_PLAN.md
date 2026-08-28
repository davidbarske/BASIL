# PROJECT BASIL — CAPABILITY MIGRATION & CANONICALITY PLAN

**Date:** 28 August 2026  
**Status:** WORKING EXECUTION PLAN  
**Target:** `davidbarske/BASIL` becomes the canonical source for BASIL system, capability, build and implementation state.

## 1. Objective

Move BASIL from a Drive/chat-centred capability estate into a GitHub-centred implementation estate without losing provenance, evidence or historical lineage.

The target operating model is:

- **GitHub `main`** = canonical source for BASIL architecture, capability definitions, skill source, executable code, build state, maturity state, integration state and implementation documentation.
- **Google Drive** = durable evidence/records repository for raw and sensitive evidence, historical archives, heavyweight artefacts, meeting records, legal/client/personal material and source evidence that should not live in a public code repository.
- **Chats and Project surfaces** = consumers/controllers. They assess claims about BASIL capabilities against the current GitHub canonical state rather than reconstructing BASIL from chat memory or scattered Drive artefacts.

This is a scope-specific authority change. It does not make GitHub the source of truth for raw private evidence or every live personal/project record.

## 2. Governing rule during migration

GitHub is the **target authority**, but it must not be treated as complete merely because a placeholder exists.

Every registered capability therefore needs two independent states:

1. **Capability maturity** — documented | designed | built | tested | operational/deployed | retired.
2. **Repository migration state** — placeholder | migrating | canonical | retired.

A capability may historically be operational while its GitHub migration state is still `placeholder`. This distinction prevents the current bootstrap registry from overstating what has actually been migrated.

Until a capability reaches `repo_status: canonical`, Drive/file-library evidence may be used to recover and reconcile the source. After cutover, Drive copies become evidence/history only unless the canonical GitHub record explicitly references them.

## 3. Canonicality contract

A capability is canonical in GitHub only when all applicable conditions are satisfied:

1. Exact current source has been recovered or deliberately reconstructed from authoritative evidence.
2. Provenance and lineage are recorded.
3. Current owner/subsystem is correct.
4. Sensitive or private material has been removed, parameterised or kept behind a Drive reference.
5. The canonical skill/code/document exists at the registered path.
6. Dependencies and invocation/entry points are explicit.
7. Maturity is supported by evidence rather than inherited wording.
8. Tests, examples or validation checks exist where the capability is executable.
9. `basil doctor` verifies the registry entry and required files.
10. The capability entry is marked `repo_status: canonical`.
11. The change is committed to `main` and the commit is the auditable state transition.

A README or migration note is not sufficient evidence that the underlying capability has migrated.

## 4. Repository structure

Preserve the current skeleton and make it authoritative rather than replacing it with another elaborate hierarchy.

```text
BASIL/
├── README.md
├── AGENTS.md
├── src/basil/                  # executable BASIL core
├── skills/
│   ├── core/                   # cross-system BASIL gates/primitives
│   ├── manuel/                 # evidence establishment/preservation
│   ├── brian/                  # intelligence and specialist evaluation
│   ├── sybil/                  # commitments, sequencing, risk control
│   ├── fawlty/                 # learning/calibration
│   └── labs/                   # experiments not yet promoted
├── integrations/               # repository/package adoption experiments
├── docs/
│   ├── architecture/
│   ├── governance/
│   ├── visual/
│   └── repository/
├── assets/
├── tests/
└── registry/                   # target home for machine-readable state
```

The current `src/basil/data/capabilities.json` should be migrated to a top-level `registry/capabilities.json` once the schema below is stable. The runtime should read that file rather than maintaining a second embedded catalogue.

## 5. Capability record

Each capability should have one machine-readable registry record. Minimum useful fields:

```json
{
  "id": "brian.meeting-intelligence",
  "name": "BASIL Meeting Intelligence",
  "owner": "BRIAN",
  "kind": "skill/product",
  "version": "1.9",
  "maturity": "operational",
  "repo_status": "canonical",
  "canonical_path": "skills/brian/meeting-intelligence/SKILL.md",
  "entry_point": null,
  "depends_on": ["manuel.interaction-evidence-ingest"],
  "source_lineage": ["Drive file id / prior version / commit"],
  "evidence_refs": ["Drive evidence identifier"],
  "sensitivity": "public-safe",
  "last_verified": "2026-08-28"
}
```

Do not overload maturity to mean repository presence. `maturity` and `repo_status` answer different questions.

## 6. Migration sequence

### Phase 0 — Establish migration controls

**Purpose:** prevent the migration itself from creating a new ambiguity problem.

Actions:

- Add `repo_status` and canonical-path validation to the capability schema.
- Move the registry to a single top-level canonical file after schema validation.
- Update `basil doctor` so it fails on dangling canonical paths, invalid maturity values, duplicate IDs or a capability marked canonical without its source present.
- Define `main` as the canonical branch.
- Use `skills/labs/` and integration branches/directories for experiments until promotion.
- Record the GitHub/Drive division of authority in the controller/governance material.
- Resolve the repository visibility question before importing sensitive capability material. The repository is currently public, so private examples, personal evidence, client material, credentials and legal/meeting source data must not be committed.

**Exit gate:** canonicality rules are machine-checkable.

### Phase 1 — Build the definitive capability inventory

**Purpose:** one list, no hidden skills.

Start from the current GitHub registry and reconcile against:

- current BASIL controller/governing material;
- current Drive capability/status inventory;
- MANUEL meeting-processing lineage;
- BRIAN specialist skills and behavioural/interaction capabilities;
- SYBIL, FAWLTY, GRAIL, POLLY and Visual Execution state;
- known tested scripts and prototypes;
- current open-source experiments;
- useful live artefacts not yet represented in GitHub.

For each item assign:

`KEEP / MERGE / MIGRATE / REBUILD / EXPERIMENT / RETIRE / HISTORICAL ONLY`

Do not copy every old artefact. Migrate the current capability and preserve history through provenance pointers.

**Exit gate:** every material BASIL capability has one stable ID and one declared migration disposition.

### Phase 2 — Migrate governing system state first

Before migrating dozens of skills, make the repository tell every future chat what BASIL currently is.

Priority order:

1. current controller kernel;
2. current architecture and subsystem responsibility map;
3. current reconciliation decisions;
4. capability maturity/canonicality doctrine;
5. repository authority/cutover rule;
6. Visual Execution governing concept/status.

Historical baselines remain linked as lineage, not merged into current canon.

**Exit gate:** a new chat reading only GitHub can correctly answer what BASIL is, what each current subsystem owns and which historical concepts are retired.

### Phase 3 — Migrate the working MANUEL → BRIAN chain

This is the highest-value capability migration because it already represents real tested/operational BASIL behaviour.

Recover exact current sources and migrate in dependency order:

1. `INTERACTION_EVIDENCE_INGEST_SKILL_v1.9`
2. tested diarisation runner (`diarise_meetings_v2.py`)
3. acoustic evidence enrichment/QC tooling
4. speaker reconciliation and canonical transcript rules
5. `BASIL_MEETING_INTELLIGENCE_SKILL_v1.9`
6. Behavioural / Interaction Profile
7. relevant tests, fixtures and public-safe synthetic examples

Private meeting data stays in Drive. GitHub contains schemas, pipeline logic, tests and synthetic fixtures.

**Exit gate:** a clean checkout can understand and, where dependencies permit, execute/test the meeting-evidence → intelligence workflow without retrieving its operating instructions from Drive.

### Phase 4 — Migrate BRIAN specialist skills

Migrate exact current source for:

- Hughes Strategic Evaluation
- Greene Strategic Evaluation
- Carnegie-Rory Strategic Evaluation
- any other specialist lens that has reached a genuine working state

Standardise only the shared envelope: metadata, invocation, evidence boundary, output contract, tests/examples and lineage. Do not homogenise the analytical substance merely to make the files look alike.

**Exit gate:** each skill is directly invokable/discoverable from the repository and registry, with its maturity correctly stated.

### Phase 5 — Build SYBIL and execution primitives around canonical state

Move from architectural ownership to working capability:

- task/commitment data contract;
- separate Importance and Urgency fields;
- sequencing/dependency representation;
- status transitions and completion evidence;
- anomaly/risk monitoring hooks;
- Evidence Before Claims as a cross-system completion gate.

Use the existing executable priority primitive as the seed, not as evidence that SYBIL is already built.

**Exit gate:** the repository contains a testable commitment/task state model and can distinguish planned, active, blocked, waiting and complete without invented state.

### Phase 6 — Migrate FAWLTY learning and capability calibration

Define the smallest executable learning contract:

`process closes → local lesson → outcome/prediction comparison → FAWLTY record → proposed change → approval required for material push-back`

Keep learning evidence distinct from automatic self-modification.

**Exit gate:** skills can emit standardised learning/calibration records and BASIL can compare planned/predicted vs actual outcomes.

### Phase 7 — Visual Execution and clients

Bring the existing web prototype and Android vertical slice into the repository only after identifying the actual current source versions.

Targets:

- web Visual Execution prototype;
- Strategic Pressure Map;
- AXIS4+1;
- Gravity Channel;
- Android task interaction vertical slice;
- shared canonical state/data contracts.

The UI must consume canonical state rather than become a separate source of truth.

**Exit gate:** at least one interface reads the same canonical BASIL state model used by the core/tests.

### Phase 8 — External skills and repository adoption

Treat external work with three different technical patterns rather than one blanket policy.

**Whole repository/package adoption**
- pin an upstream version/commit;
- preserve licence and attribution;
- isolate configuration/adapters in `integrations/`;
- avoid silently forking unless BASIL-specific changes require it.

**Selected upstream skill adoption**
- vendor the exact upstream skill or install it through its supported package/skill mechanism;
- record upstream repo, commit/version and licence;
- keep BASIL-specific wrapper separate.

**Adapted mechanism**
- BASIL-owned skill lives under `skills/labs/` during testing;
- lineage names the upstream source and extracted mechanism;
- promote only after testing.

Immediate candidates:

- Grilling / Grill-Me
- Verification Before Completion → BASIL Evidence Before Claims
- Research
- Systematic Debugging
- Writing for Agents
- gstack CEO/strategic review and code-review mechanics
- Handoff
- Taste Skill full-package trial
- Diagram Design full-package trial

**Exit gate:** every imported/adapted capability has clear provenance, licence, update path and promotion/rejection status.

### Phase 9 — Chat and Project retrieval contract

This is what makes GitHub the practical single reference point rather than merely a better folder.

For BASIL capability/system questions, every chat/controller should follow:

1. Read the latest `main` canonical-state/registry files.
2. Record the commit SHA used for the answer when state matters.
3. Resolve the relevant capability ID(s).
4. Fetch the registered canonical source path.
5. Inspect `maturity` and `repo_status` before making build/deployment claims.
6. Use Drive only for evidence explicitly referenced by the canonical capability or for private/raw records outside GitHub's scope.
7. If GitHub and an old Drive/chat document conflict on capability state, GitHub `main` wins after cutover unless David explicitly corrects it.

Add a compact command such as:

```bash
python -m basil context
python -m basil context --json
python -m basil capability brian.meeting-intelligence
```

The context command should emit the minimal architecture, registry version, current capabilities, maturity and canonicality state needed to orient another chat/tool.

**Exit gate:** a new BASIL chat can establish current capability state from the repository without asking David or searching historical Drive artefacts.

### Phase 10 — Cutover and cleanup

Cut over only when the migration completeness report proves that critical capabilities are canonical.

At cutover:

- mark GitHub `main` as canonical for BASIL system/capability/build state;
- change Drive capability copies to `HISTORICAL / EVIDENCE COPY — CURRENT SOURCE IN GITHUB` rather than deleting them;
- insert GitHub path/commit references into the Drive repository index/activity record;
- stop updating duplicate Drive copies of canonical skills/code;
- retain Drive for source evidence, private operational records and archival preservation;
- tag the first coherent cutover state, e.g. `v0.2-canonical-baseline`.

**Exit gate:** there is exactly one place to edit a capability definition or implementation: GitHub.

## 7. Migration waves

### Wave A — Canonical skeleton and authority

- registry schema + `repo_status`
- doctor validation
- controller kernel
- architecture
- current decisions
- canonicality/cutover rules

### Wave B — Proven working chain

- Interaction Evidence Ingest v1.9
- diarisation
- acoustic evidence
- Meeting Intelligence v1.9
- Behavioural / Interaction Profile

### Wave C — BRIAN specialist capability

- Hughes
- Greene
- Carnegie-Rory
- remaining working analytical skills

### Wave D — Execution and learning

- SYBIL state model
- Evidence Before Claims
- FAWLTY learning/calibration contract
- capability discovery/runtime binding

### Wave E — Interfaces and external capability

- Visual Execution web source
- Android v0.1
- Taste Skill
- Diagram Design
- gstack / Matt Pocock / Superpowers experiments

## 8. Public-repository boundary

The current repository is public. Before broad migration, make one explicit choice:

**Option A — keep BASIL public:** only public-safe capability code, instructions, schemas, synthetic examples and visual assets enter GitHub. Drive retains all private evidence and sensitive operational data.

**Option B — make BASIL private during development:** allows a wider migration surface and later selective publication.

Analytical recommendation: use **Option B during migration** unless public development is itself an objective. The risk is not the capability architecture; it is accidentally committing private examples, interaction evidence or credentials while recovering source material.

## 9. Definition of done for the migration

The migration is complete when:

- every current material capability has a stable registry ID;
- every capability has an explicit maturity and repository migration state;
- every canonical entry resolves to real source in GitHub;
- current architecture/governance is readable from GitHub alone;
- critical operational skills are present in exact or deliberately reconciled source form;
- public/private boundaries are enforced;
- tests and `basil doctor` verify structural integrity;
- a clean checkout can run the BASIL core and discover current capabilities;
- chats can retrieve a compact canonical context from GitHub;
- Drive copies of migrated capabilities are frozen as evidence/history rather than maintained as parallel current copies;
- external skills/repos have provenance and licence tracking;
- a tagged cutover commit defines the first coherent canonical baseline.

## 10. Immediate next actions

1. Add `repo_status`, canonical path and migration validation to the registry/doctor.
2. Create the reconciled capability migration inventory from current Drive + GitHub evidence.
3. Import the current controller/architecture/decision material into canonical GitHub Markdown.
4. Recover and migrate the exact MANUEL/BRIAN v1.9 meeting-processing sources.
5. Run a repository-wide verification and produce the first migration completeness report.
6. Only then declare the first GitHub canonical cutover baseline.

The first implementation objective is therefore not "move every file". It is **make GitHub capable of proving which BASIL capabilities exist, which source is current and how mature each one actually is**. Once that control plane is trustworthy, bulk capability migration becomes mechanical rather than interpretive.
