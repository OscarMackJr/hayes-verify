# WS4 — Immutable Assessment Plan

Status: **COMPLETE**. WS4 creates a frozen onboarding plan before request generation. It binds the exact WS1, WS2, and WS3 snapshot hashes, controlled EMS authority hashes, and Hayes registry version/hash.

The plan projects support state, scope-based evidence requirements, target roles, and anticipated human review requirements. Those projections are planning metadata: they do not resolve evidence, generate evaluator requests, execute an evaluator, or assert compliance.

Any changed bound snapshot, EMS authority, or registry hash yields `PLAN_INPUT_CHANGED`; the frozen plan is never rewritten. Repository, service, and organization authority boundaries remain intact and local paths are rejected.

Validation: contract bundle PASS; Ruff PASS; targeted WS1–WS4 tests 47 passed; full pytest 133 passed. Historical Wave 2D freeze remains unchanged.
