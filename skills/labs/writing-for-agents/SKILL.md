---
name: basil-lab-writing-for-agents
description: Design agent-facing instructions and skills with strong triggers, progressive disclosure, single sources of truth and checkable completion criteria.
status: candidate
owner: LABS
upstream: https://github.com/mattpocock/skills
licence: MIT
---

# Writing for Agents — BASIL lab adaptation

Use this when creating or revising skills, `AGENTS.md`, agent instructions or documents consumed primarily by an agent.

- Put the immediate action path first and branch-specific reference behind clear pointers.
- A pointer must say what material is and when it should be loaded.
- Spend always-loaded context only on behaviour required across most runs.
- Keep each rule in one authoritative location. Repetition of meaning creates drift.
- End each operational step with an observable completion criterion.
- Prefer concise leading concepts with useful existing meaning over long repeated definitions.
- Delete instructions that do not change agent behaviour.
- State positive target behaviour where possible rather than filling context with the failure pattern.
- Separate steps from reference material so the agent can see the process it must execute.

The quality test is behavioural: does the document reliably change what the agent does, with less variance and less unnecessary context?
