# Capability registry

The executable capability registry lives in `src/basil/data/capabilities.json` so it ships with the Python package. Use `python -m basil capabilities` to inspect it.

The registry is a discoverability layer, not a BASIL subsystem and not proof that every listed capability is deployed.

Two state axes are deliberately separate:

- `maturity` describes the capability itself: architectural, documented, designed, built, tested, operational, candidate, planned, historical or recovery-pending.
- `repo_status` describes whether this GitHub repository actually contains the authoritative representation: `placeholder`, `migrating`, `canonical` or `retired`.

A capability can therefore be operational in BASIL history while still being a GitHub `placeholder` if its exact current source has not yet been recovered. Conversely, an experimental skill can be repository-`canonical` while its maturity remains only `candidate`.

Useful filters:

```bash
python -m basil capabilities --repo-status placeholder
python -m basil capabilities --owner MANUEL
python -m basil capabilities --maturity tested --json
```
