---
name: basil-lab-code-review
description: Review a change against two independent axes: repository/code standards and fidelity to the originating requirement/specification.
status: candidate
owner: LABS
upstream: https://github.com/mattpocock/skills
licence: MIT
---

# Code Review — BASIL lab adaptation

Fix the comparison point first: commit, branch base or explicit diff.

Review the same change through two independent lenses:

1. **Standards** — correctness, maintainability, security, repository conventions, obvious smells and unnecessary complexity.
2. **Specification** — does the change actually implement the originating requirement, including edge conditions and exclusions?

Keep the two lenses separate long enough that a clean-looking implementation cannot distract from a missed requirement and a spec-complete implementation cannot excuse dangerous code.

Report findings by consequence and evidence. Avoid style commentary that has no material effect. End by stating what was inspected, what was not inspected and whether the evidence supports merge/readiness.
