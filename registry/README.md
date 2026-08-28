# Capability registry

The executable capability registry currently lives in `src/basil/data/capabilities.json` so it ships with the Python package. Use `python -m basil capabilities` to inspect it.

The registry is a discoverability layer, not a new BASIL subsystem and not proof that every listed capability is deployed. Maturity labels are mandatory precisely to prevent documentation from being mistaken for implementation.
