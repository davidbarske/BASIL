# Taste Skill integration candidate

Upstream: https://github.com/Leonxlnx/taste-skill  
Licence: MIT  
Current decision: candidate for full-package trial, selected-skill installation or adaptation.

Why it matters: it provides an integrated family of design skills rather than a single style prompt. Current upstream material includes general frontend taste, redesign, GPT/Codex-oriented taste, image-to-code, visual variants, output enforcement and image-generation skills.

Caveats:

- the current default frontend skill is v2 experimental
- it is opinionated about frontend stack and visual defaults
- the main skill targets landing pages, portfolios and redesigns rather than dashboards/data tables/multi-step product UI
- full adoption should therefore be trialled in a bounded branch/workspace first

Reversibility is high while BASIL has not reshaped core runtime/data structures around it.
