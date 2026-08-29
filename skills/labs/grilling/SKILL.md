---
name: grilling
description: >-
  Relentlessly clarify and stress-test a plan, decision, design or idea by mapping dependent decisions and asking only the current decision frontier. Use when the user says "grill me", "GrillMe", "grill this", "stress-test this", asks for rigorous interrogation before execution, or when a material plan carries unresolved assumptions or dependencies that should be surfaced before committing.
license: MIT
metadata:
  basil-status: "adopted"
  basil-owner: "BASIL"
  upstream: "https://github.com/mattpocock/skills"
  lineage: "Adapted from Matt Pocock's grilling skill"
---

# Grill Me / Grilling

Use a dependency-aware interview to remove silent assumptions before action. Build a **decision tree**, not a questionnaire dump.

## BASIL adoption status

**ADOPTED / TESTED — 29 August 2026.** David explicitly adopted GrillMe after positive live use. It should be available as a normal BASIL working method rather than treated as a lab curiosity.

Use it proactively, but selectively, when a material plan, decision, design or commitment contains hidden assumptions, unresolved choices, dependency ambiguity or a meaningful risk of premature execution. Do not turn routine, settled or low-stakes work into an interrogation ritual.

## Activation

Activate immediately when the user explicitly says **GrillMe**, **grill me**, **grill this** or asks to be rigorously interrogated or stress-tested about a plan, decision, design or idea.

It may also be used proactively when the cost of acting on hidden assumptions is material and clarification would materially improve the decision or execution path.

## Workflow

1. Identify the material decisions that determine the outcome.
2. Represent prerequisite relationships between those decisions as a design tree.
3. Define the **frontier** as every unresolved decision whose prerequisites are already settled.
4. Ask the whole current frontier in one numbered round.
5. For each question, give a concise recommended answer when there is a defensible view. Distinguish recommendation from fact.
6. Retrieve facts yourself using available tools and sources. Do not ask the user for facts you can reasonably obtain.
7. If a fact-finding dependency is unresolved, leave only downstream questions waiting and continue with the rest of the frontier.
8. After the user's answers, recompute the tree and advance the frontier.
9. Repeat until no material branch remains silently assumed.
10. Summarise the resulting shared understanding and ask the user to confirm it before executing the plan.

## Round format

Use compact numbered questions. Each question should contain one decision or tightly coupled decision cluster.

**Q1 — [decision title]**  
[Question, context and options where useful.]

**Recommended:** [your recommendation and the reason for it]

Then continue with Q2, Q3 and so on for the rest of the current frontier.

## Rules

- Ask decisions in dependency order. Never ask a downstream question whose answer depends on an unresolved upstream decision.
- Ask the whole current frontier in one round rather than serialising independent questions one at a time.
- The user's decisions control. Recommendations are advisory, not substitutes for the user's choice.
- Facts are the assistant's retrieval problem wherever tools or available sources can resolve them.
- Do not invent certainty. Mark genuine unknowns and dependencies explicitly.
- Do not interrogate for its own sake. Stop when every material branch is settled or consciously left open.
- Do not execute the resulting plan until shared understanding is confirmed, unless the user explicitly instructs immediate execution despite unresolved choices.

## Completion condition

The grilling session is complete when the frontier is empty: every material decision branch has been visited, unresolved items are explicitly labelled and no important assumption is being carried forward silently.

## Source lineage

Adapted for BASIL from Matt Pocock's MIT-licensed `grilling` skill in `mattpocock/skills`. The BASIL adaptation preserves the design-tree/frontier mechanism while making the skill portable across strategic, operational, commercial and technical contexts.
