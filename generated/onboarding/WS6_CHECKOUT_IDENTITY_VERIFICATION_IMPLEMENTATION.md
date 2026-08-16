# WS6 — Checkout Identity Verification

Status: **COMPLETE**. WS6 verifies an execution-only local mapping against controlled repository identity and a frozen plan. It captures normalized remote, ref, commit and dirty state, then gates repository-backed request readiness without executing any request.

Local paths never establish identity. Failed checkout verification is execution readiness only, never control compliance.

Validation: contract bundle PASS; Ruff PASS; targeted WS1–WS6 tests 58 passed; full pytest 144 passed. Historical freeze unchanged.
