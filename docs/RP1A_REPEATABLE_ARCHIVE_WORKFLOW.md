# RP1A repeatable archive workflow foundation

RP1A creates an evaluator-free durable workflow foundation. It supports `assess`, `status`, and an inspection-only `resume` command surface. `assess` creates a deterministic `ARCHIVE-*` identity from ZIP SHA-256 and a unique `ARCHIVE-ASSESS-*` workflow ID. It stops at `CLASSIFICATION` with `AWAITING_HUMAN_INPUT`; RP1B supplies safe intake plus authority discovery/freeze and classification handling.

Stages are `INTAKE`, `CLASSIFICATION`, `APPLICABILITY`, `PLAN`, `AUTHORITY_PREFLIGHT`, `EXECUTION`, `REVIEW`, and `PACKAGE`. Workflow states are separate: `CREATED`, `RUNNING`, `AWAITING_HUMAN_INPUT`, `BLOCKED`, `FAILED`, `PARTIAL`, and `COMPLETE`. Control findings never mean workflow failure by themselves.

Input manifests and checkpoints are immutable. The state pointer is mutable only as a pointer to an append-only SHA-256 checkpoint chain. Resumption validates the chain and input manifest and never replays a completed stage. No CLI input accepts manual runtime or contract hashes.

RP1A does not evaluate archives, perform classification, compile applicability, create plans, or make final packages.
