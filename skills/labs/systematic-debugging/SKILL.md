---
name: basil-lab-systematic-debugging
description: Diagnose technical or operational failures by finding root cause before proposing fixes, testing one explicit hypothesis at a time and verifying the final correction.
status: candidate
owner: LABS
upstream: https://github.com/obra/superpowers
licence: MIT
---

# Systematic Debugging — BASIL lab adaptation

## Phase 1 — Root cause evidence

Reproduce the failure where possible. Read the complete error/state. Inspect recent changes. Instrument boundaries in multi-component systems. Trace bad state backwards until the earliest supported cause is found.

## Phase 2 — Pattern comparison

Find a working analogue. Compare working and failing states line by line or boundary by boundary. List differences without prematurely deciding which ones matter.

## Phase 3 — Hypothesis

State one falsifiable hypothesis: `X is the root cause because Y evidence predicts Z`. Test the smallest change or observation that discriminates it. Change one variable at a time.

## Phase 4 — Correction

Fix the root cause rather than the visible symptom. Add a regression test or reproducible verification where practical. Apply Evidence Before Claims before reporting the issue resolved.

If repeated plausible fixes merely move the failure elsewhere, question the architecture rather than stacking patch number four on patch number three.
