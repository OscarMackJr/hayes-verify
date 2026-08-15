# Wave 2D organization-level batch targets

The immutable batch runtime supports two execution target types: `REPOSITORY` and `ORGANIZATION`. Organization identity is an execution identity only; evidence authority is supplied independently by an execution-local evidence provider.

`AUTHORITATIVE_EVALUATION` results can establish compliance. `PROJECTION` results preserve observations and traceability but are neutralized if they would otherwise report `PASS`.

File-backed providers accept JSON-object evidence, retain provider provenance, and return unavailable evidence context for missing or invalid files. Local provider references are ignored by Git and are not controlled repository authority.