---
name: basil-lab-grilling
description: Relentlessly clarify a plan, decision or design by mapping dependent decisions and asking only the currently answerable decision frontier.
status: candidate
owner: LABS
upstream: https://github.com/mattpocock/skills
licence: MIT
---

# Grilling — BASIL lab adaptation

Build a **decision tree**, not a questionnaire dump.

1. Identify the decisions that determine the outcome.
2. Represent prerequisite relationships between them.
3. The **frontier** is every unresolved decision whose prerequisites are already settled.
4. Ask the whole current frontier in one numbered round. Give a recommended answer for each question where BASIL has a real view.
5. Retrieve facts BASIL can obtain itself. Do not ask the operator to supply facts BASIL can reasonably recover.
6. After the answers, recompute the tree and advance the frontier.
7. Stop only when no material branch remains silently assumed.
8. Do not execute the resulting plan until shared understanding is confirmed.

The point is not maximal interrogation. It is to prevent downstream questions being asked before the upstream decisions they depend upon are settled.
