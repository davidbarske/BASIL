# Diagram Design integration candidate

Upstream: https://github.com/cathrynlavery/diagram-design  
Licence: MIT  
Current decision: strong candidate for a full-package trial with a BASIL brand profile.

The integrated value includes diagram selection, semantic patterns, 39 editorial diagram types, brand/style profiles, draw.io/Mermaid redraw, HTML/SVG/PNG output and progressive disclosure of type-specific rules.

Why full adoption may beat extraction: the selection logic, type grammars, styling, profiles and import/export paths are designed to work together. Standard static diagrams are self-contained HTML + SVG and do not require a build step or JavaScript.

Trial method:

1. install upstream in an isolated environment/branch
2. create a BASIL style profile from public-safe project assets
3. produce architecture, state, dependency and flow examples from real BASIL material
4. compare against current manual/generated diagrams
5. retain, customise or remove based on output quality and operational friction
